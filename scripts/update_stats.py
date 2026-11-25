"""Atualiza o cartão com totais agregados do dono do perfil autenticado no gh."""

import argparse
from datetime import datetime, timezone
from html import escape
import json
from pathlib import Path
import subprocess
import sys


QUERY = """
query ProfileStats($cursor: String) {
  viewer {
    login
    pullRequests { totalCount }
    mergedPullRequests: pullRequests(states: MERGED) { totalCount }
    issues { totalCount }
    contributionsCollection { totalCommitContributions }
    repositoriesContributedTo(includeUserRepositories: true, privacy: PUBLIC,
      contributionTypes: [COMMIT, ISSUE, PULL_REQUEST, REPOSITORY]) { totalCount }
    repositories(first: 100, after: $cursor, privacy: PUBLIC, isFork: false,
      ownerAffiliations: [OWNER]) {
      nodes { stargazerCount }
      pageInfo { hasNextPage endCursor }
    }
  }
}
"""


def github_stats_page(cursor):
    payload = json.dumps({'query': QUERY, 'variables': {'cursor': cursor}})
    result = subprocess.run(
        ['gh', 'api', 'graphql', '--input', '-'], input=payload,
        capture_output=True, text=True, timeout=90,
    )
    if result.returncode:
        raise RuntimeError('Falha na consulta ao GitHub; confira a autenticação e o acesso privado.')
    response = json.loads(result.stdout)
    if response.get('errors'):
        raise RuntimeError('O GitHub retornou dados incompletos; o cartão anterior foi preservado.')
    return response['data']['viewer']


def count(value):
    if type(value) is not int or value < 0:
        raise ValueError('O GitHub retornou uma contagem inválida.')
    return value


def collect_stats(username, api=github_stats_page):
    cursor = None
    seen = set()
    stars = 0
    stats = None
    while True:
        viewer = api(cursor)
        if viewer['login'].casefold() != username.casefold():
            raise RuntimeError('Use uma credencial pessoal do dono do perfil; GITHUB_TOKEN não serve para consultar os outros repositórios privados.')
        if stats is None:
            stats = {
                'total_prs': count(viewer['pullRequests']['totalCount']),
                'merged_prs': count(viewer['mergedPullRequests']['totalCount']),
                'total_issues': count(viewer['issues']['totalCount']),
                'commits_last_year': count(viewer['contributionsCollection']['totalCommitContributions']),
                'public_repositories_contributed_to': count(viewer['repositoriesContributedTo']['totalCount']),
            }
        repositories = viewer['repositories']
        stars += sum(count(repo['stargazerCount']) for repo in repositories['nodes'])
        page = repositories['pageInfo']
        if not page['hasNextPage']:
            break
        cursor = page['endCursor']
        if not cursor or cursor in seen:
            raise RuntimeError('A paginação do GitHub falhou; o cartão anterior foi preservado.')
        seen.add(cursor)
    stats['public_stars'] = stars
    if stats['merged_prs'] > stats['total_prs']:
        raise ValueError('O total de PRs incorporados excede o total de PRs.')
    return stats


def render_svg(stats, updated_at):
    rows = [
        ('Total Stars (públicas)', 'public_stars'),
        ('Commits (últimos 12 meses)', 'commits_last_year'),
        ('Total PRs', 'total_prs'),
        ('PRs incorporados', 'merged_prs'),
        ('Total Issues', 'total_issues'),
        ('Repositórios públicos com contribuições', 'public_repositories_contributed_to'),
    ]
    lines = []
    for index, (label, key) in enumerate(rows):
        y = 61 + index * 24
        lines.append(f'<text x="24" y="{y}">{escape(label)}</text>')
        lines.append(f'<text x="466" y="{y}" text-anchor="end" font-weight="600">{count(stats[key])}</text>')
    stamp = escape(updated_at.strftime('%d/%m/%Y %H:%M UTC'))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="495" height="234" viewBox="0 0 495 234" role="img" aria-labelledby="title desc">
  <title id="title">Estatísticas do GitHub</title>
  <desc id="desc">Totais agregados dos dados acessíveis à credencial do perfil. PRs e issues incluem repositórios privados acessíveis. Commits cobrem os últimos 12 meses.</desc>
  <rect x="0.5" y="0.5" width="494" height="233" rx="6" fill="#0d1117" stroke="#30363d"/>
  <g font-family="Segoe UI, Ubuntu, Helvetica Neue, sans-serif" font-size="13" fill="#c9d1d9">
    <text x="24" y="30" fill="#58a6ff" font-size="18" font-weight="600">Estatísticas do GitHub</text>
    {''.join(lines)}
    <text x="24" y="219" fill="#8b949e" font-size="10">Atualizado em {stamp}</text>
  </g>
</svg>
'''


def update(username, output, api=github_stats_page):
    stats = collect_stats(username, api)
    svg = render_svg(stats, datetime.now(timezone.utc))
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix('.svg.tmp')
    temporary.write_text(svg, encoding='utf-8')
    temporary.replace(output)
    return stats


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--username', default='joaoqueirozst')
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[1] / 'profile/stats.svg')
    args = parser.parse_args()
    try:
        stats = update(args.username, args.output)
    except (RuntimeError, ValueError, KeyError, TypeError, OSError, subprocess.TimeoutExpired) as error:
        # Não reproduz respostas da API ou valores de credenciais nos logs.
        print(f'Não foi possível atualizar o cartão ({type(error).__name__}). Confira a credencial e suas permissões. O cartão anterior foi preservado.', file=sys.stderr)
        return 1
    print(f"Estatísticas atualizadas: {stats['total_prs']} PR(s), {stats['merged_prs']} incorporado(s).")
    return 0


if __name__ == '__main__':
    sys.exit(main())

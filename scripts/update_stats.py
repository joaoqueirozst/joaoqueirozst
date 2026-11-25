"""Atualiza o cartão com totais agregados do dono do perfil autenticado no gh."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys


QUERY = """
query ProfileStats($cursor: String) {
  viewer {
    login
    pullRequests { totalCount }
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
    return stats


def render_svg(stats):
    # O SVG original é o modelo: somente os cinco valores numéricos mudam.
    template = Path(__file__).resolve().parent / 'templates/stats-github-dark.svg'
    svg = template.read_text(encoding='utf-8')
    for key in ('public_stars', 'commits_last_year', 'total_prs', 'total_issues',
                'public_repositories_contributed_to'):
        placeholder = '{{' + key + '}}'
        if svg.count(placeholder) != 1:
            raise ValueError('Modelo do cartão inválido; o cartão anterior foi preservado.')
        svg = svg.replace(placeholder, str(count(stats[key])))
    return svg


def version_image(markdown, svg):
    # Uma URL por conteúdo evita reutilizar no navegador o cartão anterior.
    version = hashlib.sha256(svg.encode('utf-8')).hexdigest()[:12]
    updated, matches = re.subn(
        r'(?<=src=")\./profile/stats\.svg(?:\?[^\"]*)?(?=")',
        './profile/stats.svg?v=' + version, markdown,
    )
    if matches != 1:
        raise ValueError('Referência ao cartão não encontrada de forma única no README.')
    return updated


def update(username, output, api=github_stats_page, readme=None):
    stats = collect_stats(username, api)
    svg = render_svg(stats)
    markdown = None if readme is None else version_image(readme.read_text(encoding='utf-8'), svg)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix('.svg.tmp')
    temporary.write_text(svg, encoding='utf-8')
    temporary.replace(output)
    if readme is not None:
        readme.write_text(markdown, encoding='utf-8')
    return stats


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--username', default='joaoqueirozst')
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[1] / 'profile/stats.svg')
    parser.add_argument('--readme', type=Path, default=Path(__file__).resolve().parents[1] / 'README.md')
    args = parser.parse_args()
    try:
        stats = update(args.username, args.output, readme=args.readme)
    except (RuntimeError, ValueError, KeyError, TypeError, OSError, subprocess.TimeoutExpired) as error:
        # Não reproduz respostas da API ou valores de credenciais nos logs.
        print(f'Não foi possível atualizar o cartão ({type(error).__name__}). Confira a credencial e suas permissões. O cartão anterior foi preservado.', file=sys.stderr)
        return 1
    print(f"Estatísticas atualizadas: {stats['total_prs']} PR(s).")
    return 0


if __name__ == '__main__':
    sys.exit(main())

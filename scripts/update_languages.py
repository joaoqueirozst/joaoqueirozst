"""Gera o grafico com todas as linguagens dos repositorios do perfil.

Execute localmente com o GitHub CLI autenticado como o dono do perfil.
Somente nomes de linguagens e totais de bytes sao gravados no repositorio.
"""

import argparse
from collections import Counter
import hashlib
from html import escape
import json
from pathlib import Path
import shutil
import subprocess


COLORS = {
    'Python': '#3572A5', 'HTML': '#e34c26', 'C++': '#f34b7d',
    'C': '#555555', 'JavaScript': '#f1e05a', 'TypeScript': '#3178c6',
    'CSS': '#563d7c', 'Shell': '#89e051', 'Dockerfile': '#384d54',
    'Makefile': '#427819', 'CMake': '#DA3434', 'Jupyter Notebook': '#DA5B0B',
    'MATLAB': '#e16737', 'Fortran': '#4d41b1', 'TeX': '#3D6117',
}


def github_json(endpoint, paginate=False):
    gh = shutil.which('gh') or str(Path.home() / '.local/bin/gh')
    command = [gh, 'api', endpoint]
    if paginate:
        command.extend(['--paginate', '--slurp'])
    completed = subprocess.run(command, text=True, capture_output=True)
    if completed.returncode:
        raise RuntimeError('Nao foi possivel consultar o GitHub. Confira a autenticacao do gh.')
    return json.loads(completed.stdout)


def collect_languages(username, api=github_json):
    if api('user')['login'].casefold() != username.casefold():
        raise RuntimeError('Autentique o gh como o dono do perfil antes de gerar os dados.')
    pages = api('user/repos?affiliation=owner&visibility=all&per_page=100', paginate=True)
    totals = Counter()
    for page in pages:
        for repo in page:
            if repo['owner']['login'].casefold() != username.casefold():
                continue
            values = api('repos/{}/languages'.format(repo['full_name']))
            for language, size in values.items():
                if type(size) is not int or size < 0:
                    raise ValueError('O GitHub retornou uma contagem de linguagem invalida.')
                if size:
                    totals[language] += size
    if not totals:
        raise RuntimeError('Nenhuma linguagem encontrada; o grafico anterior foi preservado.')
    return dict(sorted(totals.items(), key=lambda item: (-item[1], item[0].casefold())))


def color_for(language):
    hue = int(hashlib.sha256(language.encode()).hexdigest()[:4], 16) % 360
    return COLORS.get(language, 'hsl({}, 65%, 58%)'.format(hue))


def percentage(size, total):
    value = size / total * 100
    return '<0,01%' if value < 0.01 else '{:.2f}%'.format(value).replace('.', ',')


def render_svg(languages):
    total = sum(languages.values())
    width, height = 495, 115 + 27 * len(languages)
    description = '; '.join('{}: {}'.format(name, percentage(size, total))
                            for name, size in languages.items())
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="{}" height="{}" viewBox="0 0 {} {}" '
        'role="img" aria-labelledby="title desc">'.format(width, height, width, height),
        '<title id="title">Todas as linguagens</title>',
        '<desc id="desc">{}</desc>'.format(escape(description)),
        '<rect x="0.5" y="0.5" width="494" height="{}" rx="8" fill="#0d1117" '
        'stroke="#30363d"/>'.format(height - 1),
        '<g font-family="Segoe UI, Ubuntu, sans-serif">',
        '<text x="24" y="32" fill="#58a6ff" font-size="18" font-weight="600">Todas as linguagens</text>',
        '<text x="24" y="54" fill="#8b949e" font-size="12">Repositórios públicos e privados · volume de código</text>',
        '<defs><clipPath id="bar"><rect x="24" y="72" width="447" height="9" rx="4.5"/></clipPath></defs>',
        '<g clip-path="url(#bar)">',
    ]
    offset = 24.0
    for name, size in languages.items():
        segment_width = size / total * 447
        parts.append('<rect x="{:.6f}" y="72" width="{:.6f}" height="9" fill="{}"/>'.format(
            offset, segment_width, color_for(name)))
        offset += segment_width
    parts.append('</g>')
    for index, (name, size) in enumerate(languages.items()):
        y = 112 + index * 27
        parts.extend([
            '<circle cx="29" cy="{}" r="5" fill="{}"/>'.format(y - 4, color_for(name)),
            '<text x="43" y="{}" fill="#c9d1d9" font-size="13">{}</text>'.format(y, escape(name)),
            '<text x="471" y="{}" fill="#c9d1d9" font-size="13" text-anchor="end">{}</text>'.format(
                y, escape(percentage(size, total))),
        ])
    parts.extend(['</g>', '</svg>'])
    return '\n'.join(parts) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--username', default='joaoqueirozst')
    args = parser.parse_args()
    languages = collect_languages(args.username)
    output = Path(__file__).resolve().parents[1] / 'profile'
    output.mkdir(exist_ok=True)
    data = {'scope': 'owned_repositories_public_and_private_including_forks',
            'language_bytes': languages}
    (output / 'languages.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    (output / 'languages.svg').write_text(render_svg(languages))
    print('Grafico atualizado: {} linguagens.'.format(len(languages)))
    print(', '.join(languages))


if __name__ == '__main__':
    main()

"""Gera o grafico com todas as linguagens dos repositorios do perfil.

Execute localmente com o GitHub CLI autenticado como o dono do perfil.
Somente nomes de linguagens e totais de bytes sao gravados no repositorio.
"""

import argparse
from collections import Counter
import hashlib
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
    from update_donut import main as update_donut
    update_donut()
    print('Grafico atualizado: {} linguagens.'.format(len(languages)))
    print(', '.join(languages))


if __name__ == '__main__':
    main()

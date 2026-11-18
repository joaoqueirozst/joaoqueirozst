"""Atualiza somente o gráfico circular da imagem 3D com os totais agregados."""

import json
import math
from html import escape
from pathlib import Path
import re

from update_languages import color_for, percentage


def render_donut(languages):
    total = sum(languages.values())
    if not languages or total <= 0 or any(size <= 0 for size in languages.values()):
        raise ValueError('Os totais de linguagens devem ser positivos.')
    parts = ['<g transform="translate(40, 520)">',
             '<title>Linguagens por volume de código em repositórios públicos e privados</title>',
             '<g transform="translate(130, 130)">']
    angle = -math.pi / 2
    for name, size in languages.items():
        end = angle + size / total * math.tau
        color = color_for(name)
        label = escape('{}: {}'.format(name, percentage(size, total)))
        if len(languages) == 1:
            parts.append('<circle r="91" fill="none" stroke="{}" stroke-width="52"><title>{}</title></circle>'.format(color, label))
        else:
            def point(radius, theta):
                return '{:.6f},{:.6f}'.format(radius * math.cos(theta), radius * math.sin(theta))
            large = int(end - angle > math.pi)
            path = 'M{}A117,117,0,{},1,{}L{}A65,65,0,{},0,{}Z'.format(
                point(117, angle), large, point(117, end), point(65, end), large, point(65, angle))
            parts.append('<path d="{}" fill="{}"><title>{}</title></path>'.format(path, color, label))
        angle = end
    parts.append('</g><g transform="translate(273, 0)">')
    spacing = min(32.5, 240 / len(languages))
    font = min(21.666667, spacing * .7)
    for index, (name, size) in enumerate(languages.items()):
        y = 130 + (index - (len(languages) - 1) / 2) * spacing
        parts.append('<rect x="0" y="{:.6f}" width="{:.6f}" height="{:.6f}" fill="{}"/>'.format(y - font / 2, font, font, color_for(name)))
        parts.append('<text dominant-baseline="middle" x="{:.6f}" y="{:.6f}" class="fill-fg" font-size="{:.6f}px">{}</text>'.format(font + 5, y, font, escape(name)))
    parts.append('</g></g>')
    return ''.join(parts)


def update_donut(svg, languages):
    marker = '<g transform="translate(40, 520)">'
    start = svg.index(marker)
    depth = 0
    for match in re.finditer(r'<g\b[^>]*>|</g>', svg[start:]):
        depth += -1 if match.group() == '</g>' else 1
        if depth == 0:
            end = start + match.end()
            return svg[:start] + render_donut(languages) + svg[end:]
    raise ValueError('Grupo do gráfico circular incompleto.')


def main():
    root = Path(__file__).resolve().parents[1]
    languages = json.loads((root / 'profile/languages.json').read_text())['language_bytes']
    image = root / 'profile-3d-contrib/profile-night-white.svg'
    image.write_text(update_donut(image.read_text(), languages))


if __name__ == '__main__':
    main()

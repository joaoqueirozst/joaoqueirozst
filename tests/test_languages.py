import unittest
from xml.etree import ElementTree

from scripts.update_languages import collect_languages
from scripts.update_donut import render_donut, update_donut


class LanguageChartTests(unittest.TestCase):
    def test_collects_every_language_from_all_pages_and_private_repositories(self):
        responses = {
            'user': {'login': 'owner'},
            'user/repos?affiliation=owner&visibility=all&per_page=100': [
                [{'full_name': 'owner/public', 'owner': {'login': 'owner'}, 'private': False}],
                [{'full_name': 'owner/private', 'owner': {'login': 'owner'}, 'private': True}],
            ],
            'repos/owner/public/languages': {'Python': 1000, 'C++': 1},
            'repos/owner/private/languages': {'Python': 2000, 'Shell': 1, 'HTML': 10},
        }
        data = collect_languages('owner', lambda endpoint, **kwargs: responses[endpoint])
        self.assertEqual(data, {'Python': 3000, 'HTML': 10, 'C++': 1, 'Shell': 1})
        self.assertNotIn('owner/private', repr(data))

    def test_chart_has_no_language_limit_or_other_bucket(self):
        data = {'Language {}'.format(index): index + 1 for index in range(40)}
        svg = render_donut(data)
        root = ElementTree.fromstring(svg)
        texts = [node.text for node in root.findall('.//text')]
        for language in data:
            self.assertIn(language, texts)
        self.assertNotIn('Other', texts)
        self.assertEqual(len(root.findall('.//path')), len(data))

    def test_xml_escaping_and_tiny_languages_remain_visible(self):
        root = ElementTree.fromstring(render_donut({'Python': 1000000, 'A&B <C>': 1}))
        texts = [node.text for node in root.findall('.//text')]
        self.assertIn('A&B <C>', texts)
        titles = [node.text for node in root.findall('.//path/title')]
        self.assertIn('A&B <C>: <0,01%', titles)


    def test_replaces_only_donut_and_preserves_surrounding_svg(self):
        prefix = '<svg><g id="contributions"><path d="M0,0"/></g>'
        suffix = '<g id="radar"/><text>Statistics</text></svg>'
        original = prefix + '<g transform="translate(40, 520)"><g><text>other</text></g></g>' + suffix
        data = {'Python': 100, 'C++': 1}
        result = update_donut(original, data)
        self.assertEqual(result, prefix + render_donut(data) + suffix)
        self.assertEqual(update_donut(result, data), result)
        ElementTree.fromstring(result)

    def test_single_language_uses_complete_ring(self):
        root = ElementTree.fromstring(render_donut({'Python': 100}))
        self.assertEqual(len(root.findall('.//circle')), 1)
        self.assertEqual(root.find('.//circle/title').text, 'Python: 100,00%')


if __name__ == '__main__':
    unittest.main()

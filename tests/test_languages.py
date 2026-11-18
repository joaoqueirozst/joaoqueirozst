import unittest
from xml.etree import ElementTree

from scripts.update_languages import collect_languages, render_svg


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
        svg = render_svg(data)
        root = ElementTree.fromstring(svg)
        texts = [node.text for node in root.findall('.//{http://www.w3.org/2000/svg}text')]
        for language in data:
            self.assertIn(language, texts)
        self.assertNotIn('Other', texts)
        self.assertGreater(int(root.attrib['height']), 1000)

    def test_xml_escaping_and_tiny_languages_remain_visible(self):
        root = ElementTree.fromstring(render_svg({'Python': 1000000, 'A&B <C>': 1}))
        texts = [node.text for node in root.findall('.//{http://www.w3.org/2000/svg}text')]
        self.assertIn('A&B <C>', texts)
        self.assertIn('<0,01%', texts)


if __name__ == '__main__':
    unittest.main()

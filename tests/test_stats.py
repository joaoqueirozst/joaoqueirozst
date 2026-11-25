import importlib.util
from pathlib import Path
import re
import tempfile
import unittest
from xml.etree import ElementTree


spec = importlib.util.spec_from_file_location('update_stats', Path(__file__).resolve().parents[1] / 'scripts/update_stats.py')
stats = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stats)


def page(stars=(2,), more=False, cursor=None):
    return {
        'login': 'joaoqueirozst',
        'pullRequests': {'totalCount': 3},
        'issues': {'totalCount': 2},
        'contributionsCollection': {'totalCommitContributions': 150},
        'repositoriesContributedTo': {'totalCount': 10},
        'repositories': {
            'nodes': [{'stargazerCount': n} for n in stars],
            'pageInfo': {'hasNextPage': more, 'endCursor': cursor},
        },
    }


class StatsTests(unittest.TestCase):
    def test_stars_paginate_but_profile_counts_are_not_added_twice(self):
        calls = []

        def api(cursor):
            calls.append(cursor)
            return page((2, 4), True, 'next') if cursor is None else page((3,))

        result = stats.collect_stats('joaoqueirozst', api)
        self.assertEqual(calls, [None, 'next'])
        self.assertEqual(result['public_stars'], 9)
        self.assertEqual(result['total_prs'], 3)

    def test_different_account_or_automatic_bot_is_rejected(self):
        response = page()
        response['login'] = 'github-actions[bot]'
        with self.assertRaises(RuntimeError):
            stats.collect_stats('joaoqueirozst', lambda _: response)

    def test_invalid_count_does_not_replace_previous_card(self):
        response = page()
        response['pullRequests']['totalCount'] = -1
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'stats.svg'
            target.write_text('previous card')
            with self.assertRaises(ValueError):
                stats.update('joaoqueirozst', target, lambda _: response)
            self.assertEqual(target.read_text(), 'previous card')

    def test_failure_on_second_page_does_not_replace_previous_card(self):
        def api(cursor):
            if cursor:
                raise RuntimeError('API unavailable')
            return page(more=True, cursor='next')

        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'stats.svg'
            target.write_text('previous card')
            with self.assertRaises(RuntimeError):
                stats.update('joaoqueirozst', target, api)
            self.assertEqual(target.read_text(), 'previous card')

    def test_invalid_pagination_is_rejected(self):
        with self.assertRaises(RuntimeError):
            stats.collect_stats('joaoqueirozst', lambda _: page(more=True, cursor='same'))

    def test_svg_contains_totals_and_no_unrelated_private_fields(self):
        response = page()
        response['private_repository_name'] = 'secret-project'
        response['token'] = 'secret-credential'
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'stats.svg'
            stats.update('joaoqueirozst', target, lambda _: response)
            svg = target.read_text()
            ElementTree.fromstring(svg)
            self.assertIn('Total PRs', svg)
            self.assertIn('Stats', svg)
            self.assertNotIn('PRs incorporados', svg)
            self.assertNotIn('Atualizado em', svg)
            self.assertNotIn('secret-project', svg)
            self.assertNotIn('secret-credential', svg)

    def test_only_the_five_numbers_change_in_the_original_layout(self):
        values = stats.collect_stats('joaoqueirozst', lambda _: page())
        svg = stats.render_svg(values)
        template = (Path(stats.__file__).parent / 'templates/stats-github-dark.svg').read_text()
        replaced, n = re.subn(r'(<text\b[^>]*\bx="130"[^>]*>)(\d+)(</text>)', r'\1VALUE\3', svg)
        expected, placeholders = re.subn(r'\{\{[a-z_]+\}\}', 'VALUE', template)
        self.assertEqual(n, 5)
        self.assertEqual(placeholders, 5)
        self.assertEqual(replaced, expected)
        root = ElementTree.fromstring(svg)
        self.assertEqual(root.attrib, {'width': '340', 'height': '200', 'viewBox': '0 0 340 200'})
        texts = [item.text for item in root.iter() if item.tag.endswith('}text')]
        self.assertEqual(texts[:6], ['Stats', 'Total Stars:', 'Total Commits:', 'Total PRs:', 'Total Issues:', 'Contributed to:'])
        self.assertEqual(texts[6:], ['2', '150', '3', '2', '10'])


if __name__ == '__main__':
    unittest.main()

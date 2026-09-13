import unittest
from plainvoice_text_cleaning import clean_text


class CleanerTests(unittest.TestCase):
    def check(self, source, expected=None, **kw):
        a = clean_text(source, **kw)
        self.assertEqual(clean_text(a['text'], **kw)['text'], a['text'])
        if expected is not None:
            self.assertEqual(a['text'], expected)
        return a

    def test_owid_style_header(self):
        raw = '''---
title: An influenza history A description.
date: 2020-03-04
authors: Example Author
url: https://example.org/history
-------------------------------------------------------------------

*Home > Influenza*

# An influenza history

By:Example Author | March 4, 2020

\\---

The event affected many countries.
'''
        r = self.check(raw, 'The event affected many countries.')
        self.assertEqual(r['actions']['frontmatter'], 1)
        self.assertEqual(r['actions']['breadcrumb'], 1)
        self.assertEqual(r['actions']['byline'], 1)
        self.assertTrue(any(x['reason'] == 'frontmatter' and 'date:' in x['text'] for x in r['removed']))

    def test_unknown_yaml_preserved(self):
        raw = '---\ntitle: Config test\ncustom_meaning: Must retain\n---\n\nText.'
        r = self.check(raw, raw)
        self.assertIn('ambiguous_frontmatter_preserved', r['warnings'])

    def test_unclosed_yaml_preserved(self):
        raw = '---\ntitle: Config test\ndate: 2020-01-01\n\nThe block never closes.'
        self.assertIn('unclosed_frontmatter_preserved', self.check(raw, raw)['warnings'])

    def test_duplicate_title_only(self):
        self.check('# Example title\n\n# Example title\n\nActual prose.', 'Example title\n\nActual prose.', title='Example title')
        self.check('We waited.\n\nWe waited.', 'We waited.\n\nWe waited.')

    def test_article_title_moves_to_metadata(self):
        self.check('# Actual title\n\n## Section\n\nBody.', 'Section\n\nBody.',
                   title='Actual title A subtitle.', source_unit_type='complete article')
        self.check('Actual title\n\nBody.', 'Body.', title='Actual title', source_url='https://example.org/memo.pdf')
        self.check('# Different title\n\nBody.', 'Different title\n\nBody.', title='Original title', source_unit_type='article')
        self.check('## A section\n\nBody.', 'A section\n\nBody.', title='Different title', source_unit_type='article')

    def test_titles_preserved(self):
        self.check('# A title\n\n## A section\n\nWords.', 'A title\n\nA section\n\nWords.')
        self.check('A title\n===\n\nWords.', 'A title\n\nWords.')

    def test_code_fence_exact(self):
        raw = '```python\nx = "<p> &amp; *word*"\n    # Heading?\n    print(x)\n```'
        self.check(raw, raw)
        self.check('~~~sql\nSELECT * FROM t;\n~~~')

    def test_unclosed_code(self):
        raw = '```js\nconst x = "**keep**";'
        self.assertIn('unclosed_code_fence_preserved', self.check(raw, raw)['warnings'])

    def test_inline_code(self):
        self.check('Call `create_user(name, "*literal*")` then **return**.', 'Call `create_user(name, "*literal*")` then return.')
        self.check('Use ``a`b`` and `foo_bar`.', 'Use ``a`b`` and `foo_bar`.')

    def test_math_and_currency(self):
        raw = 'Use $x_i + y_j$ and \\(a*b\\).\n\n$$\nF = a * b\n$$\n\nIt costs $5 and later $10.'
        self.check(raw, raw)
        self.check('The value is \\nu, not \\neq.', 'The value is \\nu, not \\neq.')

    def test_identifiers(self):
        self.check('Pass foo_bar and Class<T> to set_value().', 'Pass foo_bar and Class<T> to set_value().')
        self.check('Place <API_KEY> in Authorization.', 'Place <API_KEY> in Authorization.')

    def test_lists_and_javadoc(self):
        raw = '- First\n  - Nested\n1. Ordered\n2. Again\n@param arg the value\n@return result\n@throws Error on failure'
        self.check(raw, raw)

    def test_links(self):
        self.check('Read [the study](https://example.org/study) first.', 'Read the study first.')
        self.check('Call [create](https://api.example.org/v1/users?x=a_b) now.', 'Call create (https://api.example.org/v1/users?x=a_b) now.')
        self.check('Call [`POST`](/v1/users) next.', 'Call `POST` (/v1/users) next.')
        self.check('Follow [this](/api/items_(new)) exactly.', 'Follow this (/api/items_(new)) exactly.')
        self.check('Fact [1](#note-1).', 'Fact [1].')

    def test_orphan_owid_note_markers(self):
        r = self.check('Researcher (2020) found this. [1](#note-1)', 'Researcher (2020) found this.', source_collection='coggen-owid')
        self.assertIn('source_endnotes_missing', r['warnings'])
        self.assertEqual(r['removed'][0]['text'], '[1](#note-1)')
        self.check('Researcher (2020) found this. [1](#note-1)', 'Researcher (2020) found this. [1]')

    def test_reference_links(self):
        self.check('Read [the study][ref].\n\n[ref]: https://example.org/study', 'Read the study.')
        self.check('Call [API][].\n\n[API]: /api/v2/items', 'Call API (/api/v2/items).')

    def test_images_audited(self):
        r = self.check('Text.\n\n![A chart](image.png)\n\nMore.', 'Text.\n\nMore.')
        self.assertEqual(r['actions']['image'], 1)
        self.assertTrue(any('A chart' in x['text'] for x in r['removed']))

    def test_html(self):
        self.check('<p>One <strong>bold</strong> word.</p><p>Two.</p>', 'One bold word.\n\nTwo.')
        self.check('<script>steal()</script><p>Real text.</p>', 'Real text.')
        self.check('<style>p {color:red}</style><p>Real text.</p>', 'Real text.')
        self.check('<pre><code>x = "&lt;p&gt;"\n    f(x)</code></pre>', '```\nx = "<p>"\n    f(x)\n```')
        self.check('Call <code>foo_bar()</code>.', 'Call `foo_bar()`.')

    def test_scientific_markup(self):
        self.check('Use H<sub>2</sub>O and x<sup>2</sup>.', 'Use H_{2}O and x^{2}.')
        self.check('> 10', '> 10')
        self.check('> Quoted prose.', 'Quoted prose.')

    def test_entities(self):
        self.check('A &amp; B &mdash; C&nbsp;D.', 'A & B — C D.')
        self.check('Write &lt;div&gt; literally.', 'Write `<div>` literally.')
        self.check('A &amp;amp; B.', 'A & B.')
        self.check('Write &amp;lt;div&amp;gt; literally.', 'Write `<div>` literally.')

    def test_unicode_and_spaces(self):
        self.check('Cafe\u0301\u200b   normal\u00a0text.', 'Café normal text.')
        self.check('a\u200cb\u200dc', 'a\u200cb\u200dc')

    def test_table_preserved(self):
        raw = '| Name | Value |\n| --- | --- |\n| foo_bar | **literal** |'
        self.check(raw, raw)

    def test_json_preserved(self):
        raw = '{\n  "text": "Keep   **everything**",\n  "n": 2\n}'
        r = self.check(raw, raw)
        self.assertIn('structured_json_preserved_not_prose', r['warnings'])

    def test_byline_not_in_body(self):
        long = 'This paragraph is genuine prose. ' * 10
        self.check(long + '\n\nBy: a later attribution', long.strip() + '\n\nBy: a later attribution')
        self.check('By studying the data, we found a change.', 'By studying the data, we found a change.')

    def test_dates_and_metadata_subject(self):
        self.check('2020-03-04', '2020-03-04')
        self.check('Copyright protects expression.', 'Copyright protects expression.')
        self.check('[MATH] follows from [CITATION].', '[MATH] follows from [CITATION].')

    def test_pdf_prose_wraps(self):
        raw = ('This is a sufficiently long first line of a source paragraph that\n'
               'continues here with further details and then finally ends.\n\n'
               'A separate paragraph stays separate.')
        expected = raw.replace('that\ncontinues', 'that continues')
        r = self.check(raw, expected, source_url='https://example.org/memo.pdf')
        self.assertEqual(r['actions']['pdf_soft_wrap_joins'], 1)
        self.check(raw, raw)
        technical = '- One fairly long list item that should stay a list line.\n- Another fairly long list item with independent meaning.'
        self.check(technical, technical, source_unit_type='pdf article')
        hyphen = 'This is a fairly long sentence about a complete full-\ncircle change in conditions.'
        self.check(hyphen, hyphen.replace('full-\ncircle', 'full-circle'), source_url='https://example.org/memo.pdf')

    def test_extracted_prose_punctuation_spacing(self):
        self.check('*Period life expectancy* , one *particular year* .', 'Period life expectancy, one particular year.')
        self.check('Read [this study](https://example.org/study) .', 'Read this study.')
        self.check('句子 ，和词语 。', '句子，和词语。')
        self.check('Use `x , y` and $x , y$.', 'Use `x , y` and $x , y$.')
        self.check('Use 1 . 5 and time 10 : 20.', 'Use 1 . 5 and time 10 : 20.')
        self.check('An ellipsis . . . stays.', 'An ellipsis . . . stays.')
        self.check('This is a very long line that reaches the wrap column\n. Next sentence.', 'This is a very long line that reaches the wrap column. Next sentence.', source_url='https://example.org/a.pdf')

    def test_naked_scientific_and_corrupt_source_preserved(self):
        raw = r'The temperature T^*_{\rm cr} follows \langle R _g \rangle, with T^*_{\rm cr}^2.'
        self.assertIn('unmarked_tex_preserved_review_required', self.check(raw, raw)['warnings'])
        masked = 'Let [MATH](N)^* and [MATH]P[MATH] be the input.'
        self.check(masked, masked, source_collection='arxivedits-unaligned')
        self.check('See [REF](source unavailable) and [CITATION].', 'See [REF](source unavailable) and [CITATION].')
        formula = '_el v_rel_0 &_el^2 T_reh^2m_^4, _el_0 _el v_rel_0.'
        self.check(formula, formula, source_collection='arxivedits-unaligned')
        diff = r'%DIFDELCMD < \ge %%% x_1 + x_2'
        self.check(diff, diff)
        wiki = '--~~~~Insert non-formatted text here--~~~~--~~~~ A sentence.'
        self.check(wiki, wiki)
        self.check('**Use** `$x_i$` and `\\nu`.', 'Use `$x_i$` and `\\nu`.')
        self.check('(A + B + C) _________________________ 3', '(A + B + C) _________________________ 3')

    def test_no_punctuation_rewriting(self):
        self.check('A.. B.C; 123.45; 30%; 3–5.', 'A.. B.C; 123.45; 30%; 3–5.')


if __name__ == '__main__':
    unittest.main()

"""Conservative, deterministic plain-prose normalization; stdlib only.

Raw text must be retained separately. The same rules apply to either side of a
pair. This module deliberately does not rewrite grammar, facts or repetition.
Fenced/inline code, math and Markdown tables remain structurally intact: stripping
those delimiters can corrupt technical meaning and breaks repeatability.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import html
import json
import re
import unicodedata

VERSION = 'plainvoice-text-cleaning-v1'
META_KEYS = {'title', 'date', 'authors', 'author', 'url', 'source', 'published',
             'published_at', 'updated', 'updated_at', 'description', 'slug',
             'tags', 'categories', 'layout', 'language', 'lang'}
BLOCK_TAGS = {'p', 'div', 'section', 'article', 'main', 'header', 'footer',
              'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'ul', 'ol',
              'table', 'tr', 'dl', 'dt', 'dd', 'figure', 'figcaption'}
INLINE_TAGS = {'span', 'b', 'strong', 'i', 'em', 'u', 's', 'del', 'small',
               'sup', 'sub', 'mark', 'label', 'abbr', 'cite', 'time', 'font'}
DATE = r'(?:\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{4}年\d{1,2}月\d{1,2}日|(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?\s+\d{1,2},?\s+\d{4}|\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})'
DATE_RE = re.compile(r'^' + DATE + r'$', re.I)
SEP_RE = re.compile(r'^\s*\\?(?:(?:-\s*){3,}|(?:\*\s*){3,}|(?:_\s*){3,})\s*$')


def _punctuation_spacing(value):
    # Web extraction can leave a space between an emphasized/link label and
    # following prose punctuation. Do not touch numeric expressions, newlines,
    # code or math (which have been protected before the slow path calls this).
    return re.sub(r'''(?<=[A-Za-z\u3400-\u9fff\]\)"'”’\ue001]) +([,.;:!?，。；：！？、])(?![ \t]*\.)''', r'\1', value)


def clean_text(text, *, title='', source_url='', source_collection='', source_unit_type=''):

    """Return cleaned text, change counts, exact removed spans, and QA warnings.

    Metadata may be moved out of training text; it must remain in provenance.
    An unchanged output is possible even when warnings flag ambiguous formatting.
    """
    if not isinstance(text, str):
        raise TypeError('text must be a string')
    original = text
    # Some published research corpora contain LaTeX without math delimiters,
    # missing-formula placeholders, diff commands, or ASCII vandalism. They
    # cannot safely be interpreted as Markdown prose. Preserve these fields
    # exactly and surface a review flag instead of deleting mathematical
    # subscripts, treating [MATH](...) as a link, or rewriting an ASCII diagram.
    # Ignore explicitly fenced/inline code and delimited math when identifying
    # *unmarked* TeX so ordinary technical articles still receive prose cleanup.
    probe = text
    if any(marker in text for marker in ('\\', '[MATH]', '[EQUATION]', '[REF]', '[CITATION]', '~~~', '__NOTOC__')):
        probe = re.sub(r'(?ms)^ {0,3}(`{3,}|~{3,})[^\n]*\n.*?^ {0,3}\1\s*$', '', probe)
        probe = re.sub(r'(?<!`)(`+)(?!`)([^\n]*?)(?<!`)\1(?!`)', '', probe)
        probe = re.sub(r'\\\[[\s\S]*?\\\]|\\\([\s\S]*?\\\)|\$\$[\s\S]*?\$\$', '', probe)
        probe = re.sub(r'(?<![\\\w$])\$(?!\s)([^$\n]+?)(?<!\s)\$(?!\$)', '', probe)
    structured_warning = None
    if re.search(r'\[(?:MATH|EQUATION)\]', probe):
        structured_warning = 'source_formula_placeholders_preserved_review_required'
    elif re.search(r'\[(?:REF|CITATION)\]', probe):
        structured_warning = 'source_reference_placeholders_preserved_review_required'
    elif re.search(r'%DIF(?:DEL|ADD|BEGIN|END)', probe):
        structured_warning = 'source_latex_diff_markup_preserved_not_prose'
    elif re.search(r'\\[A-Za-z]{2,}\b', probe):
        structured_warning = 'unmarked_tex_preserved_review_required'
    elif str(source_collection).startswith('arxivedits') and re.search(r'[_^=]', probe):
        structured_warning = 'scientific_notation_preserved_review_required'
    elif probe.count('\\') >= 4 and probe.count('|') >= 3 and probe.count('_') >= 3:
        structured_warning = 'ascii_art_or_corrupted_markup_preserved_not_prose'
    elif re.search(r'__NOTOC__|(?:--)?~{4}|Insert non-formatted text here', probe):
        structured_warning = 'source_wiki_editing_markup_preserved_review_required'
    if structured_warning:
        return {'text': text, 'actions': {}, 'removed': [],
                'warnings': [structured_warning], 'protected': {'structured_source_text': 1}}
    # Trace payloads and standalone JSON are data, not prose. Avoid modifying
    # whitespace inside quoted strings or structured fields.
    stripped = text.strip()
    if stripped.startswith(('{', '[')):
        try:
            parsed = json.loads(stripped)
        except (ValueError, TypeError):
            pass
        else:
            if isinstance(parsed, (dict, list)):
                return {'text': text, 'actions': {}, 'removed': [],
                        'warnings': ['structured_json_preserved_not_prose'],
                        'protected': {'structured_json': 1}}
    # The bulk of released edit datasets consists of ordinary single-line
    # sentences. This fast path has exactly the same prose whitespace rules.
    if not re.search(r'[\r\n<>&*_~`\[\]$\\\u200b\u200c\u200d\u2060\ufeff]', text) and not re.match(
            r'\s*(?:#{1,6} |By\s*:|作者\s*[:：]|文\s*[:：]|Home\s*[>/›»→]|首页\s*[>/›»→]|主页\s*[>/›»→]|\[|!\[)', text, re.I):
        date_candidate = re.sub(r'^(?:Published|Updated|发布日期|发布时间|日期)\s*[:：]?\s*', '', stripped, flags=re.I)
        standalone_article_title = (stripped == str(title).strip() and (
            'article' in str(source_unit_type).casefold() or re.search(r'\.pdf(?:$|[?#])', str(source_url), re.I)
            or source_collection in {'coggen-owid', 'freshwiki', 'rewrite-article-v2', 'ai-enrichment-articles', 'ai-enrichment-comparison'}))
        if not DATE_RE.fullmatch(date_candidate) and not standalone_article_title:
            normalized = unicodedata.normalize('NFC', text)
            result = re.sub(r'[\t \f\v\u00a0\u202f]+', ' ', normalized).strip()
            fast_actions = {}
            if normalized != text:
                fast_actions['unicode_nfc'] = 1
            if result != normalized:
                fast_actions['horizontal_whitespace'] = 1
            spaced = _punctuation_spacing(result)
            if spaced != result:
                fast_actions['prose_punctuation_spacing'] = 1
                result = spaced
            fast_warnings = []
            if re.search(r'\b(?:Click here|Subscribe to|Sign up for|All rights reserved)\b|订阅|版权所有', result, re.I):
                fast_warnings.append('possible_residual_boilerplate_review_required')
            return {'text': result, 'actions': fast_actions, 'removed': [],
                    'warnings': fast_warnings, 'protected': {}}
    actions = Counter()
    protected = Counter()
    removed = []
    warnings = []
    tokens = {}
    prefix = '\ue000PV' + hashlib.sha256(text.encode('utf-8')).hexdigest()[:12] + '_'
    while prefix in text:
        prefix += '_'

    def warn(message):
        if message not in warnings:
            warnings.append(message)

    def removal(reason, value):
        if value:
            removed.append({'reason': reason, 'text': value})
            actions[reason] += 1

    def hold(value, kind):
        token = prefix + str(len(tokens)) + '\ue001'
        tokens[token] = value
        protected[kind] += 1
        return token

    def sub_count(pattern, replacement, value, reason, flags=0):
        def replace(match):
            new = replacement(match) if callable(replacement) else replacement
            if new != match.group():
                actions[reason] += 1
            return new
        return re.sub(pattern, replace, value, flags=flags)

    # Normalize transport line endings, including inside code; preserve all other
    # characters inside code blocks verbatim.
    text = sub_count(r'\r\n?', '\n', text, 'line_endings')

    # Fence scanner supports variable delimiter lengths and unclosed fences.
    lines = text.splitlines(keepends=True)
    out = []
    i = 0
    while i < len(lines):
        match = re.match(r'^ {0,3}(`{3,}|~{3,})[^\n]*\n?$', lines[i])
        if match:
            delim = match.group(1)
            j = i + 1
            while j < len(lines):
                if re.match(r'^ {0,3}' + re.escape(delim[0]) + '{' + str(len(delim)) + r',}\s*$', lines[j]):
                    break
                j += 1
            if j == len(lines):
                warn('unclosed_code_fence_preserved')
                out.append(hold(''.join(lines[i:]).rstrip('\n'), 'fenced_code') + '\n')
                break
            out.append(hold(''.join(lines[i:j + 1]).rstrip('\n'), 'fenced_code') + '\n')
            i = j + 1
        else:
            out.append(lines[i])
            i += 1
    text = ''.join(out)

    # Preformatted HTML is represented by a code fence so a second pass protects
    # precisely the same content. The angle brackets in code are never removed.
    def html_pre(match):
        value = re.sub(r'^\s*<code\b[^>]*>|</code>\s*$', '', match.group(1), flags=re.I)
        value = html.unescape(value).strip('\n')
        delimiter = '`' * max(3, 1 + max([len(x) for x in re.findall(r'`+', value)] or [0]))
        actions['html_pre_to_fence'] += 1
        return '\n' + hold(delimiter + '\n' + value + '\n' + delimiter, 'html_code') + '\n'
    text = re.sub(r'<pre\b[^>]*>([\s\S]*?)</pre\s*>', html_pre, text, flags=re.I)

    def html_code(match):
        value = html.unescape(match.group(1))
        delimiter = '`' * (1 + max([len(x) for x in re.findall(r'`+', value)] or [0]))
        actions['html_code_to_inline'] += 1
        return hold(delimiter + value + delimiter, 'html_code')
    text = re.sub(r'<code\b[^>]*>([\s\S]*?)</code\s*>', html_code, text, flags=re.I)
    text = re.sub(r'(?<!`)(`+)(?!`)([^\n]*?)(?<!`)\1(?!`)',
                  lambda m: hold(m.group(), 'inline_code'), text)

    # Equations retain delimiters and spacing, and currency is not treated as math.
    for pattern in (r'\\\[[\s\S]*?\\\]', r'\\\([\s\S]*?\\\)', r'\$\$[\s\S]*?\$\$'):
        text = re.sub(pattern, lambda m: hold(m.group(), 'math'), text)
    text = re.sub(r'(?<![\\\w$])\$(?!\s|\d[\d,.]*\b)([^$\n]+?)(?<!\s)\$(?!\$)',
                  lambda m: hold(m.group(), 'math'), text)

    # Superscripts/subscripts carry scientific meaning, so express them
    # explicitly instead of silently flattening x<sup>2</sup> into x2.
    def html_index(match):
        operator = '^' if match.group(1).lower() == 'sup' else '_'
        actions['html_math_index'] += 1
        return hold(operator + '{' + html.unescape(match.group(2)) + '}', 'math')
    text = re.sub(r'<(sup|sub)\b[^>]*>([^<>]*?)</\1\s*>', html_index, text, flags=re.I)

    # Literal escaped HTML examples are code, rather than real element markup.
    def escaped_tag(match):
        value = html.unescape(match.group())
        actions['literal_html_entity_to_code'] += 1
        return hold('`' + value + '`', 'literal_html')
    text = re.sub(r'&lt;/?[A-Za-z][^\n<>]*?&gt;', escaped_tag, text)

    def script_style(match):
        removal('html_noncontent_block', match.group())
        return '\n'
    text = re.sub(r'<(script|style)\b[^>]*>[\s\S]*?</\1\s*>', script_style, text, flags=re.I)
    if re.search(r'<(?:script|style)\b', text, re.I):
        warn('unclosed_html_noncontent_block_preserved')

    def html_anchor(match):
        attrs, label = match.group(1), match.group(2)
        href = re.search(r'\bhref\s*=\s*([\'"])(.*?)\1', attrs, re.I | re.S)
        actions['html_anchor'] += 1
        return '[' + label + '](' + html.unescape(href.group(2)) + ')' if href else label
    text = re.sub(r'<a\b([^>]*)>([\s\S]*?)</a\s*>', html_anchor, text, flags=re.I)
    def html_image(match):
        removal('image', match.group())
        warn('image_removed_review_surrounding_references')
        return ''
    text = re.sub(r'<img\b[^>]*>', html_image, text, flags=re.I)
    text = re.sub(r'<!--[\s\S]*?-->', lambda m: removal('html_comment', m.group()) or '', text)

    def html_tag(match):
        name = match.group(2).lower()
        tag = match.group()
        closing = bool(match.group(1))
        if name in {'br', 'hr'}:
            removal('html_tag', tag)
            return '\n'
        if name == 'li':
            removal('html_tag', tag)
            return '\n' if closing else '\n- '
        if name in {'td', 'th'}:
            removal('html_tag', tag)
            return ' | '
        if name in BLOCK_TAGS:
            removal('html_tag', tag)
            return '\n\n'
        if name in INLINE_TAGS:
            removal('html_tag', tag)
            return ''
        # Type parameters and placeholders such as <T> and <API_KEY> are data.
        return tag
    text = re.sub(r'<(/?)([A-Za-z][\w:-]*)(?:\s[^<>]*?)?\s*/?>', html_tag, text)

    # Fully decode normal character entities (including double-escaped entities)
    # to a fixed point; nested angle-tag escapes remain protected as literals.
    for _ in range(8):
        decoded = html.unescape(text)
        if decoded == text:
            break
        actions['html_entities'] += 1
        text = decoded
        text = re.sub(r'&lt;/?[A-Za-z][^\n<>]*?&gt;', escaped_tag, text)
    else:
        warn('deeply_nested_entities_preserved')
    # Decoded literal markup must survive a second pass too.
    text = re.sub(r'&lt;/?[A-Za-z][^\n<>]*?&gt;', escaped_tag, text)

    nfc = unicodedata.normalize('NFC', text)
    if nfc != text:
        actions['unicode_nfc'] += 1
    text = nfc
    text = sub_count(r'[\u200b\u2060\ufeff]', '', text, 'zero_width_characters')
    # ZWJ/ZWNJ can be linguistically meaningful in Persian/Indic text or emoji.
    if '\u200c' in text or '\u200d' in text:
        protected['meaningful_joiners'] += text.count('\u200c') + text.count('\u200d')
    text = text.replace('\u00a0', ' ').replace('\u202f', ' ')

    # Parse only a bounded, verified leading frontmatter block. No general YAML
    # evaluation; ambiguous/unknown keys leave the entire block in place.
    lines = text.split('\n')
    start = next((i for i, s in enumerate(lines) if s.strip()), None)
    metadata_title = ''
    if start is not None and re.fullmatch(r'\s*---\s*', lines[start]):
        end = next((i for i in range(start + 1, min(start + 61, len(lines)))
                    if re.fullmatch(r'\s*-{3,}\s*', lines[i])), None)
        if end is not None:
            keys = []
            valid = True
            for line in lines[start + 1:end]:
                if not line.strip():
                    continue
                m = re.match(r'^([A-Za-z_]+):\s*(.*)$', line)
                if not m or m.group(1).lower() not in META_KEYS:
                    valid = False
                    break
                key = m.group(1).lower()
                keys.append(key)
                if key == 'title':
                    metadata_title = m.group(2).strip().strip('\'"')
            if valid and len(set(keys)) >= 2 and set(keys) & {'title', 'date', 'author', 'authors', 'url'}:
                removal('frontmatter', '\n'.join(lines[start:end + 1]))
                lines = lines[:start] + lines[end + 1:]
            elif any(re.match(r'^[A-Za-z_]+:', x) for x in lines[start + 1:end]):
                warn('ambiguous_frontmatter_preserved')
                lines = lines[:start] + [hold('\n'.join(lines[start:end + 1]), 'ambiguous_metadata')] + lines[end + 1:]
        elif any(re.match(r'^(?:title|date|authors?|url):', x) for x in lines[start + 1:start + 8]):
            warn('unclosed_frontmatter_preserved')
            lines = lines[:start] + [hold('\n'.join(lines[start:]), 'ambiguous_metadata')]
    text = '\n'.join(lines)

    # The released OWID capture omits all endnote definitions. Remove only
    # these explicitly recognized orphan-anchor markers, keep the surrounding
    # research attribution, and expose the source loss for review.
    if source_collection == 'coggen-owid':
        def orphan_note(match):
            removal('orphan_source_endnote_anchor', match.group())
            warn('source_endnotes_missing')
            return ''
        text = re.sub(r'\[(\d+)\]\(#note-\1\)', orphan_note, text)

    # Balanced Markdown inline link/image parser; no regex that truncates a URL
    # at its first nested closing parenthesis.
    reference_defs = {}
    def refdef(match):
        reference_defs[match.group(1).casefold()] = match.group(2)
        removal('link_reference_definition', match.group())
        return ''
    text = re.sub(r'^ {0,3}\[([^\]^]+)\]:\s*(<?\S+>?)(?:\s+[\'"].*?[\'"])?\s*$', refdef, text, flags=re.M)

    def visible_link(label, dest):
        dest = dest.strip()
        if dest.startswith('<') and dest.endswith('>'):
            dest = dest[1:-1]
        dest = re.sub(r'\s+[\'"][^\n]*[\'"]$', '', dest)
        plain_label = label.strip()
        actions['markdown_link'] += 1
        if not plain_label:
            return dest
        if re.fullmatch(r'\d+', plain_label) and dest.startswith('#'):
            return '[' + plain_label + ']'
        technical = bool(re.search(r'^(?:/|\./|\.\./)|[?{}=]|/(?:api|v\d+)(?:/|$)|localhost|\.(?:py|js|ts|json|ya?ml|sh|java|c|cpp|h)(?:$|#)', dest, re.I))
        technical = technical or prefix in label or bool(re.search(r'\b(?:GET|POST|PUT|DELETE|PATCH|endpoint|接口)\b', label))
        if dest and not dest.startswith('#') and technical and dest not in label:
            protected['link_destination'] += 1
            return plain_label + ' (' + dest + ')'
        if dest != plain_label:
            removal('markdown_link_destination', dest)
        return plain_label

    def links(value):
        output = []
        i = 0
        while i < len(value):
            image = value.startswith('![', i)
            if value[i] != '[' and not image:
                output.append(value[i]); i += 1; continue
            begin = i + (2 if image else 1)
            depth, j = 1, begin
            while j < len(value) and depth:
                if value[j] == '\\':
                    j += 2; continue
                if value[j] == '[': depth += 1
                if value[j] == ']': depth -= 1
                j += 1
            if depth:
                output.append(value[i]); i += 1; continue
            label = value[begin:j - 1]
            if j < len(value) and value[j] == '(':
                k, depth = j + 1, 1
                while k < len(value) and depth:
                    if value[k] == '\\':
                        k += 2; continue
                    if value[k] == '(': depth += 1
                    if value[k] == ')': depth -= 1
                    k += 1
                if depth:
                    warn('unbalanced_markdown_link_preserved')
                    output.append(value[i]); i += 1; continue
                dest, end = value[j + 1:k - 1], k
            elif j < len(value) and value[j] == '[':
                end = value.find(']', j + 1)
                key = value[j + 1:end] if end >= 0 else ''
                if not key: key = label
                if end < 0 or key.casefold() not in reference_defs:
                    output.append(value[i:j]); i = j; continue
                dest, end = reference_defs[key.casefold()], end + 1
            elif label.casefold() in reference_defs:
                dest, end = reference_defs[label.casefold()], j
            else:
                output.append(value[i:j]); i = j; continue
            span = value[i:end]
            if image:
                removal('image', span)
                warn('image_removed_review_surrounding_references')
                output.append('')
            else:
                output.append(visible_link(label, dest))
            i = end
        return ''.join(output)
    text = links(text)
    text = sub_count(r'<((?:https?://|mailto:)[^<>\s]+)>', lambda m: m.group(1), text, 'autolink_markup')

    # URLs and bare technical paths cannot have underscores/emphasis interpreted.
    text = re.sub(r'https?://[^\s<>]+|(?<!\w)/(?:[A-Za-z0-9_.{}:-]+/)+[A-Za-z0-9_.{}?=&:/%-]*',
                  lambda m: hold(m.group(), 'url_or_path'), text)
    # Keep tables intact; cell ordering and separator syntax carry information.
    table_lines = text.split('\n')
    for idx, line in enumerate(table_lines):
        if re.match(r'^\s*\|?(?:\s*:?-{3,}:?\s*\|)+\s*:?-{3,}:?\s*\|?\s*$', line):
            lo = idx - 1
            hi = idx + 1
            while hi < len(table_lines) and '|' in table_lines[hi] and table_lines[hi].strip(): hi += 1
            if lo >= 0:
                block = '\n'.join(table_lines[lo:hi])
                table_lines[lo] = hold(block, 'table')
                for k in range(lo + 1, hi): table_lines[k] = ''
    text = '\n'.join(table_lines)

    # Long inline underscore/asterisk runs may be a fraction bar, redaction,
    # or damaged layout. They are not a sequence of nested emphasis markers.
    # Standalone rules are still handled by the separator-removal rule below.
    inline_lines = text.split('\n')
    for line_no, line in enumerate(inline_lines):
        if not SEP_RE.fullmatch(line):
            def inline_rule(match):
                warn('inline_rule_or_fraction_bar_preserved_review_required')
                return hold(match.group(), 'inline_rule_or_fraction_bar')
            inline_lines[line_no] = re.sub(r'_{4,}|\*{4,}|~{4,}', inline_rule, line)
    text = '\n'.join(inline_lines)

    # Remove only paired emphasis delimiters, with word boundaries protecting
    # snake_case, arithmetic multiplication, wildcard paths and list bullets.
    for delim in ('**', '__', '*', '_', '~~'):
        pat = r'(?<![\w\\])' + re.escape(delim) + r'(?=\S)(.+?)(?<=\S)' + re.escape(delim) + r'(?!\w)'
        text = sub_count(pat, lambda m: m.group(1), text, 'emphasis_markup')

    spaced = _punctuation_spacing(text)
    if spaced != text:
        actions['prose_punctuation_spacing'] += 1
        text = spaced
    lines = text.split('\n')
    cleaned = []
    meaningful_prefix = []
    saw_body = False
    for idx, line in enumerate(lines):
        value = line.strip()
        if re.fullmatch(r'={3,}', value) and cleaned and any(x.strip() for x in cleaned):
            removal('setext_heading_markup', line)
            cleaned.append('')
            continue
        if SEP_RE.fullmatch(value):
            removal('separator', line)
            cleaned.append('')
            continue
        heading = re.match(r'^ {0,3}#{1,6}\s+(.+?)(?:\s+#+)?\s*$', line)
        if heading:
            value = heading.group(1).strip()
            actions['heading_markup'] += 1
        else:
            if re.match(r'^>\s*[-+]?\d', value):
                warn('possible_comparison_marker_preserved')
            else:
                value = re.sub(r'^ {0,3}(?:>\s*)+', '', value)
                if value != line.strip(): actions['quote_markup'] += 1
        leading = not saw_body and len(meaningful_prefix) < 5
        if leading and re.match(r'^(?:Home|首页|主页)\s*(?:>|›|»|/|→)\s*\S', value, re.I):
            removal('breadcrumb', line)
            continue
        byline = re.match(r'^(?:By\s*:\s*|作者\s*[:：]\s*|文\s*[:：]\s*)(.{1,160})$', value, re.I)
        # Unmarked "By X" needs a date separator, avoiding prose "By doing...".
        if not byline and re.search(r'\s[|·]\s*' + DATE + r'$', value, re.I):
            byline = re.match(r'^By\s+(.{1,160})$', value, re.I)
        if leading and byline:
            removal('byline', line)
            continue
        date_value = re.sub(r'^(?:Published|Updated|发布日期|发布时间|日期)\s*[:：]?\s*', '', value, flags=re.I)
        if leading and DATE_RE.fullmatch(date_value) and len(lines) > 1:
            removal('publication_date', line)
            continue
        # Move a verified leading document title out of the text body. The
        # caller retains title/provenance metadata separately. For OWID-style
        # title-plus-subtitle metadata, the first H1 must be its exact prefix.
        # Unmatched H1s and all section headings remain prose text.
        norm = re.sub(r'\s+', ' ', value).strip()
        article_context = (bool(metadata_title) or 'article' in str(source_unit_type).casefold()
                           or bool(re.search(r'\.pdf(?:$|[?#])', str(source_url), re.I))
                           or source_collection in {'coggen-owid', 'freshwiki', 'rewrite-article-v2',
                                                    'ai-enrichment-articles', 'ai-enrichment-comparison'})
        title_candidates = [re.sub(r'\s+', ' ', str(t)).strip() for t in (title, metadata_title) if t]
        title_matches = norm and any(norm == candidate or (heading and candidate.startswith(norm + ' '))
                                     for candidate in title_candidates)
        if article_context and not meaningful_prefix and title_matches:
            removal('document_title_to_metadata', line)
            continue
        # Only duplicate headings/prefix titles, never ordinary repeated prose.
        if leading and norm and (heading or norm in {str(title).strip(), metadata_title}) and norm in meaningful_prefix:
            removal('duplicate_leading_title', line)
            continue
        if value:
            meaningful_prefix.append(norm)
            # A title/subtitle is short and isolated; a prose paragraph closes
            # prefix-only removal even when it happens to contain a later byline.
            if len(value) > 240 or (not heading and re.search(r'[。.!?][\'"”’)]?$', value) and len(value) > 120):
                saw_body = True
        if prefix in value:
            cleaned.append(value)
        else:
            # Preserve list indentation, which can encode nesting. Prose indent
            # from PDF extraction is not a semantic distinction.
            indent = re.match(r'^([ \t]*)(?:[-+*]|\d+[.)])\s+', line)
            pad = indent.group(1).replace('\t', '    ') if indent else ''
            normalized = re.sub(r'[\t \f\v]+', ' ', value)
            if normalized != value or (not indent and line != line.strip()): actions['horizontal_whitespace'] += 1
            cleaned.append(pad + normalized)
    text = '\n'.join(cleaned).strip()
    # PDF prose often wraps at a fixed page column. Only join inside existing
    # paragraphs for an explicitly identified PDF source, never across blank
    # lines or through code, equations, lists, Javadoc or table-like material.
    # The same source metadata and rule must be supplied for both pair sides.
    pdf_source = bool(re.search(r'\.pdf(?:$|[?#])', str(source_url), re.I)) or 'pdf' in str(source_unit_type).casefold()
    if pdf_source:
        blocks = re.split(r'(\n\s*\n)', text)
        for bi in range(0, len(blocks), 2):
            block = blocks[bi]
            wrapped = block.split('\n')
            if len(wrapped) < 2 or any(not x.strip() for x in wrapped):
                continue
            if any(prefix in x or re.match(r'\s*(?:[-+*•]|\d+[.)]|@|#|\||[{}=])', x) or '|' in x for x in wrapped):
                continue
            if not all(len(x.strip()) >= 45 for x in wrapped[:-1]):
                continue
            if any(re.search(r'(?:[;{}]\s*$|^(?:def|class|function|return|const|let|var|import|SELECT)\b)', x) for x in wrapped):
                continue
            joined = wrapped[0].strip()
            for tail in wrapped[1:]:
                tail = tail.strip()
                if joined.endswith('-') and re.match(r'[a-z]', tail):
                    joined += tail
                    warn('pdf_line_end_hyphen_preserved_review_required')
                else:
                    joined += ' ' + tail
                actions['pdf_soft_wrap_joins'] += 1
            blocks[bi] = joined
        text = ''.join(blocks)
    # Soft PDF joins can expose spaces before punctuation across a line break.
    spaced = _punctuation_spacing(text)
    if spaced != text:
        actions['prose_punctuation_spacing'] += 1
        text = spaced
    text = sub_count(r'\n{3,}', '\n\n', text, 'blank_lines').strip()
    # Restore longest/newest tokens first because a table or URL can wrap an
    # earlier code token. No raw source can collide with the generated prefix.
    for token, value in reversed(list(tokens.items())):
        text = text.replace(token, value)
    if prefix in text:
        raise AssertionError('unrestored protection token')
    if original.strip() and not text.strip():
        warn('empty_after_cleaning')
    if len(original) >= 200 and len(text) < len(original) * .70:
        warn('high_deletion_ratio_review_required')
    if re.search(r'\b(?:Click here|Subscribe to|Sign up for|All rights reserved)\b|订阅|版权所有', text, re.I):
        warn('possible_residual_boilerplate_review_required')
    if re.search(r'<(?:script|style)\b|^\s*(?:title|authors?|date|url):', text, re.I | re.M):
        warn('possible_residual_metadata_review_required')
    return {'text': text, 'actions': dict(sorted(actions.items())), 'removed': removed,
            'warnings': warnings, 'protected': dict(sorted(protected.items()))}

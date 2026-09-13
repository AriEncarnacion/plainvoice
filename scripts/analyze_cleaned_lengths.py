#!/usr/bin/env python3
"""Compare raw and cleaned lengths on identical generated record IDs, read-only.

Uses the previous length-analysis counters. Outputs contain counts and provenance
hashes only, never source/rewrite prose. Does not modify previous statistics.
"""
import argparse
from collections import Counter, defaultdict
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
from statistics import mean, median
import zlib

from analyze_rewrite_lengths import HAN, WORDS

BASELINE_COLLECTIONS = {'ai-enrichment-articles', 'ai-enrichment-units'}
EXCLUSIONS = {
    'plainvoice-enrichment-svo-v3:68d31c2616d399a6570c761d': {
        'reason': 'failed_stub',
        'raw_right_sha256': '95b71313a45e592a6f606d91324c65f2b6b9a5684067ed678b78ab55665de39e',
    },
    'plainvoice-enrichment-svo-v3:0f6332ab6a7b52f9b3c37c15': {
        'reason': 'wrong_language',
        'raw_right_sha256': '8779908fe48cb5cf2927579d2783baf07b617e13fd95dca2105946a85e0180b1',
    },
}


def read_generated(path):
    with closing(sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)) as db:
        return {record['id']: record for (blob,) in db.execute(
            "SELECT payload FROM records WHERE collection LIKE 'ai-enrichment-%'"
        ) for record in [json.loads(zlib.decompress(blob))]}


def summarize(rows, view):
    if not rows:
        return {'n': 0}
    assert len({r['language'] for r in rows}) == 1, 'Do not pool Chinese characters and English words'
    originals = [row[view]['original'] for row in rows]
    rewrites = [row[view]['rewritten'] for row in rows]
    assert all(value > 0 for value in originals), 'Zero source count requires a separate cohort'
    changes = [(b / a - 1) * 100 for a, b in zip(originals, rewrites)]
    return {
        'n': len(rows), 'source_total': sum(originals), 'rewrite_total': sum(rewrites),
        'source_mean': mean(originals), 'rewrite_mean': mean(rewrites),
        'longer': sum(b > a for a, b in zip(originals, rewrites)),
        'equal': sum(b == a for a, b in zip(originals, rewrites)),
        'shorter': sum(b < a for a, b in zip(originals, rewrites)),
        'longer_pct': sum(b > a for a, b in zip(originals, rewrites)) / len(rows) * 100,
        'median_pair_change_pct': median(changes),
        'total_pair_change_pct': (sum(rewrites) / sum(originals) - 1) * 100,
    }


def compare(rows):
    raw, clean = summarize(rows, 'raw'), summarize(rows, 'clean')
    changes = {}
    for label, field in [('original', 'source_total'), ('rewritten', 'rewrite_total')]:
        changes[label] = {
            'count_delta': clean[field] - raw[field],
            'count_change_pct': (clean[field] / raw[field] - 1) * 100 if raw[field] else None,
            'records_with_count_change': sum(row['raw'][label] != row['clean'][label] for row in rows),
        }
    return {'raw': raw, 'clean': clean, 'cleaning_effect': changes}


def analyze(raw_path, clean_path, output):
    raw_records, clean_records = read_generated(raw_path), read_generated(clean_path)
    if not raw_records or raw_records.keys() != clean_records.keys():
        raise ValueError('Raw/clean generated record ID sets are empty or do not match')
    rows = []
    versions, rules = set(), set()
    for record_id in sorted(raw_records):
        original, clean = raw_records[record_id], clean_records[record_id]
        if original['language'] not in ('en', 'zh'):
            continue
        cleaning = clean['extra']['cleaning']
        assert cleaning['raw_content_hash'] == original['content_hash'], (record_id, 'raw hash mismatch')
        assert clean['language'] == original['language'], (record_id, 'language metadata drift')
        assert clean['collection'] == original['collection'], (record_id, 'collection drift')
        versions.add(cleaning['version'])
        rules.add(cleaning['rules_sha256'])
        exclusion = EXCLUSIONS.get(record_id)
        if exclusion:
            actual = hashlib.sha256(original['right']['text'].encode()).hexdigest()
            assert actual == exclusion['raw_right_sha256'], (record_id, 'stale failure exclusion')
        counter = HAN if original['language'] == 'zh' else WORDS
        counts = {}
        for view, record in [('raw', original), ('clean', clean)]:
            counts[view] = {'original': len(counter.findall(record['left']['text'])),
                            'rewritten': len(counter.findall(record['right']['text']))}
        rows.append({
            'id': record_id, 'source_id': original['provenance']['source_record_id'],
            'collection': original['collection'], 'language': original['language'],
            'source_collection': original['extra']['source_collection'],
            'model': original['extra']['generation']['model'],
            'raw_content_hash': original['content_hash'], 'clean_content_hash': clean['content_hash'],
            'quality_status': cleaning['status'],
            'excluded_reason': exclusion['reason'] if exclusion else None, **counts,
        })
    assert EXCLUSIONS.keys() <= raw_records.keys(), 'Expected dated failure records are absent'
    baseline = [row for row in rows if row['collection'] in BASELINE_COLLECTIONS]
    previous = [row for row in baseline if row['excluded_reason'] != 'failed_stub']
    matched = [row for row in baseline if row['excluded_reason'] is None]
    assert len({row['source_id'] for row in matched}) == len(matched), 'Baseline source IDs are not unique'
    groups = defaultdict(list)
    for row in matched:
        groups['baseline/' + row['language']].append(row)
        groups[row['collection'] + '/' + row['language']].append(row)
        groups['baseline_source/' + row['source_collection'] + '/' + row['language']].append(row)
    for row in rows:
        if row['collection'] not in BASELINE_COLLECTIONS and row['excluded_reason'] is None:
            groups[row['collection'] + '/' + row['language']].append(row)
    group_results = {name: compare(group) for name, group in sorted(groups.items())}
    previous_groups = {lang: summarize([row for row in previous if row['language'] == lang], 'raw')
                       for lang in ('en', 'zh')}
    summary = {
        'schema_version': 'plainvoice-clean-length-comparison-v1',
        'cleaning_versions': sorted(versions), 'cleaning_rules_sha256': sorted(rules),
        'units': {'zh': 'Han characters; punctuation, digits, whitespace and Latin letters excluded',
                  'en': 'English letter words; apostrophes internal, hyphens split; digits excluded'},
        'saved_generated_records': len(rows),
        'previous_filter_baseline_n': len(previous),
        'matched_raw_clean_baseline_n': len(matched),
        'exclusions': [{'id': row['id'], 'reason': row['excluded_reason']} for row in rows if row['excluded_reason']],
        'matched_baseline_quality_status_counts': dict(Counter(row['quality_status'] for row in matched)),
        'previous_raw_filter_only': previous_groups,
        'groups': group_results,
        'records': rows,
        'limitations': [
            'Same IDs are compared between raw and clean; the previous cohort additionally contained one wrong-language output.',
            'Formatting-only comparison retains other semantic-risk/quarantined cases, so it is not a training-eligible or gold cohort.',
            'Cleanup includes known scraped metadata; no model regeneration or semantic restoration occurred.',
            'Human source attribution is inherited, not independently authenticated. Language and source are confounded.',
        ],
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / 'length-comparison.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    report = [
        '# 清理格式后：原文与 AI 稿的长度变化', '',
        f"本次读取 {len(rows)} 条已生成候选。之前 Gemini 2.5 主统计排除了失败短稿，N={len(previous)}；本次另外排除一条误写成英文的中文任务，主分析 N={len(matched)}。下表每一行的原始版、清理版使用完全相同的记录 ID，避免把换样本造成的变化当成清理效果。", '',
        '计数沿用之前口径：中文只计汉字；英文计字母词，词内撇号不拆、连字符拆开，数字不计。先逐条计算 AI / 原文 − 1，再取中位数。代码、公式和有内容意义的标题可能保留，因此也不是模型 token 数。', '',
        '| 同一批样本 | N | 原文平均：清理前 → 后 | AI 平均：清理前 → 后 | AI 相对原文变化中位数：清理前 → 后 |',
        '|---|---:|---:|---:|---:|',
    ]
    labels = [
        ('中文短句 · 2.5', 'ai-enrichment-units/zh'),
        ('英文句段／技术片段 · 2.5', 'ai-enrichment-units/en'),
        ('英文全文 · 2.5', 'ai-enrichment-articles/en'),
        ('中文全文 · 2.5', 'ai-enrichment-articles/zh'),
        ('英文全文 · 3.1 对照', 'ai-enrichment-comparison/en'),
        ('中文全文 · 3.1 对照', 'ai-enrichment-comparison/zh'),
    ]
    for label, key in labels:
        if key not in group_results:
            continue
        result = group_results[key]
        a, b = result['raw'], result['clean']
        report.append(f"| {label} | {a['n']} | {a['source_mean']:.1f} → {b['source_mean']:.1f} | {a['rewrite_mean']:.1f} → {b['rewrite_mean']:.1f} | {a['median_pair_change_pct']:+.1f}% → {b['median_pair_change_pct']:+.1f}% |")
    report += ['', '格式与网页杂项对计数的影响：', '']
    for lang, unit in [('zh', '汉字'), ('en', '词')]:
        key = 'baseline/' + lang
        if key not in group_results:
            continue
        result = group_results[key]
        source, rewrite = result['cleaning_effect']['original'], result['cleaning_effect']['rewritten']
        report.append(f"- {'中文' if lang == 'zh' else '英文'}同一批 {result['raw']['n']} 条：原文合计 {source['count_delta']:+,} {unit}（{source['count_change_pct']:+.2f}%），AI 稿合计 {rewrite['count_delta']:+,} {unit}（{rewrite['count_change_pct']:+.2f}%）；分别有 {source['records_with_count_change']}、{rewrite['records_with_count_change']} 条计数发生变化。")
    article = group_results.get('ai-enrichment-articles/en')
    if article:
        a, b = article['raw'], article['clean']
        conclusion = '仍然更常缩短' if b['shorter'] > b['longer'] else '更常变长' if b['longer'] > b['shorter'] else '变长与变短数量相同'
        report += ['', f"英文全文清理后{conclusion}：{b['shorter']}/{b['n']} 条比原文短、{b['longer']}/{b['n']} 条变长。相对长度变化中位数由 {a['median_pair_change_pct']:+.1f}% 变为 {b['median_pair_change_pct']:+.1f}%。这说明格式杂项确实影响计数，但篇幅变化本身不能说明保真或写作质量。"]
    report += ['',
        '质量边界：这里只比较格式清理的影响；除失败短稿与错误语言两条外，其余已隔离的语义风险样本仍留在同 ID 的描述统计中。它们不能因此进入训练候选或变成 ground truth。中文短句来源集中于 MCTS，中英文差异不能归因于语言本身。中文全文样本很少。', '',
        '六条 Gemini 3.1 对照与五条早期诊断稿单独保留在 JSON 分组中，不并入 Gemini 2.5 主统计。所有数字由脚本计算；报告不含原文或生成正文。之前的统计文件保持不变。', '',
        '数据：`length-comparison.json` 包含逐条前后计数、分组结果、原始／清理后内容哈希和两条排除原因。脚本：`scripts/analyze_cleaned_lengths.py`。',
    ]
    (output / 'length-comparison.md').write_text('\n'.join(report) + '\n')
    print(json.dumps({'saved': len(rows), 'previous_baseline': len(previous), 'matched_baseline': len(matched),
                      'output': str(output)}, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw-database', required=True, type=Path)
    parser.add_argument('--clean-database', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    analyze(args.raw_database, args.clean_database, args.output)

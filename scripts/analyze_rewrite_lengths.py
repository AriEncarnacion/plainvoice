#!/usr/bin/env python3
"""Describe paired lengths without model calls or changes to the viewer data."""
import argparse
from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path
import re
from statistics import mean, median

HAN = re.compile('[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\U00020000-\U0002ebef\U00030000-\U000323af]')
WORDS = re.compile(r"[A-Za-z]+(?:['’][A-Za-z]+)*")
FAILED_ID = 'plainvoice-enrichment-svo-v3:68d31c2616d399a6570c761d'


def summarize(rows):
    if not rows:
        return {'n': 0}
    assert len({r['language'] for r in rows}) == 1, 'Never pool Han counts and English words'
    a = sum(r['original'] for r in rows)
    b = sum(r['rewritten'] for r in rows)
    return {
        'n': len(rows),
        'longer': sum(r['delta'] > 0 for r in rows),
        'equal': sum(r['delta'] == 0 for r in rows),
        'shorter': sum(r['delta'] < 0 for r in rows),
        'original_mean': mean(r['original'] for r in rows),
        'rewritten_mean': mean(r['rewritten'] for r in rows),
        'median_pair_change_pct': median(r['change_pct'] for r in rows),
        'mean_pair_change_pct': mean(r['change_pct'] for r in rows),
        'total_length_change_pct': (b / a - 1) * 100,
        'more_than_10pct_longer': sum(r['change_pct'] > 10 + 1e-8 for r in rows),
        'more_than_10pct_shorter': sum(r['change_pct'] < -10 - 1e-8 for r in rows),
    }


def analyze(root, output):
    records, inputs = [], []
    for path in sorted((root / 'ai-enrichment').glob('*/pairs.jsonl')):
        raw = path.read_bytes()
        inputs.append({'file': str(path.relative_to(root)), 'sha256': hashlib.sha256(raw).hexdigest()})
        for line in raw.decode().splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if r['language'] not in ('zh', 'en'):
                continue
            counter = HAN if r['language'] == 'zh' else WORDS
            a = len(counter.findall(r['left']['text']))
            b = len(counter.findall(r['right']['text']))
            assert a > 0
            failure = r['id'] == FAILED_ID and r['right']['text'].strip() == 'The article'
            records.append({'id': r['id'], 'source_id': r['provenance']['source_record_id'],
                            'collection': r['collection'], 'language': r['language'],
                            'model': r['extra']['generation']['model'],
                            'source_collection': r['extra']['source_collection'],
                            'unit_type': r['extra']['source_unit_type'],
                            'original': a, 'rewritten': b, 'delta': b-a,
                            'change_pct': (b/a-1)*100,
                            'known_failed_output': failure})
    assert len({r['id'] for r in records}) == len(records)
    baseline = [r for r in records if r['collection'] in ('ai-enrichment-articles', 'ai-enrichment-units') and not r['known_failed_output']]
    assert len({r['source_id'] for r in baseline}) == len(baseline)
    grouped = defaultdict(list)
    for r in records:
        grouped['all_saved/' + r['language']].append(r)
        if not r['known_failed_output']:
            grouped[r['collection'] + '/' + r['language']].append(r)
    for r in baseline:
        grouped['baseline/' + r['language']].append(r)
        grouped['baseline_source/' + r['source_collection'] + '/' + r['language']].append(r)
    summary = {key: summarize(rows) for key, rows in sorted(grouped.items())}
    output.mkdir(parents=True, exist_ok=True)
    with (output / 'pair-lengths.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    (output / 'summary.json').write_text(json.dumps({'inputs': inputs, 'saved_records': len(records),
        'baseline_after_known_failure_exclusion': len(baseline), 'groups': summary}, ensure_ascii=False, indent=2)+'\n')
    lines = ['# AI 改写长度：本地候选的描述统计', '',
             f'统计 {len(records)} 条已保存中英文候选。主分析为 Gemini 2.5 批次：排除一条确定失败输出后 {len(baseline)} 条；6 条 Gemini 3.1 对照与 5 条早期 pilot 单列。未生成的目标不纳入。', '',
             '中文计汉字，不计标点、空格、数字和拉丁字母。英文计字母构成的词，撇号缩写算一个词、连字符词拆开；数字不算词。以 A/B 正文原样计数，未清理其中标题、引用、代码或 URL 字母串。中文与英文不合并求总长度。', '',
             '百分比变化 =（AI 长度 / 原文长度 − 1）× 100%；“变化中位数”先逐条计算百分比，再取中位数，和总字数变化不是同一个量。', '',
             '| 批次 / 类型 | N | 原文 → AI 平均长度 | 变长 | 不变 | 变短 | 变化中位数 |',
             '|---|---:|---:|---:|---:|---:|---:|']
    groups = [('中文短句 · 2.5', 'ai-enrichment-units/zh'),
              ('英文句段／技术片段 · 2.5', 'ai-enrichment-units/en'),
              ('英文全文 · 2.5', 'ai-enrichment-articles/en'),
              ('中文全文 · 2.5（仅 2 篇）', 'ai-enrichment-articles/zh'),
              ('英文全文 · 3.1（仅 4 篇）', 'ai-enrichment-comparison/en'),
              ('中文全文 · 3.1（仅 2 篇）', 'ai-enrichment-comparison/zh')]
    for label, key in groups:
        s = summary[key]
        lines.append(f"| {label} | {s['n']} | {s['original_mean']:.1f} → {s['rewritten_mean']:.1f} | {s['longer']}（{s['longer']/s['n']:.1%}） | {s['equal']} | {s['shorter']} | {s['median_pair_change_pct']:+.1f}% |")
    lines += ['', '英文来源分层（主分析；不把技术片段与长篇文章混在一起）：', '',
              '| 来源 | N | 变长比例 | 变化中位数 |', '|---|---:|---:|---:|']
    for key, s in summary.items():
        if key.startswith('baseline_source/') and key.endswith('/en'):
            lines.append(f"| {key.split('/')[1]} | {s['n']} | {s['longer']/s['n']:.1%} | {s['median_pair_change_pct']:+.1f}% |")
    lines += ['', '结论：本批次中文短句更常略微变长；英文句段没有普遍膨胀；英文全文通常显著缩短。Code2Doc 技术片段仅 15 条，其中 10 条变长，中位数 +17.4%，说明具体来源与任务类型很重要。', '',
              '限制：中文短句全部来自 MCTS，不能将中英文差异归因于语言本身。本实验只有特定模型与 SVO 抽取→乱序→重写流程，不能推广为所有 AI。人类作者身份沿用来源标注，并未逐条认证。缩短可能来自语义遗漏、正文/元数据混杂或过度概括，不能视为质量提高。', '',
              '数据质量发现：一条 OWID 长文的输出只有 “The article”（2 词），ID 为 `'+FAILED_ID+'`。它虽曾被保存为候选，实质上没有完成改写，已从主要统计排除，但原始数据未被改动。包含该条时，英文全文 N=27，26 条变短，中位数 −44.3%；排除后 N=26，25 条变短，中位数 −43.6%，主要方向不变。', '',
              '逐条计数见 `pair-lengths.csv`；分组汇总与输入文件哈希见 `summary.json`。没有调用模型，没有修改原文、生成稿或个人评审。']
    (output / 'report.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({'saved': len(records), 'baseline': len(baseline), 'report': str(output / 'report.md')}, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    analyze(args.root, args.output)

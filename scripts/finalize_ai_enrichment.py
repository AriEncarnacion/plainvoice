#!/usr/bin/env python3
"""Freeze generated review pairs, attach scoped QA, and account for every run.

Run only after all generation workers have stopped. Original generated pairs are
kept beside the finalized viewer input; no original viewer records are changed.
"""
import argparse
from collections import Counter
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile


def stage_file(path, *, data=None, source=None):
    """Create a durable sibling temporary file without changing a named input."""
    fd, name = tempfile.mkstemp(prefix='.' + path.name + '.', suffix='.tmp', dir=path.parent)
    temp = Path(name)
    try:
        with os.fdopen(fd, 'wb') as handle:
            if source is not None:
                with source.open('rb') as original:
                    shutil.copyfileobj(original, handle)
            else:
                handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        return temp
    except BaseException:
        temp.unlink(missing_ok=True)
        raise


def finalize(root, flag_paths, queue):
    folder = root / 'ai-enrichment'
    flags = {}
    for path in flag_paths:
        for source_id, flag in json.loads(path.read_text()).items():
            key = flag['applies_to']['pair_id']
            if key in flags and flags[key] != flag:
                raise ValueError('Conflicting scoped QA for ' + key)
            flags[key] = flag
    ledgers = []
    spent = held = Decimal(0)
    for path in sorted(folder.glob('*/budget-ledger.json')):
        ledger = json.loads(path.read_text())
        if any(e['state'] == 'pending' for e in ledger['entries']):
            raise ValueError('A worker still has pending requests: ' + str(path))
        known = sum((Decimal(e['actual_usd']) for e in ledger['entries'] if e['state'] == 'settled'), Decimal(0))
        unknown = sum((Decimal(e.get('held_usd', e['reserved_usd'])) for e in ledger['entries'] if e['state'] != 'settled'), Decimal(0))
        spent += known
        held += unknown
        ledgers.append({'run': path.parent.name, 'model': ledger['model'],
                        'calls': len(ledger['entries']), 'spent_usd': str(known),
                        'held_usd': str(unknown),
                        'request_states': dict(Counter(e['state'] for e in ledger['entries']))})
    if spent + held > Decimal('20'):
        raise ValueError('Combined recorded cost exposure exceeds user authorization')
    records = []
    applied = []
    planned = []
    for run in sorted(p for p in folder.iterdir() if p.is_dir()):
        diagnostic = (run / 'pilot-pairs.jsonl').exists()
        original = run / ('pilot-pairs.jsonl' if diagnostic else 'pairs.generated.jsonl')
        target = run / 'pairs.jsonl'
        preserve_original = not original.exists()
        source = target if preserve_original else original
        if not source.exists():
            continue
        rows = [json.loads(line) for line in source.read_text(encoding='utf-8').splitlines() if line]
        for row in rows:
            if diagnostic:
                row['collection'] = 'ai-enrichment-diagnostics'
                row['collection_title'] = 'AI 补全 · 早期 pilot 诊断'
                row['right']['label'] += ' · 早期 pilot'
                row['context'] = '早期提示版本的诊断候选；不属于最新批次。\n' + row.get('context', '')
            flag = flags.get(row['id'])
            if flag:
                scope = flag['applies_to']
                actual = hashlib.sha256(row['right']['text'].encode()).hexdigest()
                if (scope['model'] != row['extra']['generation']['model'] or
                    actual != scope['writer_text_sha256'] or
                    row['extra']['source_sha256'] != scope['selected_source_sha256']):
                    raise ValueError('Scoped QA does not match exact output: ' + row['id'])
                row['extra']['independent_agent_review'] = flag
                row['extra']['qa']['independent_agent_review'] = flag['status']
                row['extra']['qa']['flags'].append('independent_agent_found_fidelity_issues')
                row['right']['label'] += ' · 已发现保真问题'
                row['context'] = '独立 agent 抽查发现：' + '；'.join(flag['findings']) + '\n\n' + row.get('context', '')
                applied.append(row['id'])
            elif row.get('extra', {}).get('qa', {}).get('flags'):
                row['context'] = '自动检查有待核对提示；详情见 QA，尚未经人工验收。\n\n' + row.get('context', '')
            records.append(row)
        planned.append((target, original if preserve_original else None, rows))
    if len({r['id'] for r in records}) != len(records):
        raise ValueError('Duplicate generated pair IDs')
    if set(flags) != set(applied):
        raise ValueError('Some scoped QA did not find its exact output')
    primary = [r for r in records if r['collection'] != 'ai-enrichment-diagnostics']
    source_ids = {r['provenance']['source_record_id'] for r in primary}
    target_rows = [json.loads(x) for x in queue.read_text().splitlines() if x]
    target_rows = [r for r in target_rows if r['target_language'] != 'ja']
    failures_by_source = {}
    for path in sorted(folder.glob('*/failures.json')):
        for failure in json.loads(path.read_text()):
            failures_by_source.setdefault(failure['source_id'], []).append({
                'run': path.parent.name, 'reason': failure['reason']})
    report = {'schema_version': 'plainvoice-enrichment-delivery-1',
              'pairs': len(records), 'main_and_comparison_pairs': len(primary),
              'diagnostic_pairs': len(records) - len(primary),
              'unique_target_sources_with_new_ai': len(source_ids),
              'target_sources': len(target_rows),
              'uncovered_targets': [{'source_id': r['source_id'], 'source_unit_type': r['source_unit_type'],
                                     'failures': failures_by_source.get(r['source_id'], [])}
                                    for r in target_rows if r['source_id'] not in source_ids],
              'collections': dict(Counter(r['collection'] for r in records)),
              'languages': dict(Counter(r['language'] for r in records)),
              'source_collections': dict(Counter(r['extra']['source_collection'] for r in primary)),
              'scoped_independent_agent_defect_flags': len(applied),
              'known_spent_usd': str(spent), 'unresolved_reserved_usd': str(held),
              'maximum_recorded_exposure_usd': str(spent + held), 'ledgers': ledgers,
              'gold_status': 'none; all generated records are candidates awaiting human review'}
    notes_path = folder / 'delivery-notes.json'
    if notes_path.exists():
        report['delivery_notes'] = json.loads(notes_path.read_text())
    for item in report['uncovered_targets']:
        item['status'] = 'failed_or_interrupted' if item['failures'] else 'not_attempted'
    # All scope, duplicate, accounting and queue validation above is read-only.
    # Stage every output before preserving originals or publishing viewer inputs.
    # Copy originals so even an interrupted commit never removes a viewer input.
    # Re-running is safe: preserved originals remain the source of truth.
    staged = []
    try:
        for target, original, rows in planned:
            if original is not None:
                staged.append((stage_file(original, source=target), original))
        for target, _, rows in planned:
            data = ''.join(json.dumps(row, ensure_ascii=False, separators=(',', ':')) + '\n'
                           for row in rows).encode('utf-8')
            staged.append((stage_file(target, data=data), target))
        summary = folder / 'delivery-summary.json'
        data = (json.dumps(report, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
        staged.append((stage_file(summary, data=data), summary))
        for temp, target in staged:
            os.replace(temp, target)
        for directory in {target.parent for _, target in staged}:
            fd = os.open(directory, os.O_RDONLY)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)
    finally:
        for temp, _ in staged:
            temp.unlink(missing_ok=True)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--queue', required=True, type=Path)
    parser.add_argument('--flags', action='append', type=Path, default=[])
    args = parser.parse_args()
    finalize(args.root, args.flags, args.queue)

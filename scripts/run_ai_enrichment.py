#!/usr/bin/env python3
"""Generate review candidates from a deterministic queue with a bounded API client.

Each source is processed in two independent calls: semantic extraction, then
fresh writing from a shuffled packet without original prose or source locators.
Whole downloaded articles are never split into independent paragraph rewrites.
"""
import argparse
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import random
import re
import threading
import time
from types import SimpleNamespace

from browser_key_bridge import receive_key
from plainvoice_budget_client import BudgetClient, BudgetError

VERSION = 'plainvoice-enrichment-svo-v3'
SCRIPT_ROOT = Path(__file__).resolve().parent.parent


def obj(properties):
    return {'type': 'object', 'properties': properties,
            'required': list(properties), 'additionalProperties': False}


STR = {'type': 'string'}
STRS = {'type': 'array', 'items': STR}
EXTRACT_SCHEMA = obj({
    'claims': {'type': 'array', 'items': obj({
        'subject': STR, 'predicate': STR, 'object': STR, 'qualifiers': STRS,
        'attribution': {'type': ['string', 'null']}, 'source_units': STRS})},
    'excluded_units': {'type': 'array', 'items': obj({'unit': STR, 'reason': STR})},
    'uncovered_units': STRS,
})
WRITE_SCHEMA = obj({'text': STR, 'covered_claim_ids': STRS,
                    'unresolved_claim_ids': STRS, 'issues': STRS})


def extraction_schema(source_units):
    claim = obj({k: v for k, v in EXTRACT_SCHEMA['properties']['claims']['items']['properties'].items()
                 if k != 'source_units'})
    assessment = obj({'unit_id': {'type': 'string', 'enum': [u['unit'] for u in source_units]},
                      'claims': {'type': 'array', 'items': claim},
                      'excluded_reason': {'type': ['string', 'null']},
                      'unresolved': {'type': 'boolean'}})
    return obj({'by_unit': {'type': 'array', 'items': assessment}})


def normalize_extraction(raw, source_units, warnings=None):
    warnings = warnings if warnings is not None else []
    if isinstance(raw, dict) and isinstance(raw.get('by_unit'), list):
        assessments = raw['by_unit']
        if len(assessments) != len(source_units) or len({a['unit_id'] for a in assessments}) != len(assessments):
            raise ValueError('duplicate_or_missing_unit_assessments')
        raw = {'by_unit': {a['unit_id']: {k: v for k, v in a.items() if k != 'unit_id'} for a in assessments}}
    if (not isinstance(raw, dict) or set(raw) != {'by_unit'}
            or not isinstance(raw['by_unit'], dict)
            or set(raw['by_unit']) != {u['unit'] for u in source_units}):
        raise ValueError('unit_assessment_mismatch')
    result = {'claims': [], 'excluded_units': [], 'uncovered_units': []}
    for uid, assessment in raw['by_unit'].items():
        if (not isinstance(assessment, dict)
                or set(assessment) != {'claims', 'excluded_reason', 'unresolved'}
                or not isinstance(assessment['claims'], list)
                or type(assessment['unresolved']) is not bool
                or (assessment['excluded_reason'] is not None
                    and (not isinstance(assessment['excluded_reason'], str)
                         or not assessment['excluded_reason'].strip()))):
            raise ValueError('invalid_unit_assessment')
        if assessment['claims'] and assessment['excluded_reason'] is not None:
            warnings.append({'stage': 'extraction', 'unit_id': uid,
                             'issue': 'contradictory_exclusion_dropped_claims_retained'})
            assessment = {**assessment, 'excluded_reason': None}
        for claim in assessment['claims']:
            if (not isinstance(claim, dict)
                    or set(claim) != {'subject', 'predicate', 'object', 'qualifiers', 'attribution'}):
                raise ValueError('claim_structure')
            result['claims'].append({**claim, 'source_units': [uid]})
        if assessment['excluded_reason']:
            result['excluded_units'].append({'unit': uid, 'reason': assessment['excluded_reason']})
        if assessment['unresolved'] or (not assessment['claims'] and not assessment['excluded_reason']):
            result['uncovered_units'].append(uid)
    return result


def writing_schema(packet):
    evidence = obj({'claim_id': {'type': 'string', 'enum': [c['id'] for c in packet['claims']]},
                    'status': {'type': 'string', 'enum': ['covered', 'unresolved']}, 'evidence': STRS})
    return obj({'text': STR, 'coverage': {'type': 'array', 'items': evidence}, 'issues': STRS})


def normalize_writing(raw, packet, warnings=None):
    warnings = warnings if warnings is not None else []
    if isinstance(raw, dict) and isinstance(raw.get('coverage'), list):
        assessments = raw['coverage']
        if len(assessments) != len(packet['claims']) or len({a['claim_id'] for a in assessments}) != len(assessments):
            raise ValueError('duplicate_or_missing_claim_assessments')
        raw = {**raw, 'coverage': {a['claim_id']: {k: v for k, v in a.items() if k != 'claim_id'} for a in assessments}}
    if (not isinstance(raw, dict) or set(raw) != {'text', 'coverage', 'issues'}
            or not isinstance(raw['coverage'], dict)
            or set(raw['coverage']) != {c['id'] for c in packet['claims']}):
        raise ValueError('claim_assessment_mismatch')
    if not isinstance(raw['issues'], list) or not all(isinstance(s, str) for s in raw['issues']):
        raise ValueError('invalid_writing_issues')
    if not isinstance(raw['text'], str) or not raw['text'].strip():
        raise ValueError('empty_writing')
    normalize = lambda s: ' '.join(s.split())
    text = normalize(raw['text'])
    coverage = {}
    issues = list(raw['issues'])
    for claim_id, value in raw['coverage'].items():
        if (not isinstance(value, dict) or set(value) != {'status', 'evidence'}
                or not isinstance(value['evidence'], list)
                or not all(isinstance(span, str) for span in value['evidence'])):
            raise ValueError('invalid_claim_assessment')
        if value['status'] not in ('covered', 'unresolved'):
            raise ValueError('invalid_coverage_status')
        if value['status'] == 'covered' and (not value['evidence'] or
                any(not span.strip() or normalize(span) not in text for span in value['evidence'])):
            warnings.append({'stage': 'writing', 'claim_id': claim_id,
                             'issue': 'evidence_not_found_claim_marked_unresolved'})
            issues.append('Evidence for ' + claim_id + ' was absent or did not match the writing; human review required.')
            value = {**value, 'status': 'unresolved'}
        coverage[claim_id] = value
    return {'text': raw['text'],
            'covered_claim_ids': [k for k, v in coverage.items() if v['status'] == 'covered'],
            'unresolved_claim_ids': [k for k, v in coverage.items() if v['status'] == 'unresolved'],
            'issues': issues}


def load_saved_stage(item_dir, stage, ledger_path):
    """Reuse only accepted, settled responses with matching accounting identity."""
    raw_path = item_dir / (stage + '-raw.json')
    call_path = item_dir / (stage + '-call.json')
    if not raw_path.exists() or not call_path.exists():
        return None
    call = json.loads(call_path.read_text())
    ledger = json.loads(ledger_path.read_text())
    entry = next((e for e in ledger['entries'] if e['id'] == call.get('ledger_id')), None)
    if not entry or entry['state'] != 'settled' or entry.get('outcome') != 'accepted':
        return None
    recorded = entry.get('metadata', {})
    if (call.get('model') != ledger.get('model')
            or call.get('generation_id') != recorded.get('generation_id')
            or call.get('cost_usd') != recorded.get('cost_usd')
            or call.get('cost_usd') != entry.get('actual_usd')):
        return None
    return SimpleNamespace(parsed=json.loads(raw_path.read_text()), metadata=call)


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    with temp.open('w', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')
        f.flush()
        os.fsync(f.fileno())
    os.replace(temp, path)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'))


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def units(text):
    # Paragraph IDs are extraction audit only; no units or order reach writing.
    # Do not split code fences at blank lines.
    chunks, current, fence = [], [], None
    for line in text.splitlines():
        marker = re.match(r'^\s{0,3}(`{3,}|~{3,})', line)
        if fence is None and marker:
            fence = (marker.group(1)[0], len(marker.group(1)))
        elif fence is not None and re.fullmatch(
                r'\s{0,3}' + re.escape(fence[0]) + '{' + str(fence[1]) + r',}\s*', line):
            fence = None
        if not line.strip() and fence is None and current:
            chunks.append('\n'.join(current))
            current = []
        elif line.strip() or current:
            current.append(line)
    if current:
        chunks.append('\n'.join(current))
    return [{'unit': f'u{i:04d}', 'text': t} for i, t in enumerate(chunks, 1)]


def validate_extraction(data, source_units):
    if not isinstance(data, dict) or set(data) != set(EXTRACT_SCHEMA['properties']):
        raise ValueError('extraction_structure')
    if not data['claims'] or data['uncovered_units']:
        raise ValueError('no_claims_or_uncovered_units')
    expected = {u['unit'] for u in source_units}
    seen = set()
    for claim in data['claims']:
        if set(claim) != set(EXTRACT_SCHEMA['properties']['claims']['items']['properties']):
            raise ValueError('claim_structure')
        if any(not isinstance(claim[k], str) or not claim[k].strip()
               for k in ('subject', 'predicate', 'object')):
            raise ValueError('empty_claim')
        if not claim['source_units'] or not set(claim['source_units']) <= expected:
            raise ValueError('invalid_claim_units')
        if not isinstance(claim['qualifiers'], list) or not all(isinstance(s, str) for s in claim['qualifiers']):
            raise ValueError('invalid_qualifiers')
        if claim['attribution'] is not None and not isinstance(claim['attribution'], str):
            raise ValueError('invalid_attribution')
        seen.update(claim['source_units'])
    for excluded in data['excluded_units']:
        if excluded['unit'] not in expected or not excluded['reason'].strip():
            raise ValueError('invalid_exclusion')
        seen.add(excluded['unit'])
    if seen != expected:
        raise ValueError('unit_coverage_mismatch')


def packet_for(data, q):
    seed = digest(VERSION + '|' + q['queue_id'])
    rng = random.Random(seed)
    # Source position is discarded; content-dependent IDs cannot reveal order.
    packet_claims = []
    for claim in data['claims']:
        clean = {k: claim[k] for k in ('subject', 'predicate', 'object', 'qualifiers', 'attribution')}
        clean['id'] = 'c_' + digest(canonical(clean))[:20]
        packet_claims.append(clean)
    # Duplicate semantic cards add no new content; audit remains in extraction.
    packet_claims = list({c['id']: c for c in packet_claims}.values())
    rng.shuffle(packet_claims)
    unit_type = q['source_unit_type']
    task = ('full_article' if 'article' in unit_type else
            'technical_documentation' if q['collection'] == 'code2doc' else
            'document_unit' if 'document' in unit_type else 'sentence_unit')
    return {'language': q['target_language'], 'unit_type': task, 'claims': packet_claims}, seed


def validate_writing(data, packet):
    if not isinstance(data, dict) or set(data) != set(WRITE_SCHEMA['properties']):
        raise ValueError('writing_structure')
    if not isinstance(data['text'], str) or not data['text'].strip():
        raise ValueError('empty_writing')
    expected = {c['id'] for c in packet['claims']}
    covered, unresolved = data['covered_claim_ids'], data['unresolved_claim_ids']
    if not isinstance(covered, list) or not isinstance(unresolved, list):
        raise ValueError('invalid_coverage_lists')
    combined = covered + unresolved
    if len(combined) != len(set(combined)) or set(combined) != expected:
        raise ValueError('writing_coverage_mismatch')
    if any(c in data['text'] for c in expected):
        raise ValueError('claim_id_leaked_into_prose')


def diagnostics(source, text, packet, extraction, writing):
    # These checks are review hints, never a semantic fidelity verdict.
    number = r'(?<![\w])\d+(?:[.,]\d+)*(?:%)?'
    a, b = set(re.findall(number, source)), set(re.findall(number, text))
    ratio = len(text) / max(1, len(source))
    flags = []
    if a - b:
        flags.append('literal_numbers_missing_or_reformatted')
    if b - a:
        flags.append('literal_numbers_added_or_reformatted')
    if ratio < 0.4:
        flags.append('substantial_compression_check_omissions')
    if ratio > 2:
        flags.append('substantial_expansion_check_additions')
    if writing['unresolved_claim_ids'] or writing['issues']:
        flags.append('writer_reported_unresolved_or_issues')
    return {'status': 'unreviewed_candidate', 'semantic_fidelity': 'not_independently_verified',
            'coverage': 'model_self_report_plus_structural_checks_only',
            'source_chars': len(source), 'rewrite_chars': len(text),
            'length_ratio': round(ratio, 3), 'claims': len(packet['claims']),
            'excluded_units': extraction['excluded_units'],
            'literal_numbers_missing_or_reformatted': sorted(a - b),
            'literal_numbers_added_or_reformatted': sorted(b - a), 'flags': flags}


def make_pair(q, output, extraction, packet, meta, qa, relative_dir):
    original = q['source_record']
    full = packet['unit_type'] == 'full_article'
    collection = 'ai-enrichment-articles' if full else 'ai-enrichment-units'
    title = original.get('title') or q['source_id']
    return {
        'id': VERSION + ':' + digest(q['queue_id'])[:24],
        'collection': collection,
        'collection_title': ('AI 补全 · 整篇文章 · Gemini 2.5 Flash Lite' if full else
                             'AI 补全 · 数据集与技术片段 · Gemini 2.5 Flash Lite'),
        'family': 'rewrite-experiment', 'language': q['target_language'],
        'pair_type': 'rewrite', 'title': title,
        'left': {'label': q['selected_source_label'] + ' · ' + q['collection'],
                 'text': q['selected_source_text'], 'role': q['selected_source_role']},
        'right': {'label': 'AI rewrite · Gemini 2.5 Flash Lite · 待人评',
                  'text': output['text'], 'role': 'ai-rewrite-unreviewed'},
        'alternatives': [],
        'context': '同语言重写；全文/原始记录抽取 SVO → 乱序内容包 → 独立成文。'
                   '原文角色与质量沿用来源标注，不代表已经验证 human gold。',
        'provenance': {**original.get('provenance', {}),
                       'source_record_id': q['source_id'],
                       'local_path': relative_dir + '/pairs.jsonl',
                       'original_local_path': original.get('provenance', {}).get('local_path'),
                       'notes': 'Generated candidate only; original split and source rights retained. '
                                'No independent human fidelity/style rating yet.'},
        'extra': {'generation': meta, 'qa': qa, 'source_collection': q['collection'],
                  'writer_evidence': meta.get('writer_evidence'),
                  'normalization_warnings': meta.get('normalization_warnings', []),
                  'source_unit_type': q['source_unit_type'], 'source_selected_side': q['selected_source_side'],
                  'source_sha256': q['selected_source_sha256'],
                  'source_authorship_status': q['authorship_status'],
                  'source_quality_notes': q['quality_notes'],
                  'source_record_content_hash': original.get('content_hash'),
                  'optional_existing_pair_comparison': q['optional'],
                  'semantic_packet': packet, 'writer_coverage': {k: v for k, v in output.items() if k != 'text'}}}


def wait_gate(path, timeout=3600):
    started = time.monotonic()
    while not path.exists():
        if time.monotonic() - started > timeout:
            raise TimeoutError('Run gate timed out')
        time.sleep(1)


def run(args):
    rows = [json.loads(line) for line in args.queue.read_text().splitlines() if line.strip()]
    if args.skip_japanese:
        rows = [r for r in rows if r['target_language'] != 'ja']
    if args.workers < 1:
        raise ValueError('workers_must_be_positive')
    if len({q['queue_id'] for q in rows}) != len(rows):
        raise ValueError('duplicate_queue_ids')
    if any(digest(q['selected_source_text']) != q['selected_source_sha256'] for q in rows):
        raise ValueError('source_hash_mismatch')
    prompts = {name: (SCRIPT_ROOT / 'prompts' / f'enrichment-{name}-v3.txt').read_text()
               for name in ('extract', 'write')}
    args.output.mkdir(parents=True, exist_ok=True)
    config = {'version': VERSION, 'model': 'google/gemini-2.5-flash-lite',
              'queue_sha256': hashlib.sha256(args.queue.read_bytes()).hexdigest(),
              'records': len(rows), 'budget_usd': args.budget, 'max_calls': args.max_calls,
              'workers': args.workers, 'generation_is_gold': False,
              'skip_japanese': args.skip_japanese,
              'prompt_sha256': {k: digest(v) for k, v in prompts.items()}}
    config_path = args.output / 'config.json'
    if config_path.exists():
        prior_config = json.loads(config_path.read_text())
        # Concurrency may change on resume; all data, prompts and spend limits
        # must remain identical so an old pair cannot stand in for new input.
        if any(prior_config.get(k) != v for k, v in config.items() if k != 'workers'):
            raise ValueError('resume_configuration_mismatch')
    else:
        if any(args.output.iterdir()):
            raise ValueError('nonempty_output_without_config')
        dump(config_path, config)
    for name, text in prompts.items():
        (args.output / f'prompt-{name}.txt').write_text(text)
    key = receive_key() if args.browser_key else os.environ.get('OPENROUTER_API_KEY', '')
    client = BudgetClient(api_key=key, ledger_path=args.output / 'budget-ledger.json',
                          budget_usd=args.budget, max_calls=args.max_calls, timeout=300)
    key = None
    dump(args.output / 'preflight.json', client.preflight(force=True))
    if args.wait_start:
        print('WAITING_START_GATE', flush=True)
        wait_gate(args.output / 'START')
    lock = threading.Lock()
    stop_scheduling = threading.Event()
    completed = []
    failures_path = args.output / 'failures.json'
    failures = json.loads(failures_path.read_text()) if failures_path.exists() else []
    if failures:
        history_path = args.output / 'failure-history.json'
        history = json.loads(history_path.read_text()) if history_path.exists() else []
        history.append({'saved_at_unix': int(time.time()), 'failures': failures})
        dump(history_path, history)
    if (args.output / 'pairs.jsonl').exists():
        completed = [json.loads(x) for x in (args.output / 'pairs.jsonl').read_text().splitlines() if x]
    done_ids = {p['id'] for p in completed}
    todo = [q for q in rows if VERSION + ':' + digest(q['queue_id'])[:24] not in done_ids]

    def one(q):
        item_dir = args.output / 'items' / digest(q['queue_id'])[:24]
        item_dir.mkdir(parents=True, exist_ok=True)
        state_path = item_dir / 'state.json'
        saved_extracted = saved_written = None
        if state_path.exists():
            # Recover a fully generated candidate after interruption without
            # sending either stage again. Any other previous attempt is held.
            pair_path = item_dir / 'pair.json'
            if pair_path.exists():
                pair = json.loads(pair_path.read_text())
                if (pair['id'] != VERSION + ':' + digest(q['queue_id'])[:24]
                        or pair['extra']['source_sha256'] != q['selected_source_sha256']):
                    raise ValueError('saved_pair_identity_mismatch')
                with lock:
                    with (args.output / 'pairs.jsonl').open('a', encoding='utf-8') as f:
                        f.write(canonical(pair) + '\n')
                        f.flush()
                        os.fsync(f.fileno())
                    completed.append(pair)
                dump(state_path, {'status': 'complete', 'source_id': q['source_id'],
                                  'pair_id': pair['id'], 'recovered_without_api_calls': True})
                return {'source_id': q['source_id'], 'status': 'recovered'}
            if not getattr(args, 'resume_saved_stages', False):
                return {'source_id': q['source_id'], 'status': 'skipped_previous_attempt'}
            saved_extracted = load_saved_stage(item_dir, 'extraction', args.output / 'budget-ledger.json')
            saved_written = load_saved_stage(item_dir, 'writing', args.output / 'budget-ledger.json')
            if saved_extracted is None:
                return {'source_id': q['source_id'], 'status': 'skipped_unsettled_or_missing_extraction'}
            # A packet is persisted before any writer call. If an earlier writer
            # attempt lacks an accepted saved response, never submit it again.
            if (item_dir / 'writer-packet.json').exists() and saved_written is None:
                return {'source_id': q['source_id'], 'status': 'skipped_previous_writer_attempt'}
        try:
            normalization_warnings = []
            source = q['selected_source_text']
            if digest(source) != q['selected_source_sha256']:
                raise ValueError('source_hash_mismatch')
            source_units = units(source)
            dump(state_path, {'status': 'extracting', 'source_id': q['source_id']})
            dump(item_dir / 'source.json', {k: v for k, v in q.items() if k != 'source_record'})
            dump(item_dir / 'source-units.json', source_units)
            # Generous output space for complete semantic inventories. Hard cap is
            # checked and reserved before inference, not after money is spent.
            extract_cap = min(60000, max(4096, len(source.encode()) * 2))
            extracted = saved_extracted or client.chat(messages=[{'role': 'system', 'content': prompts['extract']},
                {'role': 'user', 'content': canonical({'language': q['target_language'], 'source_units': source_units})}],
                max_tokens=extract_cap, json_schema=extraction_schema(source_units),
                schema_name='semantic_inventory', temperature=0.2)
            dump(item_dir / 'extraction-raw.json', extracted.parsed)
            dump(item_dir / 'extraction-call.json', extracted.metadata)
            inventory = normalize_extraction(extracted.parsed, source_units, normalization_warnings)
            dump(item_dir / 'extraction.json', inventory)
            validate_extraction(inventory, source_units)
            packet, seed = packet_for(inventory, q)
            dump(item_dir / 'writer-packet.json', packet)
            dump(item_dir / 'packet-audit.json', {'seed': seed,
                  'packet_sha256': digest(canonical(packet)), 'claims': len(packet['claims']),
                  'source_locators_removed': True, 'original_prose_sent_to_writer': False})
            dump(state_path, {'status': 'writing', 'source_id': q['source_id']})
            write_cap = min(60000, max(4096, len(canonical(packet).encode())))
            written = saved_written or client.chat(messages=[{'role': 'system', 'content': prompts['write']},
                {'role': 'user', 'content': canonical(packet)}], max_tokens=write_cap,
                json_schema=writing_schema(packet), schema_name='fresh_writing', temperature=0.8)
            dump(item_dir / 'writing-raw.json', written.parsed)
            dump(item_dir / 'writing-call.json', written.metadata)
            writing = normalize_writing(written.parsed, packet, normalization_warnings)
            dump(item_dir / 'writing.json', writing)
            validate_writing(writing, packet)
            qa = diagnostics(source, writing['text'], packet, inventory, writing)
            qa['normalization_warnings'] = normalization_warnings
            if normalization_warnings:
                qa['flags'].append('normalization_warnings_require_human_review')
            dump(item_dir / 'qa.json', qa)
            (item_dir / 'rewrite.md').write_text(writing['text'] + '\n')
            meta = {'prompt_version': VERSION, 'model': client.summary()['model'],
                    'writer_evidence': written.parsed.get('coverage'),
                    'normalization_warnings': normalization_warnings,
                    'reused_saved_stages': {'extraction': saved_extracted is not None,
                                           'writing': saved_written is not None},
                    'extraction': extracted.metadata, 'writing': written.metadata,
                    'prompt_sha256': {k: digest(v) for k, v in prompts.items()},
                    'cost_usd': str(__import__('decimal').Decimal(extracted.metadata['cost_usd']) +
                                    __import__('decimal').Decimal(written.metadata['cost_usd'])),
                    'generated_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
            pair = make_pair(q, writing, inventory, packet, meta, qa,
                             'ai-enrichment/' + args.output.name)
            dump(item_dir / 'pair.json', pair)
            with lock:
                with (args.output / 'pairs.jsonl').open('a', encoding='utf-8') as f:
                    f.write(canonical(pair) + '\n')
                    f.flush()
                    os.fsync(f.fileno())
                completed.append(pair)
                failures[:] = [f for f in failures if f['source_id'] != q['source_id']]
                dump(failures_path, failures)
            dump(state_path, {'status': 'complete', 'source_id': q['source_id'],
                              'pair_id': pair['id'], 'cost_usd': meta['cost_usd']})
            return {'source_id': q['source_id'], 'status': 'complete', 'qa': qa}
        except Exception as exc:
            # Static client messages and validation labels only; no upstream
            # response body, user data, or credentials in console/failure reports.
            reason = str(exc) if isinstance(exc, (BudgetError, ValueError)) else type(exc).__name__
            if isinstance(exc, BudgetError):
                stop_scheduling.set()
            status = {'status': 'failed', 'source_id': q['source_id'], 'reason': reason}
            dump(state_path, status)
            with lock:
                failures.append(status)
                dump(args.output / 'failures.json', failures)
            return status

    def phase(items, name):
        results = []
        iterator = iter(items)
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
            active = {}
            def schedule():
                if stop_scheduling.is_set() or client.summary()['halted']:
                    return False
                q = next(iterator, None)
                if q is None:
                    return False
                active[pool.submit(one, q)] = q
                return True
            for _ in range(args.workers):
                schedule()
            while active:
                ready, _ = concurrent.futures.wait(active, return_when=concurrent.futures.FIRST_COMPLETED)
                for future in ready:
                    active.pop(future)
                    results.append(future.result())
                    if len(results) % 20 == 0 or name == 'pilot':
                        print(canonical({'phase': name, 'processed': len(results),
                                         'complete_total': len(completed), 'failures': len(failures),
                                         'budget': client.summary()}), flush=True)
                    schedule()
        return results

    # Pilot spans bilingual whole articles plus short technical/human units.
    pilot = []
    predicates = [lambda q: q['collection'] == 'rewrite-article-v2' and q['target_language'] == 'zh',
                  lambda q: q['collection'] == 'coggen-owid',
                  lambda q: q['collection'] == 'freshwiki',
                  lambda q: q['collection'] == 'code2doc',
                  lambda q: q['collection'] == 'mcts-references',
                  lambda q: q['collection'] == 'iterater-human-doc']
    for predicate in predicates:
        candidates = sorted((q for q in todo if predicate(q)), key=lambda q: q['selected_source_chars'])
        if candidates:
            pilot.append(candidates[0])
    pilot_results = phase(pilot, 'pilot')
    dump(args.output / 'pilot-ready.json', {'results': pilot_results, 'budget': client.summary()})
    if args.pause_after_pilot and not client.summary()['halted']:
        print('PILOT_READY_WAITING_CONTINUE_GATE', flush=True)
        wait_gate(args.output / 'CONTINUE')
    pilot_ids = {q['queue_id'] for q in pilot}
    phase([q for q in todo if q['queue_id'] not in pilot_ids], 'batch')
    from collections import Counter
    summary = {'config': config, 'complete_pairs': len(completed), 'failures': failures,
               'language_counts': dict(Counter(p['language'] for p in completed)),
               'collection_counts': dict(Counter(p['collection'] for p in completed)),
               'source_counts': dict(Counter(p['extra']['source_collection'] for p in completed)),
               'budget': client.summary(), 'human_review': 'pending'}
    dump(args.output / 'run-summary.json', summary)
    print(canonical(summary), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--queue', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--budget', default='20')
    parser.add_argument('--max-calls', type=int, default=2200)
    parser.add_argument('--workers', type=int, default=6)
    parser.add_argument('--browser-key', action='store_true')
    parser.add_argument('--wait-start', action='store_true')
    parser.add_argument('--pause-after-pilot', action='store_true')
    parser.add_argument('--skip-japanese', action='store_true')
    parser.add_argument('--resume-saved-stages', action='store_true',
                        help='Reuse only accepted, settled saved responses; never retry uncertain calls')
    run(parser.parse_args())

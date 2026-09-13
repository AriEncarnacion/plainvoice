#!/usr/bin/env python3
"""Build a reversible text-cleaning derivative; never modify the input database.

All normalized records/references survive in the archive. Rewrite candidates are
unreviewed examples, not preference labels or human-authorship ground truth.
Exact source-specific removals and defect evidence are local-only sidecars.
"""
import argparse
from collections import Counter, defaultdict
from functools import lru_cache
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import time
import zlib

from plainvoice_text_cleaning import VERSION, clean_text


def packed(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode()


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def file_sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def read_json(path, fallback):
    return json.loads(path.read_text()) if path else fallback


def fields(record):
    yield 'left', record['left']
    if record.get('right') is not None:
        yield 'right', record['right']
    for i, side in enumerate(record.get('alternatives', [])):
        yield f'alternatives[{i}]', side


@lru_cache(maxsize=12000)
def normalized(text, title, source_url, collection, unit):
    return clean_text(text, title=title, source_url=source_url,
                      source_collection=collection, source_unit_type=unit)


def transform(record, removals, defects, review_warnings, rules_hash):
    raw_hash = record.pop('content_hash')
    extra = record.setdefault('extra', {})
    source = extra.get('source_collection') or record['collection']
    url = record.get('provenance', {}).get('source_url', '')
    url = url if isinstance(url, str) else ''
    unit = extra.get('source_unit_type', '')
    if record['collection'] == 'rewrite-article-v2':
        unit = 'article'
    audits = {}
    raw_side_hashes = {}
    actions = Counter()
    warnings = set()
    changed_sides = 0
    for name, side in fields(record):
        original = side['text']
        text = original
        h = sha(original)
        raw_side_hashes[name] = h
        scoped = removals.get(h, {})
        edits = []
        if scoped and record['id'] in scoped['record_ids'] and name == scoped['side']:
            for span in scoped['remove_spans']:
                assert text.count(span['text']) == 1, (record['id'], name, 'scoped span mismatch')
                text = text.replace(span['text'], '')
                edits.append({'reason': 'scoped_web_metadata', **span})
            actions['scoped_web_metadata'] += len(edits)
        result = normalized(text, record['title'], url, source, unit)
        side['text'] = result['text']
        actions.update(result['actions'])
        side_warnings = list(result['warnings'])
        if '[MATH]' in text or '[CITATION]' in text:
            side_warnings.append('source_math_or_citation_placeholders')
        if original.strip() and not side['text'].strip():
            side_warnings.append('nonempty_source_became_empty')
        changed = side['text'] != original
        changed_sides += changed
        if changed:
            again = normalized(side['text'], record['title'], url, source, unit)['text']
            assert again == side['text'], (record['id'], name, 'cleaner is not idempotent')
        warnings.update(side_warnings)
        if changed or side_warnings or result['protected']:
            audits[name] = {'raw_sha256': h, 'clean_sha256': sha(side['text']),
                            'raw_chars': len(original), 'clean_chars': len(side['text']),
                            'actions': result['actions'], 'removed': edits + result['removed'],
                            'warnings': side_warnings, 'protected': result['protected']}
    generated = record['family'] == 'rewrite-experiment' and record.get('right') is not None
    reasons = []
    scoped_defect = defects.get(record['id'])
    if scoped_defect:
        assert scoped_defect['record_content_hash'] == raw_hash, 'stale defect hash'
        for flag in scoped_defect['flags']:
            if flag['kind'] != 'paraphrased_site_boilerplate':
                reasons.append(flag['kind'])
    mixed = review_warnings.get(record['id'])
    if mixed:
        assert raw_side_hashes[mixed['side']] == mixed['sha256'], 'stale review warning'
        reasons.append('metadata_mixed_with_substantive_sentence')
    # Existing independent semantic checks are scoped to each generated record.
    qa = extra.get('qa', {})
    if isinstance(qa, dict):
        if qa.get('semantic_defect_flags') or qa.get('requires_semantic_review'):
            reasons.append('existing_semantic_review_flag')
        # Enrichment v1-v3 stores these diagnostics under qa.flags, with an
        # independent review status in qa and the scoped evidence in extra.
        # Number-format differences are review requirements, not established
        # factual errors, but must not silently pass the candidate gate.
        for flag in qa.get('flags', []):
            if isinstance(flag, str):
                reasons.append('existing_qa:' + flag)
        if qa.get('normalization_warnings'):
            reasons.append('existing_normalization_requires_review')
        if qa.get('independent_agent_review') == 'material_errors_found':
            reasons.append('existing_independent_fidelity_issues')
        mechanical = qa.get('mechanical', {})
        if isinstance(mechanical, dict) and any(mechanical.get(key) for key in (
                'missing_claim_ids', 'unknown_claim_ids', 'duplicate_claim_ids',
                'unresolved_claim_ids', 'writer_issues', 'empty_coverage_locations')):
            reasons.append('existing_article_mechanical_review_required')
    independent = extra.get('independent_agent_review')
    if isinstance(independent, dict) and independent.get('status') == 'material_errors_found':
        applies = independent.get('applies_to', {})
        if applies.get('pair_id'):
            assert applies['pair_id'] == record['id'], 'stale independent-review record scope'
        # Validate against the raw side hash: cleaning changes formatting, not
        # the scope of already recorded fidelity findings.
        expected = applies.get('pair_right_text_sha256') or applies.get('writer_text_sha256')
        if expected:
            actual = raw_side_hashes.get('right')
            assert actual == expected, 'stale independent-review text scope'
        reasons.append('existing_independent_fidelity_issues')
    if generated:
        a, b = record['left']['text'], record['right']['text']
        if not a.strip() or not b.strip():
            reasons.append('empty_rewrite_side')
        if a == b:
            reasons.append('identical_text_no_style_contrast')
        if len(a) > 1000 and len(b) / max(1, len(a)) < .2:
            reasons.append('extreme_compression_review_required')
        for w in warnings:
            if w not in {'image_removed_review_surrounding_references'}:
                reasons.append(w)
    state = 'quarantined' if generated and reasons else 'review_candidate' if generated else 'archive_only'
    status = {'status': state, 'reasons': sorted(set(reasons)), 'human_review': 'unreviewed',
              'semantic_equivalence': 'not_certified', 'authorship': 'see_original_provenance'}
    extra['cleaning'] = {'version': VERSION, 'rules_sha256': rules_hash,
                         'raw_content_hash': raw_hash, 'changed_sides': changed_sides,
                         'actions': dict(actions), 'warnings': sorted(warnings), **status}
    record['content_hash'] = hashlib.sha256(packed(record)).hexdigest()
    audit = {'id': record['id'], 'raw_content_hash': raw_hash,
             'clean_content_hash': record['content_hash'], 'fields': audits,
             'scoped_defects': scoped_defect, 'mixed_metadata_review': mixed}
    return record, audit, status, changed_sides, actions, warnings


def build(a):
    assert a.database.resolve() != (a.output / 'review.sqlite').resolve()
    if a.output.exists():
        raise SystemExit('Output already exists; choose a new version directory.')
    temp = a.output.with_name(a.output.name + '.building')
    if temp.exists():
        raise SystemExit('Staging directory exists; inspect it before retrying.')
    temp.mkdir(parents=True)
    (temp / 'text-only').mkdir()
    (temp / 'qa').mkdir()
    raw_before = file_sha(a.database)
    removals = read_json(a.removals, {})
    defects = {x['record_id']: x for x in read_json(a.defects, {'records': []})['records']}
    reviews = {x['id']: x for x in read_json(a.warnings, [])}
    rules_hash = hashlib.sha256(packed({'version': VERSION,
        'code': file_sha(Path(__file__).with_name('plainvoice_text_cleaning.py')),
        'pipeline': file_sha(Path(__file__)), 'removals': removals, 'defects': defects,
        'warnings': reviews})).hexdigest()
    for name, path in [('scoped-removals.json', a.removals), ('scoped-defects.json', a.defects), ('review-warnings.json', a.warnings)]:
        if path:
            shutil.copyfile(path, temp / 'qa' / name)
    raw = sqlite3.connect(a.database.resolve().as_uri() + '?mode=ro', uri=True)
    # Fail closed on stale source-specific rules, including scopes whose hash
    # would otherwise simply stop matching and silently leave metadata behind.
    def source_record(identifier):
        found = raw.execute('SELECT payload FROM records WHERE id=?', (identifier,)).fetchone()
        assert found, ('missing scoped record', identifier)
        return json.loads(zlib.decompress(found[0]))
    for expected, scope in removals.items():
        for identifier in scope['record_ids']:
            side = dict(fields(source_record(identifier)))[scope['side']]
            assert sha(side['text']) == expected, ('stale removal scope', identifier)
    for identifier, defect in defects.items():
        source_row = source_record(identifier)
        assert source_row['content_hash'] == defect['record_content_hash'], ('stale defect', identifier)
        for side in ('left', 'right'):
            if defect.get(side + '_sha256'):
                assert sha(source_row[side]['text']) == defect[side + '_sha256']
    for identifier, warning in reviews.items():
        assert sha(dict(fields(source_record(identifier)))[warning['side']]['text']) == warning['sha256']
    db = sqlite3.connect(temp / 'review.sqlite')
    db.executescript('''PRAGMA journal_mode=OFF; PRAGMA synchronous=OFF;
    CREATE TABLE records(rid INTEGER PRIMARY KEY,id TEXT NOT NULL UNIQUE,collection TEXT,language TEXT,pair_type TEXT,family TEXT,title TEXT,hash TEXT,search_text TEXT,payload BLOB,quality_status TEXT);
    CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT);
    CREATE TABLE cleaning_audits(record_id TEXT PRIMARY KEY,payload BLOB);
    ''')
    catalog = json.loads(raw.execute("SELECT value FROM metadata WHERE key='catalog'").fetchone()[0])
    summary = Counter()
    collection_counts = defaultdict(Counter)
    actions = Counter()
    warning_counts = Counter()
    reason_counts = Counter()
    writers = {}
    candidates = gzip.open(temp / 'rewrite-candidates.jsonl.gz', 'wb', compresslevel=3)
    quarantine = gzip.open(temp / 'quarantined-rewrites.jsonl.gz', 'wb', compresslevel=3)
    manifests = gzip.open(temp / 'metadata.jsonl.gz', 'wb', compresslevel=3)
    started = time.time()
    for rid, blob in raw.execute('SELECT rid,payload FROM records ORDER BY rid'):
        record = json.loads(zlib.decompress(blob))
        record, audit, status, changed, acts, warns = transform(record, removals, defects, reviews, rules_hash)
        coll = record['collection']
        summary['records'] += 1
        summary['text_fields'] += sum(1 for _ in fields(record))
        summary['changed_records'] += bool(changed)
        summary['changed_text_fields'] += changed
        summary[status['status']] += 1
        collection_counts[coll]['records'] += 1
        collection_counts[coll]['changed_records'] += bool(changed)
        collection_counts[coll][status['status']] += 1
        actions.update(acts); warning_counts.update(warns); reason_counts.update(status['reasons'])
        search = '\n'.join([record['title']] + [s['text'] for _, s in fields(record)]).lower()
        db.execute('INSERT INTO records VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                   (rid, record['id'], coll, record['language'], record['pair_type'], record['family'],
                    record['title'], record['content_hash'], search, zlib.compress(packed(record), 1), status['status']))
        if audit['fields'] or audit['scoped_defects'] or audit['mixed_metadata_review']:
            db.execute('INSERT INTO cleaning_audits VALUES (?,?)', (record['id'], zlib.compress(packed(audit), 1)))
        minimal = {'id': record['id'], 'a': record['left']['text'],
                   'b': record['right']['text'] if record.get('right') is not None else None,
                   'references': [s['text'] for s in record.get('alternatives', [])]}
        if coll not in writers:
            assert re.fullmatch(r'[a-zA-Z0-9_.-]+', coll)
            writers[coll] = gzip.open(temp / 'text-only' / (coll + '.jsonl.gz'), 'wb', compresslevel=3)
        writers[coll].write(packed(minimal) + b'\n')
        manifests.write(packed({'id': record['id'], 'collection': coll, 'language': record['language'],
            'pair_type': record['pair_type'], 'roles': {n: s.get('role') for n, s in fields(record)},
            'raw_content_hash': audit['raw_content_hash'], 'clean_content_hash': record['content_hash'],
            'provenance': record.get('provenance'), 'eligibility': status}) + b'\n')
        if status['status'] != 'archive_only':
            target = candidates if status['status'] == 'review_candidate' else quarantine
            target.write(packed({'id': record['id'], 'source_text': minimal['a'], 'rewrite_text': minimal['b']}) + b'\n')
        if summary['records'] % 10000 == 0:
            db.commit()
        if summary['records'] % 100000 == 0:
            print(json.dumps({**summary, 'seconds': round(time.time() - started)}), flush=True)
    for f in [*writers.values(), candidates, quarantine, manifests]:
        f.close()
    assert summary['records'] == catalog['total_records']
    db.commit()
    print('Building cleaned search indexes…', flush=True)
    db.executescript('''CREATE INDEX collection_records ON records(collection,rid);
    CREATE INDEX type_records ON records(pair_type,rid);
    CREATE INDEX language_records ON records(language,rid);
    CREATE INDEX quality_records ON records(quality_status,rid);
    CREATE VIRTUAL TABLE search USING fts5(search_text,content='records',content_rowid='rid',tokenize='unicode61');
    INSERT INTO search(search) VALUES('rebuild');''')
    raw.close()
    assert file_sha(a.database) == raw_before, 'Raw database changed during cleaning'
    report = {'version': VERSION, 'rules_sha256': rules_hash, 'raw_database_sha256': raw_before,
              'counts': dict(summary), 'collections': dict(collection_counts), 'actions': dict(actions),
              'warnings': dict(warning_counts), 'quarantine_reasons': dict(reason_counts),
              'elapsed_seconds': round(time.time() - started),
              'qa': {'raw_unchanged': True, 'changed_fields_idempotent': True,
                     'all_records_and_references_preserved': True},
              'scope': 'Formatting-clean archive and unreviewed rewrite candidates; not training gold.'}
    catalog.update({'text_view': 'clean', 'cleaning': report})
    db.execute('INSERT INTO metadata VALUES (?,?)', ('catalog', json.dumps(catalog, ensure_ascii=False)))
    db.commit()
    assert db.execute('PRAGMA quick_check').fetchone()[0] == 'ok'
    db.close()
    (temp / 'summary.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    (temp / 'README.md').write_text('''# Clean text v1\n\nDefault viewer: http://127.0.0.1:8876/?view=clean\n\n- review.sqlite: complete cleaned archive, provenance, QA and reversible removal audits.\n- text-only/*.jsonl.gz: every collection, `id,a,b,references`; null is absent, empty may be an insertion/deletion. Feed only text fields to models.\n- rewrite-candidates.jsonl.gz: unreviewed source/AI candidates; no inferred preferred answer or verified human authorship.\n- quarantined-rewrites.jsonl.gz: known failures, semantic or format review requirements; inspect metadata.jsonl.gz for reasons.\n- metadata.jsonl.gz: per-ID roles, original/clean hashes, attribution, license and eligibility. Full generation/context metadata stays in SQLite.\n- qa/: exact local source-specific removals and defects.\n\nRaw corpus and previous review hashes remain unchanged. Cleaned reviews have distinct content hashes. Code, math, Javadoc, URLs used as technical content, and table syntax are preserved intentionally. Cleaning does not certify fidelity or authorship.\n''')
    os.replace(temp, a.output)
    print(json.dumps(report, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--database', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    p.add_argument('--removals', type=Path)
    p.add_argument('--defects', type=Path)
    p.add_argument('--warnings', type=Path)
    build(p.parse_args())

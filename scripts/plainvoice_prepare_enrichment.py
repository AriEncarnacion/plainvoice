#!/usr/bin/env python3
"""Prepare a reproducible, read-only Plainvoice enrichment queue.

Standard-library-only. Importing this module has no I/O side effects. Paths are
explicit arguments/default constants; the current directory is never assumed.
No database writes, network requests, or model calls are made.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import sqlite3
from typing import Any, Iterable
import zlib

DEFAULT_DB = Path(__file__).resolve().parents[1] / 'data/local/data-viewer/review.sqlite'
CLEAN_DB = DEFAULT_DB.parent.parent / 'clean-text-v1/review.sqlite'
DEFAULT_OUTPUT = Path('/private/tmp/plainvoice-enrichment-queue.jsonl')
SELECTION_VERSION = 'plainvoice-enrichment-queue-v3-clean-text'
SEED = 'plainvoice-2026-09-12-enrichment-1'
BAD_CODE = {
    'code2doc:test-7': 'Docstring describes jarmode inclusion setter; code writes native-image args.',
    'code2doc:test-13': 'License header only, not documentation prose.',
    'code2doc:test-14': 'Docstring describes cooperative assignment validation; code handles leaving group.',
    'code2doc:test-15': 'Docstring parameters belong to a different function than parseEntityName.',
    'code2doc:test-17': 'Docstring describes unmodifiableEntry, while code is unmodifiableEntryIterator.',
}


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def normalize(text: str) -> str:
    """Conservative deduplication: whitespace only, no case/punctuation edits."""
    return re.sub(r'\s+', ' ', text).strip()


def score(identifier: str) -> str:
    return sha256(SEED + '\0' + identifier)


def read_collection(connection: sqlite3.Connection, name: str) -> list[dict[str, Any]]:
    return [json.loads(zlib.decompress(blob)) for (blob,) in connection.execute(
        'SELECT payload FROM records WHERE collection=? ORDER BY id', (name,))]


def human_reference(record: dict[str, Any], min_chars: int) -> tuple[str, dict[str, Any]] | None:
    """Pick one explicit human reference, rotating its index deterministically."""
    refs = [('right', record.get('right') or {})] + [
        (f'alternatives[{i}]', value) for i, value in enumerate(record.get('alternatives') or [])]
    refs = [(side, value) for side, value in refs
            if value.get('role') == 'reference' and 'human' in value.get('label', '').lower()
            and len(value.get('text', '').strip()) >= min_chars]
    if not refs:
        return None
    refs.sort(key=lambda value: score(record['id'] + '\0' + value[0]))
    return refs[0]


class QueueBuilder:
    def __init__(self) -> None:
        self.rows: list[dict[str, Any]] = []
        self.used_selected: set[str] = set()
        self.used_original: set[str] = set()
        self.used_record_ids: set[str] = set()
        self.used_iterater_doc_ids: set[str] = set()
        self.rejections: Counter[str] = Counter()
        self.coverage: dict[str, Any] = {}

    def add(self, record: dict[str, Any], group: str, unit_type: str,
            selected_side: str = 'left', selected: dict[str, Any] | None = None,
            authorship: str = 'dataset-attributed-human; not independently verified',
            quality_notes: Iterable[str] = (), optional: bool = False,
            doc_unique: bool = False) -> bool:
        selected = selected if selected is not None else record.get(selected_side)
        if not selected or not selected.get('text', '').strip():
            self.rejections['empty_selected_text'] += 1
            return False
        cleaning_warnings = record.get('extra', {}).get('cleaning', {}).get('warnings', [])
        blocked_source_warnings = {
            'structured_json_preserved_not_prose',
            'source_latex_diff_markup_preserved_not_prose',
            'ascii_art_or_corrupted_markup_preserved_not_prose',
            'source_wiki_editing_markup_preserved_review_required',
            'source_formula_placeholders_preserved_review_required',
            'nonempty_source_became_empty',
        }
        if blocked_source_warnings.intersection(cleaning_warnings):
            self.rejections['source_capture_requires_repair'] += 1
            return False
        selected_text = selected['text']
        if selected_text.lstrip().startswith(('{', '[')):
            try:
                structured = json.loads(selected_text)
            except ValueError:
                pass
            else:
                if isinstance(structured, (dict, list)):
                    self.rejections['structured_data_not_prose'] += 1
                    return False
        selected_hash = sha256(normalize(selected_text))
        original_text = (record.get('left') or {}).get('text', '')
        original_hash = sha256(normalize(original_text))
        if record['id'] in self.used_record_ids:
            self.rejections['record_id_already_selected'] += 1
            return False
        if selected_hash in self.used_selected or selected_hash in self.used_original:
            self.rejections['selected_text_duplicate_across_queue'] += 1
            return False
        if original_hash in self.used_original or original_hash in self.used_selected:
            self.rejections['original_input_duplicate_across_queue'] += 1
            return False
        doc_id = str(record.get('extra', {}).get('doc_id', ''))
        if doc_unique and doc_id in self.used_iterater_doc_ids:
            self.rejections['iterater_document_already_selected'] += 1
            return False
        explicit_ai_role = selected.get('role', '').startswith('ai-')
        if explicit_ai_role:
            raise ValueError(f'Refusing AI output as human/source side: {record["id"]}')
        row = {
            'queue_version': SELECTION_VERSION,
            'queue_id': SELECTION_VERSION + ':' + sha256(record['id'] + '\0' + selected_side)[:24],
            'source_id': record['id'],
            'collection': record['collection'],
            'sampling_group': group,
            'source_unit_type': unit_type,
            'optional': optional,
            'same_language_rewrite': True,
            'source_language': record['language'],
            'target_language': record['language'],
            'selected_source_side': selected_side,
            'selected_source_role': selected.get('role'),
            'selected_source_label': selected.get('label'),
            'selected_source_text': selected_text,
            'selected_source_chars': len(selected_text),
            'selected_source_sha256': sha256(selected_text),
            'selected_source_normalized_sha256': selected_hash,
            'original_input_normalized_sha256': original_hash,
            'authorship_status': authorship,
            'existing_pair_type': record.get('pair_type'),
            'existing_right_role': (record.get('right') or {}).get('role'),
            'split': record.get('provenance', {}).get('split'),
            'license': record.get('provenance', {}).get('license'),
            'quality_notes': list(quality_notes) + [
                'Generated rewrite is an unreviewed candidate, not human gold.',
                'Preserve original split and source license; queue inclusion is not training or redistribution clearance.',
            ],
            'source_record': record,
            'source_cleaning_version': record.get('extra', {}).get('cleaning', {}).get('version'),
            'source_raw_content_hash': record.get('extra', {}).get('cleaning', {}).get('raw_content_hash'),
        }
        if cleaning_warnings:
            row['quality_notes'].append('Source cleaning review flags: ' + ', '.join(cleaning_warnings))
        if record['collection'] == 'coedit':
            row['original_edit_instruction'] = record.get('extra', {}).get('instruction')
            row['quality_notes'].append(
                'A plain rewrite of this input is a separate task from applying its original CoEdIT edit instruction; record which condition is used.')
        self.rows.append(row)
        self.used_selected.add(selected_hash)
        self.used_original.add(original_hash)
        self.used_record_ids.add(record['id'])
        if doc_unique:
            self.used_iterater_doc_ids.add(doc_id)
        return True

    def stratified_take(self, candidates: list[tuple[dict[str, Any], str, dict[str, Any]]],
                        quota: int, group: str, unit_type: str,
                        stratum_key, **kwargs: Any) -> int:
        buckets: dict[str, list[tuple[dict[str, Any], str, dict[str, Any]]]] = defaultdict(list)
        for item in candidates:
            buckets[str(stratum_key(item[0]))].append(item)
        for values in buckets.values():
            values.sort(key=lambda value: score(value[0]['id']))
        positions = Counter()
        chosen = 0
        while chosen < quota:
            progressed = False
            for key in sorted(buckets):
                values = buckets[key]
                while positions[key] < len(values):
                    record, side, selected = values[positions[key]]
                    positions[key] += 1
                    if self.add(record, group, unit_type, side, selected, **kwargs):
                        self.rows[-1]['sampling_stratum'] = key
                        chosen += 1
                        progressed = True
                        break
                if chosen == quota:
                    break
            if not progressed:
                break
        self.coverage[group] = {'eligible_rows_before_global_dedup': len(candidates),
                                'requested': quota, 'selected': chosen,
                                'eligible_by_stratum': {key: len(values) for key, values in sorted(buckets.items())}}
        return chosen


def prepare_queue(db_path: Path | str, include_japanese: bool = True) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    db_path = Path(db_path).expanduser().resolve()
    connection = sqlite3.connect(db_path.as_uri() + '?mode=ro', uri=True)
    connection.execute('PRAGMA query_only=ON')
    builder = QueueBuilder()
    try:
        total_records = connection.execute('SELECT COUNT(*) FROM records').fetchone()[0]
        for record in read_collection(connection, 'coggen-owid'):
            if record['left']['role'] == 'human-reference' and not record.get('right'):
                builder.add(record, 'mandatory-owid-articles', 'complete-downloaded-article',
                            quality_notes=['Human reference supplied by benchmark; original author attribution retained.'])
        for record in read_collection(connection, 'freshwiki'):
            builder.add(record, 'mandatory-freshwiki-articles', 'complete-downloaded-article',
                        authorship='community-reference; machine assistance cannot be ruled out',
                        quality_notes=['Complete downloaded section/sentence assembly; not a current live-page verification.'])
        for record in read_collection(connection, 'code2doc'):
            if record['id'] not in BAD_CODE:
                builder.add(record, 'mandatory-code2doc-snippets', 'function-documentation-snippet',
                            authorship='source-documentation-authorship-unverified',
                            quality_notes=['Short function documentation, not an article.',
                                           'Attached code retained for context; four obvious misalignments and one license-only record excluded.',
                                           'Code was not executed and all documentation claims have not been validated.'])
        for record in read_collection(connection, 'rewrite-article-v2'):
            builder.add(record, 'optional-existing-article-cheap-model-comparison', 'complete-cleaned-source-article',
                        authorship=record['left']['role'] + '; attribution is not a quality label', optional=True,
                        quality_notes=['Existing AI rewrite already present; this is a new model comparison, not filling an absent AI side.',
                                       'Two Chinese articles provide a same-language full-article comparison condition.'])

        iterater = read_collection(connection, 'iterater-human-doc')
        for domain, quota in [('arxiv', 90), ('news', 100), ('wiki', 100), ('unspecified', 10)]:
            candidates = [(record, 'right', record['right']) for record in iterater
                          if record.get('extra', {}).get('domain', 'unspecified') == domain
                          and record['left']['text'].strip() != record['right']['text'].strip()
                          and 200 <= len(record['right']['text'].strip()) <= 12000]
            builder.stratified_take(candidates, quota, 'iterater-human-doc-' + domain,
                'human-document-revision-unit', lambda record: record['provenance']['split'], doc_unique=True,
                quality_notes=['Select human-authored after-revision text; HUMAN describes annotation origin, not an AI role.',
                               'One record per doc_id across this queue. Abstracts, sections and collected revision units are not called complete articles.',
                               'Original before/after and edit annotations remain in source_record.'])

        for collection, quota, min_chars, group in [
            ('mcts-references', 400, 12, 'mcts-human-reference-sentences'),
            ('asset-references', 60, 25, 'asset-human-reference-sentences'),
        ]:
            candidates = []
            for record in read_collection(connection, collection):
                ref = human_reference(record, min_chars)
                if ref:
                    candidates.append((record, ref[0], ref[1]))
            builder.stratified_take(candidates, quota, group, 'human-reference-sentence',
                lambda record: record['provenance']['split'],
                authorship='explicit-human-reference label from dataset; not independently verified',
                quality_notes=['Selected text is one explicit human simplification reference, not a machine pseudo target.',
                               'Rewrite the selected human reference; its original pre-simplification input and other human references are context, not mandatory omitted facts to reinsert.',
                               'A sentence-level example is not an article. Reference choice is deterministic and rotates across released reference indices.'])

        arxiv_candidates = []
        for record in read_collection(connection, 'arxivedits-alignment'):
            left = record['left']['text']; right = record['right']['text']
            methods = record['extra'].get('alignment_methods', [])
            if (any(method.startswith('manual_alignment') for method in methods)
                    and normalize(left) != normalize(right)
                    and 100 <= len(right.strip()) <= 2500
                    and not re.search(r'\[(?:MATH|REF)\]', right)
                    and right.rstrip().endswith(('.', '?', '!'))):
                arxiv_candidates.append((record, 'right', record['right']))
        builder.stratified_take(arxiv_candidates, 60, 'arxiv-manual-revision-units',
            'scientific-sentence-revision-unit', lambda record: record['provenance']['split'],
            quality_notes=['Changed manual alignment; no unaligned orphan rows or auto-identical rows selected.',
                           'Select later human paper version as rewrite source. Scientific claim equivalence to the earlier version is not assumed.',
                           'Math/reference placeholders are filtered from selected target; citation placeholders may remain and must be preserved.'])

        coedit_candidates = []
        for record in read_collection(connection, 'coedit'):
            left = record['left']['text']; right = record['right']['text']
            if 80 <= len(left.strip()) <= 3000 and normalize(left) != normalize(right):
                coedit_candidates.append((record, 'left', record['left']))
        builder.stratified_take(coedit_candidates, 60, 'coedit-source-editing-units',
            'instruction-editing-source-unit', lambda record: record['extra']['task'],
            authorship='heterogeneous editing-source text; per-example human authorship not verified',
            quality_notes=['Select original input, not an unlabeled preferred/model output.',
                           'Generic input/target roles are insufficient to prove human authorship; uncertainty is retained.',
                           'Six original task families sampled equally, ten each; sentence/paragraph units are not articles.'])

        if include_japanese:
            main = read_collection(connection, 'adparaphrase-v2.0-main')
            preferences = read_collection(connection, 'adparaphrase-v2.0-preferences')
            ai_source_ids: set[str] = set(); ai_texts: set[str] = set()
            for record in main + preferences:
                extra = record['extra']
                is_main = record['collection'].endswith('main')
                has_ai = extra['source_ad2'] != 'human' if is_main else any(
                    extra[key] != 'human' for key in ('model_ad1', 'model_ad2'))
                if has_ai:
                    ai_source_ids.add(extra['source_ad1'] if is_main else extra['source_input_ad'])
                    ai_texts.add(normalize(record['left']['text']))
            candidates = [(record, 'right', record['right']) for record in main
                          if record['extra']['source_ad2'] == 'human'
                          and record['extra']['source_ad1'] not in ai_source_ids
                          and normalize(record['left']['text']) not in ai_texts
                          and record['extra'].get('majority_equivalent')
                          and len(record['right']['text'].strip()) >= 8]
            builder.stratified_take(candidates, 8, 'optional-japanese-human-ad-references',
                'human-ad-copy-reference', lambda record: record['extra']['count.paraphrase'], optional=True,
                authorship='explicit crowdworker model_ad/source_ad label in original dataset',
                quality_notes=['Source is the crowdworker candidate; camera input had no AI counterpart in either downloaded view.',
                               'This is an optional Japanese same-language rewrite condition; do not translate into English or Chinese.'])

        group_counts = Counter(row['sampling_group'] for row in builder.rows)
        expected = {'mandatory-owid-articles': 19, 'mandatory-freshwiki-articles': 10,
                    'mandatory-code2doc-snippets': 15, 'optional-existing-article-cheap-model-comparison': 6}
        for group, expected_count in expected.items():
            if group_counts[group] != expected_count:
                raise RuntimeError(f'{group}: expected {expected_count}, got {group_counts[group]}')
        for index, row in enumerate(builder.rows, 1):
            row['queue_index'] = index
        summary = {
            'queue_version': SELECTION_VERSION, 'selection_seed': SEED, 'database': str(db_path),
            'database_record_count': total_records, 'read_only_database': True,
            'record_count': len(builder.rows),
            'queue_counts_by_group': dict(sorted(group_counts.items())),
            'queue_counts_by_language': dict(Counter(row['source_language'] for row in builder.rows)),
            'queue_counts_by_collection': dict(Counter(row['collection'] for row in builder.rows)),
            'queue_counts_by_selected_role': dict(Counter(row['selected_source_role'] for row in builder.rows)),
            'selected_counts_by_group_and_split': [
                {'group': key[0], 'split': key[1], 'count': count}
                for key, count in sorted(Counter((row['sampling_group'], row['split'])
                    for row in builder.rows).items(), key=lambda item: str(item[0]))],
            'queue_counts_by_unit_type': dict(Counter(row['source_unit_type'] for row in builder.rows)),
            'queue_counts_by_selected_side': dict(Counter(row['selected_source_side'] for row in builder.rows)),
            'selected_source_characters': sum(row['selected_source_chars'] for row in builder.rows),
            'optional_record_count': sum(row['optional'] for row in builder.rows),
            'selection_coverage': builder.coverage,
            'excluded_code2doc_records': BAD_CODE,
            'deduplication_rejections': dict(builder.rejections),
            'qa': {'distinct_source_ids': len(builder.used_record_ids),
                   'distinct_normalized_selected_texts': len(builder.used_selected),
                   'distinct_normalized_original_inputs': len(builder.used_original),
                   'distinct_iterater_document_ids': len(builder.used_iterater_doc_ids),
                   'explicit_AI_sources': sum(row['selected_source_role'].startswith('ai-') for row in builder.rows),
                   'all_target_languages_equal_source': all(row['source_language'] == row['target_language'] for row in builder.rows),
                   'pseudo_or_unaligned_collections_selected': sorted({row['collection'] for row in builder.rows
                       if row['collection'] in {'mcts-pseudo', 'arxivedits-unaligned'}})},
            'caveats': ['This queue is an unreviewed evaluation/pilot selection, not an independent or randomly representative benchmark.',
                        'EN and ZH both receive priority; no additional complete Chinese human-only articles exist in the bounded collections. Two existing Chinese article sources are optional new-model comparisons.',
                        'CoEdIT, community sources and one existing Stripe article preserve authorship uncertainty. No human-gold claim is made.',
                        'Sentence/paragraph and document-revision units retain those labels. Full articles refer only to the bounded article source groups.',
                        'Character counts are Unicode code points, not billable tokens.',
                        'No source text is truncated. source_record preserves original sides, references, license and provenance.'],
        }
        return builder.rows, summary
    finally:
        connection.close()


def write_outputs(rows: list[dict[str, Any]], summary: dict[str, Any], output_path: Path,
                  manifest_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open('w', encoding='utf-8') as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n')
    summary['queue_file'] = str(output_path.resolve())
    summary['queue_file_sha256'] = hashlib.sha256(output_path.read_bytes()).hexdigest()
    with manifest_path.open('w', encoding='utf-8') as stream:
        json.dump(summary, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write('\n')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', type=Path, help='Defaults to cleaned archive when available, otherwise raw. Explicit path reproduces that input version.')
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--manifest', type=Path)
    parser.add_argument('--exclude-japanese', action='store_true')
    args = parser.parse_args(argv)
    selected_db = args.db or (CLEAN_DB if CLEAN_DB.is_file() else DEFAULT_DB)
    rows, summary = prepare_queue(selected_db, include_japanese=not args.exclude_japanese)
    output = args.output.expanduser().resolve()
    manifest = args.manifest.expanduser().resolve() if args.manifest else output.with_suffix('.manifest.json')
    write_outputs(rows, summary, output, manifest)
    print(json.dumps({key: summary[key] for key in ('record_count', 'queue_counts_by_group',
        'queue_counts_by_language', 'selected_source_characters', 'optional_record_count', 'qa')},
        ensure_ascii=False, indent=2))
    print('Queue:', output)
    print('Manifest:', manifest)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

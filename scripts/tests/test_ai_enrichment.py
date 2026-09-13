import argparse
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import run_ai_enrichment as m

class FakeClient:
    calls = []
    instances = []
    mode = 'ok'
    lock = threading.Lock()
    def __init__(self, **kw):
        self.count = 0
        self.instances.append(self)
        self.ledger_path = Path(kw['ledger_path'])
        if not self.ledger_path.exists():
            self.ledger_path.write_text(json.dumps({'model': 'google/gemini-2.5-flash-lite', 'entries': []}))
    def preflight(self, *, force=False):
        return {'model': 'google/gemini-2.5-flash-lite', 'forced': force}
    def summary(self):
        return {'model': 'google/gemini-2.5-flash-lite', 'halted': False,
                'calls': self.count, 'spent_usd': str(self.count * .0001)}
    def chat(self, **kw):
        self.calls.append(kw)
        self.count += 1
        user = json.loads(kw['messages'][-1]['content'])
        if kw['schema_name'] == 'semantic_inventory':
            data = {'by_unit': [{'unit_id': u['unit'], 'claims': [{'subject': 'Subject', 'predicate': 'states', 'object': u['text'],
                'qualifiers': [], 'attribution': None}], 'excluded_reason': None, 'unresolved': False}
                for u in user['source_units']]}
        else:
            data = {'text': '\n\n'.join(c['object'] for c in user['claims']),
                'coverage': [{'claim_id': c['id'], 'status': 'covered', 'evidence': [c['object']]} for c in user['claims']], 'issues': []}
        if self.mode == 'missing_unit' and kw['schema_name'] == 'semantic_inventory':
            data['by_unit'].pop()
        if self.mode == 'unknown_coverage' and kw['schema_name'] == 'fresh_writing':
            data['coverage'][0]['status'] = 'maybe'
        with self.lock:
            ledger = json.loads(self.ledger_path.read_text())
            sequence = len(ledger['entries']) + 1
            metadata = {'cost_usd': '0.0001', 'model': 'google/gemini-2.5-flash-lite',
                        'ledger_id': 'fixture-' + str(sequence), 'generation_id': 'gen-fixture-' + str(sequence)}
            ledger['entries'].append({'id': metadata['ledger_id'], 'state': 'settled', 'outcome': 'accepted',
                                      'actual_usd': '0.0001', 'metadata': metadata})
            self.ledger_path.write_text(json.dumps(ledger))
        return SimpleNamespace(parsed=data, metadata=metadata)

class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / 'prompts').mkdir()
        for stage in ('extract', 'write'):
            (self.root / 'prompts' / f'enrichment-{stage}-v3.txt').write_text('fixture ' + stage)
        self.args = argparse.Namespace(queue=self.root / 'queue.jsonl', output=self.root / 'run',
            budget='10', max_calls=2200, workers=3, browser_key=True,
            wait_start=False, pause_after_pilot=False, skip_japanese=True, resume_saved_stages=False)
        FakeClient.calls = []
        FakeClient.instances = []
        FakeClient.mode = 'ok'
    def tearDown(self):
        self.tmp.cleanup()
    def row(self, i, collection, unit, lang='en'):
        text = '# Test heading\n\nArticle has 123 items.\n\nKeep all content.'
        return {'queue_id': 'queue-' + str(i), 'source_id': 'source-' + str(i), 'collection': collection,
            'source_unit_type': unit, 'target_language': lang, 'selected_source_text': text,
            'selected_source_sha256': m.digest(text), 'selected_source_chars': len(text),
            'source_record': {'title': 'Example ' + str(i), 'provenance': {'local_path': 'source.jsonl'}},
            'selected_source_label': 'Original', 'selected_source_role': 'human', 'selected_source_side': 'left',
            'authorship_status': 'as-labeled', 'quality_notes': [], 'optional': {}}
    def execute(self, rows):
        self.args.queue.write_text(''.join(json.dumps(q) + '\n' for q in rows))
        with patch.object(m, 'BudgetClient', FakeClient), patch.object(m, 'receive_key', return_value='fake-offline'), patch.object(m, 'SCRIPT_ROOT', self.root), contextlib.redirect_stdout(io.StringIO()):
            m.run(self.args)
    def test_pilot_batch_artifacts_and_resume_without_calls(self):
        rows = [self.row(1, 'rewrite-article-v2', 'existing-complete-article', 'zh'),
                self.row(2, 'coggen-owid', 'complete-downloaded-article'),
                self.row(3, 'freshwiki', 'complete-downloaded-article'),
                self.row(4, 'code2doc', 'function-code-record'),
                self.row(5, 'mcts-references', 'sentence-record'),
                self.row(6, 'iterater-human-doc', 'document-record'),
                self.row(7, 'other', 'document-record'),
                self.row(8, 'freshwiki', 'complete-downloaded-article', 'ja')]
        self.execute(rows)
        self.assertEqual(len(FakeClient.calls), 14)
        pairs = [json.loads(x) for x in (self.args.output / 'pairs.jsonl').read_text().splitlines()]
        self.assertEqual(len(pairs), 7)
        self.assertEqual(len({p['id'] for p in pairs}), 7)
        self.assertEqual(sum(p['collection'] == 'ai-enrichment-articles' for p in pairs), 3)
        self.assertEqual({p['extra']['semantic_packet']['unit_type'] for p in pairs},
                         {'full_article', 'technical_documentation', 'document_unit', 'sentence_unit'})
        self.assertEqual(len(json.loads((self.args.output / 'pilot-ready.json').read_text())['results']), 6)
        for call in FakeClient.calls:
            if call['schema_name'] == 'fresh_writing':
                packet = json.loads(call['messages'][-1]['content'])
                self.assertNotIn('source_units', json.dumps(packet))
                self.assertNotIn('queue_id', packet)
        self.execute(rows)
        self.assertEqual(len(FakeClient.calls), 14)
        # Recover one missing row from a per-item pair artifact, without billing.
        lost = pairs[0]
        (self.args.output / 'pairs.jsonl').write_text(''.join(json.dumps(p) + '\n' for p in pairs[1:]))
        self.execute(rows)
        recovered = [json.loads(x) for x in (self.args.output / 'pairs.jsonl').read_text().splitlines()]
        self.assertEqual(len(recovered), 7)
        self.assertEqual(sum(p['id'] == lost['id'] for p in recovered), 1)
        self.assertEqual(len(FakeClient.calls), 14)
    def test_hash_and_duplicate_ids_fail_before_client(self):
        row = self.row(1, 'coggen-owid', 'complete-downloaded-article')
        broken = {**row, 'selected_source_sha256': 'bad'}
        with self.assertRaisesRegex(ValueError, 'source_hash_mismatch'):
            self.execute([broken])
        with self.assertRaisesRegex(ValueError, 'duplicate_queue_ids'):
            self.execute([row, row])
        self.assertEqual(FakeClient.instances, [])
    def test_changed_queue_cannot_reuse_completed_pair(self):
        row = self.row(1, 'coggen-owid', 'complete-downloaded-article')
        self.execute([row])
        row['selected_source_text'] += ' changed'
        row['selected_source_sha256'] = m.digest(row['selected_source_text'])
        with self.assertRaisesRegex(ValueError, 'resume_configuration_mismatch'):
            self.execute([row])
        self.assertEqual(len(FakeClient.calls), 2)
    def test_failed_and_legacy_complete_states_never_rebill(self):
        row = self.row(1, 'coggen-owid', 'complete-downloaded-article')
        self.execute([row])
        item = self.args.output / 'items' / m.digest(row['queue_id'])[:24]
        (item / 'pair.json').unlink()
        (self.args.output / 'pairs.jsonl').unlink()
        self.execute([row])
        self.assertEqual(len(FakeClient.calls), 2)
        (item / 'state.json').write_text(json.dumps({'status': 'failed'}))
        self.execute([row])
        self.assertEqual(len(FakeClient.calls), 2)
    def test_incomplete_extraction_stops_before_writing_and_resume_holds(self):
        row = self.row(1, 'coggen-owid', 'complete-downloaded-article')
        FakeClient.mode = 'missing_unit'
        self.execute([row])
        self.assertEqual(len(FakeClient.calls), 1)
        self.assertFalse((self.args.output / 'pairs.jsonl').exists())
        failure = json.loads((self.args.output / 'failures.json').read_text())[0]
        self.assertEqual(failure['reason'], 'duplicate_or_missing_unit_assessments')
        FakeClient.mode = 'ok'
        self.execute([row])
        self.assertEqual(len(FakeClient.calls), 1)
    def test_unknown_writing_coverage_rejected_without_retry(self):
        row = self.row(1, 'coggen-owid', 'complete-downloaded-article')
        FakeClient.mode = 'unknown_coverage'
        self.execute([row])
        self.assertEqual(len(FakeClient.calls), 2)
        self.assertFalse((self.args.output / 'pairs.jsonl').exists())
        failure = json.loads((self.args.output / 'failures.json').read_text())[0]
        self.assertEqual(failure['reason'], 'invalid_coverage_status')
        self.execute([row])
        self.assertEqual(len(FakeClient.calls), 2)
    def test_required_unit_keys_and_normalized_coverage(self):
        source_units = [{'unit': 'u0001', 'text': 'a'}, {'unit': 'u0002', 'text': 'b'}]
        schema = m.extraction_schema(source_units)
        unit_schema = schema['properties']['by_unit']
        self.assertEqual(unit_schema['type'], 'array')
        self.assertEqual(unit_schema['items']['properties']['unit_id']['enum'], ['u0001', 'u0002'])
        self.assertNotIn('minItems', unit_schema)
        self.assertNotIn('maxItems', unit_schema)
        claim = {'subject': 'a', 'predicate': 'has', 'object': '1', 'qualifiers': [], 'attribution': None}
        raw = {'by_unit': {'u0001': {'claims': [claim], 'excluded_reason': None, 'unresolved': False},
                           'u0002': {'claims': [], 'excluded_reason': 'navigation only', 'unresolved': False}}}
        data = m.normalize_extraction(raw, source_units)
        m.validate_extraction(data, source_units)
        self.assertEqual(data['claims'][0]['source_units'], ['u0001'])
        for bad in ({'by_unit': {'u0001': raw['by_unit']['u0001']}},
                    {'by_unit': {**raw['by_unit'], 'u9999': raw['by_unit']['u0001']}},
                    {'by_unit': []}, None):
            with self.assertRaises(ValueError):
                m.normalize_extraction(bad, source_units)
        raw['by_unit']['u0002']['unresolved'] = 'false'
        with self.assertRaisesRegex(ValueError, 'invalid_unit_assessment'):
            m.normalize_extraction(raw, source_units)
        raw['by_unit']['u0002']['unresolved'] = False
        raw['by_unit']['u0001']['excluded_reason'] = 'also excluded'
        warnings = []
        normalized = m.normalize_extraction(raw, source_units, warnings)
        self.assertEqual(len(warnings), 1)
        self.assertNotIn('u0001', [e['unit'] for e in normalized['excluded_units']])
        self.assertEqual(raw['by_unit']['u0001']['excluded_reason'], 'also excluded')
    def test_claim_map_required_keys_partition_and_unknown_values(self):
        packet = {'claims': [{'id': 'c_one'}, {'id': 'c_two'}]}
        schema = m.writing_schema(packet)['properties']['coverage']
        self.assertEqual(schema['type'], 'array')
        self.assertEqual(schema['items']['properties']['claim_id']['enum'], ['c_one', 'c_two'])
        self.assertEqual(schema['items']['properties']['status']['enum'], ['covered', 'unresolved'])
        self.assertNotIn('minItems', schema)
        self.assertNotIn('maxItems', schema)
        raw = {'text': 'A complete candidate', 'coverage': {'c_one': {'status': 'covered', 'evidence': ['complete candidate']}, 'c_two': {'status': 'unresolved', 'evidence': []}}, 'issues': ['needs review']}
        data = m.normalize_writing(raw, packet)
        m.validate_writing(data, packet)
        self.assertEqual(data['covered_claim_ids'], ['c_one'])
        self.assertEqual(data['unresolved_claim_ids'], ['c_two'])
        for coverage in ({'c_one': raw['coverage']['c_one']}, {**raw['coverage'], 'extra': raw['coverage']['c_one']},
                         {'c_one': raw['coverage']['c_one'], 'c_two': {'status': 'maybe', 'evidence': []}},
                         {'c_one': raw['coverage']['c_one'], 'c_two': None},
                         {'c_one': raw['coverage']['c_one'], 'c_two': False},
                         {'c_one': raw['coverage']['c_one'], 'c_two': []},
                         {'c_one': {'status': 'covered', 'evidence': [123]}, 'c_two': raw['coverage']['c_two']}):
            with self.assertRaises(ValueError):
                m.normalize_writing({**raw, 'coverage': coverage}, packet)
        with self.assertRaises(ValueError):
            m.normalize_writing({**raw, 'issues': 'looks fine'}, packet)
    def test_v3_array_ids_must_be_complete_unique_and_known(self):
        us = [{'unit': 'u1', 'text': 'a'}, {'unit': 'u2', 'text': 'b'}]
        claim = {'subject': 'a', 'predicate': 'has', 'object': 'b', 'qualifiers': [], 'attribution': None}
        assessment = {'claims': [claim], 'excluded_reason': None, 'unresolved': False}
        good = [{'unit_id': u['unit'], **assessment} for u in us]
        m.validate_extraction(m.normalize_extraction({'by_unit': good}, us), us)
        for bad in (good[:1], [good[0], good[0]], [good[0], {**good[1], 'unit_id': 'invented'}]):
            with self.assertRaises(ValueError):
                m.normalize_extraction({'by_unit': bad}, us)
        packet = {'claims': [{'id': 'c1'}, {'id': 'c2'}]}
        good = [{'claim_id': 'c1', 'status': 'covered', 'evidence': ['a b']},
                {'claim_id': 'c2', 'status': 'unresolved', 'evidence': []}]
        raw = {'text': 'a   b', 'coverage': good, 'issues': []}
        m.validate_writing(m.normalize_writing(raw, packet), packet)
        for bad in (good[:1], [good[0], good[0]], [good[0], {**good[1], 'claim_id': 'invented'}],
                    [good[0], {**good[1], 'status': 'maybe'}]):
            with self.assertRaises(ValueError):
                m.normalize_writing({**raw, 'coverage': bad}, packet)
    def test_saved_stages_recover_prose_and_preserve_warning_audit(self):
        row = self.row(1, 'coggen-owid', 'complete-downloaded-article')
        self.execute([row])
        item = self.args.output / 'items' / m.digest(row['queue_id'])[:24]
        (item / 'pair.json').unlink()
        (self.args.output / 'pairs.jsonl').unlink()
        (item / 'state.json').write_text(json.dumps({'status': 'failed'}))
        (self.args.output / 'failures.json').write_text(json.dumps([{'source_id': row['source_id'], 'reason': 'old_evidence_failure'}]))
        raw = json.loads((item / 'writing-raw.json').read_text())
        raw['coverage'][0]['evidence'] = ['not actually in the complete prose']
        (item / 'writing-raw.json').write_text(json.dumps(raw))
        self.args.resume_saved_stages = True
        self.execute([row])
        self.assertEqual(len(FakeClient.calls), 2)
        pair = json.loads((self.args.output / 'pairs.jsonl').read_text())
        self.assertTrue(pair['extra']['normalization_warnings'])
        self.assertEqual(pair['extra']['writer_evidence'][0]['status'], 'covered')
        self.assertTrue(pair['extra']['writer_coverage']['unresolved_claim_ids'])
        self.assertEqual(pair['extra']['generation']['reused_saved_stages'], {'extraction': True, 'writing': True})
        self.assertEqual(json.loads((self.args.output / 'failures.json').read_text()), [])
        self.assertTrue(json.loads((self.args.output / 'failure-history.json').read_text())[0]['failures'])
    def test_resume_extraction_only_makes_one_new_writer_call(self):
        row = self.row(1, 'coggen-owid', 'complete-downloaded-article')
        with patch.object(m, 'validate_extraction', side_effect=ValueError('prior_validation_failure')):
            self.execute([row])
        self.assertEqual(len(FakeClient.calls), 1)
        self.args.resume_saved_stages = True
        self.execute([row])
        self.assertEqual(len(FakeClient.calls), 2)
        pair = json.loads((self.args.output / 'pairs.jsonl').read_text())
        self.assertEqual(pair['extra']['generation']['reused_saved_stages'], {'extraction': True, 'writing': False})
    def test_unknown_saved_call_and_unaccepted_writer_never_retry(self):
        row = self.row(1, 'coggen-owid', 'complete-downloaded-article')
        with patch.object(m, 'validate_extraction', side_effect=ValueError('prior_validation_failure')):
            self.execute([row])
        ledger_path = self.args.output / 'budget-ledger.json'
        ledger = json.loads(ledger_path.read_text())
        ledger['entries'][0]['state'] = 'unknown'
        ledger_path.write_text(json.dumps(ledger))
        self.args.resume_saved_stages = True
        self.execute([row])
        self.assertEqual(len(FakeClient.calls), 1)
        ledger['entries'][0]['state'] = 'settled'
        ledger_path.write_text(json.dumps(ledger))
        item = self.args.output / 'items' / m.digest(row['queue_id'])[:24]
        (item / 'writer-packet.json').write_text('{}')
        self.execute([row])
        self.assertEqual(len(FakeClient.calls), 1)
    def test_evidence_mismatch_downgrades_without_mutating_raw(self):
        packet = {'claims': [{'id': 'c1'}]}
        raw = {'text': 'Complete candidate prose.', 'coverage': [{'claim_id': 'c1', 'status': 'covered', 'evidence': ['different wording']}], 'issues': []}
        warnings = []
        normalized = m.normalize_writing(raw, packet, warnings)
        self.assertEqual(normalized['text'], raw['text'])
        self.assertEqual(normalized['unresolved_claim_ids'], ['c1'])
        self.assertTrue(normalized['issues'])
        self.assertEqual(raw['coverage'][0]['status'], 'covered')
        self.assertEqual(raw['issues'], [])
        self.assertEqual(len(warnings), 1)
    def test_fence_units_and_content_ids(self):
        source = 'Intro\n\n````markdown\n```python\n\nprint(1)\n```\n\n````\n\nEnd'
        us = m.units(source)
        self.assertEqual(len(us), 3)
        self.assertIn('print(1)', us[1]['text'])
        self.assertIn('\n\n', us[1]['text'])
        claims = [{'subject': 'A', 'predicate': 'has', 'object': '1', 'qualifiers': [],
                   'attribution': None, 'source_units': ['u0001']}]
        q = self.row(1, 'coggen-owid', 'complete-downloaded-article')
        p1, _ = m.packet_for({'claims': claims}, q)
        claims[0]['source_units'] = ['u0099']
        p2, _ = m.packet_for({'claims': claims + claims}, q)
        self.assertEqual(p1, p2)
        self.assertNotIn('source_units', p1['claims'][0])

if __name__ == '__main__':
    unittest.main(verbosity=2)

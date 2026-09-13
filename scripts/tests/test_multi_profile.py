"""Offline model-profile and six-article integration tests; no network or secrets.

Copy beside the other scripts/tests, or set PLAINVOICE_SCRIPTS to the scripts
directory when running this standalone temporary copy.
"""
import argparse
import contextlib
import copy
from decimal import Decimal
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

sys.path.insert(0, os.environ.get('PLAINVOICE_SCRIPTS', str(Path(__file__).resolve().parents[1])))
import plainvoice_budget_client_multi as client_module
import run_ai_enrichment_multi as runner

MODEL25 = 'google/gemini-2.5-flash-lite'
MODEL31 = 'google/gemini-3.1-flash-lite'
CANONICAL31 = 'google/gemini-3.1-flash-lite-20260507'
PARAMS = ['max_tokens', 'response_format', 'structured_outputs', 'reasoning', 'temperature']


class FixtureAPI:
    """Literal public-contract fixture plus deterministic in-memory inference."""
    def __init__(self, model=MODEL31, defect=None):
        self.model = model
        self.defect = defect
        self.posts = []
        self.gets = []
        self.lock = threading.Lock()
        self.canonical = CANONICAL31 if model == MODEL31 else MODEL25
        self.tag = 'google-vertex/global' if model == MODEL31 else 'google-vertex'
        self.pricing = {'prompt': '0.00000025', 'completion': '0.0000015'} if model == MODEL31 else {
            'prompt': '0.0000001', 'completion': '0.0000004'}

    def __call__(self, method, url, headers, body, timeout):
        if method == 'GET':
            self.gets.append((url, dict(headers)))
            if url.endswith('/models'):
                item = {'id': self.model, 'canonical_slug': self.canonical,
                        'expiration_date': None, 'pricing': dict(self.pricing),
                        'supported_parameters': list(PARAMS), 'reasoning': {'mandatory': False}}
                if self.defect == 'price':
                    item['pricing']['prompt'] = '0.000000251'
                if self.defect == 'canonical':
                    item['canonical_slug'] = 'google/unexpected-snapshot'
                if self.defect == 'mandatory_reasoning':
                    item['reasoning']['mandatory'] = True
                return {'data': [item]}
            if url.endswith('/endpoints/zdr'):
                return {'data': [] if self.defect == 'zdr' else [
                    {'model_id': self.model, 'tag': self.tag, 'status': 0}]}
            endpoint = {'tag': self.tag, 'status': 0, 'context_length': 1048576,
                        'max_completion_tokens': 65536 if self.model == MODEL31 else 65535,
                        'supported_parameters': list(PARAMS), 'pricing': dict(self.pricing)}
            if self.defect == 'route':
                endpoint['tag'] = 'google-vertex/eu'
            if self.defect == 'endpoint_price':
                endpoint['pricing']['completion'] = '0.00000151'
            return {'data': {'endpoints': [endpoint]}}
        if method != 'POST':
            raise AssertionError('Unexpected fixture method')
        request = json.loads(body)
        with self.lock:
            self.posts.append((request, bytes(body)))
            sequence = len(self.posts)
        if self.defect == 'timeout':
            raise TimeoutError('private upstream message')
        content = {'text': 'Offline candidate.'}
        schema_name = request.get('response_format', {}).get('json_schema', {}).get('name')
        if schema_name in ('semantic_inventory', 'fresh_writing'):
            user = json.loads(request['messages'][-1]['content'])
            if schema_name == 'semantic_inventory':
                content = {'by_unit': [{'unit_id': unit['unit'], 'claims': [{
                    'subject': 'Article', 'predicate': 'states', 'object': unit['text'],
                    'qualifiers': [], 'attribution': None}], 'excluded_reason': None,
                    'unresolved': False} for unit in user['source_units']]}
            else:
                content = {'text': '\n\n'.join(claim['object'] for claim in user['claims']),
                           'coverage': [{'claim_id': claim['id'], 'status': 'covered',
                                         'evidence': [claim['object']]} for claim in user['claims']],
                           'issues': []}
        return {'id': 'gen-offline-' + str(sequence),
                'model': 'google/wrong-model' if self.defect == 'served_model' else self.canonical,
                'provider': 'Google', 'choices': [{'finish_reason': 'stop', 'message': {
                    'content': json.dumps(content, ensure_ascii=False)}}],
                'usage': {'cost': Decimal('0.0001'), 'prompt_tokens': 50, 'completion_tokens': 50}}


class ProfileSafetyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.sequence = 0

    def tearDown(self):
        # Production locks intentionally live for the process; close only these
        # fixture locks once all test requests have finished.
        with client_module._REGISTRY_LOCK:
            for key in list(client_module._REGISTRY):
                if Path(key).is_relative_to(self.root):
                    client_module._REGISTRY.pop(key).lock_file.close()
        self.tmp.cleanup()

    def make_client(self, api, **kwargs):
        self.sequence += 1
        defaults = {'api_key': 'offline-test-key', 'model': api.model,
                    'ledger_path': self.root / ('ledger-' + str(self.sequence) + '.json'),
                    'transport': api}
        defaults.update(kwargs)
        return client_module.BudgetClient(**defaults)

    def call(self, client):
        return client.chat(messages=[{'role': 'user', 'content': 'Test article 中文.'}], max_tokens=1000)

    def test_31_alias_canonical_privacy_price_and_reservation(self):
        api = FixtureAPI()
        client = self.make_client(api)
        verified = client.preflight(force=True)
        self.assertEqual(verified['canonical_slug'], CANONICAL31)
        self.assertEqual(verified['provider_tags'], ['google-vertex/global'])
        result = self.call(client)
        self.assertEqual(result.metadata['model'], MODEL31)
        self.assertEqual(result.metadata['served_model'], CANONICAL31)
        request, encoded = api.posts[0]
        self.assertEqual(request['provider'], {'only': ['google-vertex/global'], 'allow_fallbacks': False,
            'require_parameters': True, 'data_collection': 'deny', 'zdr': True,
            'max_price': {'prompt': .25, 'completion': 1.5}})
        self.assertEqual(request['reasoning'], {'enabled': False})
        self.assertEqual(Decimal(result.metadata['reserved_usd']),
            Decimal(len(encoded) + 4096) * Decimal('0.00000025') + Decimal(1000) * Decimal('0.0000015'))
        self.assertEqual(len(api.gets), 3)
        self.assertTrue(all('Authorization' not in headers for _, headers in api.gets))
        self.assertNotIn('offline-test-key', client.path.read_text() + repr(client))

    def test_default_25_profile_stays_supported(self):
        api = FixtureAPI(MODEL25)
        client = self.make_client(api)
        self.call(client)
        self.assertEqual(api.posts[0][0]['provider']['max_price'], {'prompt': .1, 'completion': .4})
        self.assertEqual(client.summary()['model'], MODEL25)
        self.assertEqual(runner.DEFAULT_MODEL, MODEL25)

    def test_changed_catalog_price_identity_privacy_or_route_fail_before_post(self):
        for defect in ('price', 'canonical', 'mandatory_reasoning', 'zdr', 'route', 'endpoint_price'):
            with self.subTest(defect=defect):
                api = FixtureAPI(defect=defect)
                client = self.make_client(api)
                with self.assertRaises(client_module.PreflightError):
                    self.call(client)
                self.assertEqual(api.posts, [])
                self.assertEqual(client.summary()['calls'], 0)

    def test_force_preflight_detects_price_change_after_success(self):
        api = FixtureAPI()
        client = self.make_client(api)
        self.call(client)
        api.defect = 'price'
        with self.assertRaises(client_module.PreflightError):
            client.preflight(force=True)
        self.assertEqual(len(api.posts), 1)

    def test_budget_unknown_model_and_maxcalls_guards(self):
        api = FixtureAPI()
        for kwargs in ({'budget_usd': '1.000001'}, {'model': 'google/other-model'}):
            with self.assertRaises(client_module.BudgetError):
                self.make_client(api, **kwargs)
        client = self.make_client(api, max_calls=1)
        self.call(client)
        with self.assertRaises(client_module.BudgetError):
            self.call(client)
        self.assertEqual(len(api.posts), 1)

    def test_unknown_outcome_holds_and_never_retries(self):
        api = FixtureAPI(defect='timeout')
        client = self.make_client(api)
        with self.assertRaises(client_module.UnknownOutcome):
            self.call(client)
        summary = client.summary()
        self.assertGreater(Decimal(summary['held_usd']), 0)
        self.assertEqual(Decimal(summary['spent_usd']), 0)
        self.assertTrue(summary['halted'])
        with self.assertRaises(client_module.BudgetError):
            self.call(client)
        self.assertEqual(len(api.posts), 1)
        self.assertNotIn('private upstream message', client.path.read_text())

    def test_unexpected_served_model_settles_charge_and_halts(self):
        api = FixtureAPI(defect='served_model')
        client = self.make_client(api)
        with self.assertRaises(client_module.RejectedResponse):
            self.call(client)
        self.assertEqual(Decimal(client.summary()['spent_usd']), Decimal('0.0001'))
        self.assertTrue(client.summary()['halted'])

    def row(self, i):
        source = 'Example title\n\nThis article records 123 items.\n\nIt preserves details.'
        return {'queue_id': 'queue-' + str(i), 'source_id': 'source-' + str(i),
                'collection': ('rewrite-article-v2', 'coggen-owid', 'freshwiki')[i % 3],
                'source_unit_type': 'existing-complete-article', 'target_language': 'zh' if i == 0 else 'en',
                'selected_source_text': source, 'selected_source_sha256': runner.digest(source),
                'selected_source_chars': len(source),
                'source_record': {'title': 'Example ' + str(i), 'provenance': {'local_path': 'fixture.jsonl'}},
                'selected_source_label': 'Original', 'selected_source_role': 'human',
                'selected_source_side': 'left', 'authorship_status': 'fixture-as-labeled',
                'quality_notes': [], 'optional': {}}

    def execute_runner(self, rows, api, model=MODEL31):
        prompts = self.root / 'prompts'
        prompts.mkdir(exist_ok=True)
        for stage in ('extract', 'write'):
            (prompts / ('enrichment-' + stage + '-v3.txt')).write_text('Offline fixture ' + stage)
        queue = self.root / 'queue.jsonl'
        queue.write_text(''.join(json.dumps(row) + '\n' for row in rows))
        args = argparse.Namespace(queue=queue, output=self.root / 'run', model=model,
            budget='1', max_calls=12, workers=3, browser_key=True, wait_start=False,
            pause_after_pilot=False, skip_japanese=True, resume_saved_stages=False)
        def factory(**kwargs):
            return client_module.BudgetClient(**kwargs, transport=api)
        with patch.object(runner, 'BudgetClient', side_effect=factory), \
             patch.object(runner, 'receive_key', return_value='offline-test-key'), \
             patch.object(runner, 'SCRIPT_ROOT', self.root), contextlib.redirect_stdout(io.StringIO()):
            runner.run(args)
        return args

    def test_six_articles_twelve_calls_comparison_scope_and_idempotent_resume(self):
        api = FixtureAPI()
        rows = [self.row(i) for i in range(6)]
        args = self.execute_runner(rows, api)
        pairs = [json.loads(line) for line in (args.output / 'pairs.jsonl').read_text().splitlines()]
        self.assertEqual(len(pairs), 6)
        self.assertEqual(len(api.posts), 12)
        self.assertEqual(len({pair['id'] for pair in pairs}), 6)
        for pair in pairs:
            self.assertEqual(pair['collection'], 'ai-enrichment-comparison')
            self.assertIn('Gemini 3.1 Flash Lite', pair['collection_title'])
            self.assertIn('Gemini 3.1 Flash Lite', pair['right']['label'])
            self.assertEqual(pair['extra']['generation']['model'], MODEL31)
            self.assertIn('gemini-31-flash-lite', pair['id'])
            self.assertEqual(pair['extra']['semantic_packet']['unit_type'], 'full_article')
        ledger = json.loads((args.output / 'budget-ledger.json').read_text())
        self.assertEqual(ledger['model'], MODEL31)
        self.assertTrue(all(entry['state'] == 'settled' for entry in ledger['entries']))
        config = json.loads((args.output / 'config.json').read_text())
        self.assertEqual(config['model'], MODEL31)
        self.assertEqual(config['version'], 'plainvoice-enrichment-svo-v3')
        self.assertEqual(config['budget_usd'], '1')
        self.execute_runner(rows, api)
        self.assertEqual(len(api.posts), 12)
        for row in rows:
            self.assertNotEqual(runner.pair_id({**row, '_model': MODEL25}),
                                runner.pair_id({**row, '_model': MODEL31}))

    def test_out_of_scope_queues_fail_without_network(self):
        for rows in ([], [self.row(i) for i in range(7)],
                     [{**self.row(0), 'source_unit_type': 'sentence-record'}]):
            with self.subTest(records=len(rows)):
                api = FixtureAPI()
                with self.assertRaisesRegex(ValueError, 'at_most_six_complete_articles'):
                    self.execute_runner(rows, api)
                self.assertEqual(api.gets, [])
                self.assertEqual(api.posts, [])


if __name__ == '__main__':
    unittest.main()

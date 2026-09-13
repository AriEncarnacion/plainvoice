import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import concurrent.futures
from decimal import Decimal
import json
import io
import urllib.error
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from plainvoice_budget_client import BudgetClient, BudgetError, PreflightError, UnknownOutcome, RejectedResponse, HTTPFailure, _error_diagnostic, _http

MODEL = 'google/gemini-2.5-flash-lite'
PARAMS = ['max_tokens', 'response_format', 'structured_outputs', 'reasoning', 'temperature']

class FakeAPI:
    def __init__(self, mode='ok'):
        self.mode = mode
        self.posts = []
        self.get_auth = []
        self.lock = threading.Lock()
        self.started = threading.Event()
        self.release = threading.Event()
    def __call__(self, method, url, headers, body, timeout):
        if method == 'GET':
            self.get_auth.append(headers.get('Authorization'))
            if url.endswith('/models'):
                return {'data': [{'id': MODEL, 'canonical_slug': MODEL, 'expiration_date': None,
                    'pricing': {'prompt': '0.0000002' if self.mode == 'price_drift' else '0.0000001', 'completion': '0.0000004'},
                    'supported_parameters': PARAMS, 'reasoning': {'mandatory': False}}]}
            if url.endswith('/endpoints/zdr'):
                return {'data': [] if self.mode == 'no_zdr' else [{'model_id': MODEL, 'tag': 'google-vertex', 'status': 0}]}
            return {'data': {'endpoints': [{'tag': 'google-vertex', 'status': 0,
                'context_length': 1048576, 'max_completion_tokens': 65535,
                'supported_parameters': PARAMS,
                'pricing': {'prompt': '0.0000001', 'completion': '0.0000004'}}]}}
        with self.lock:
            self.posts.append(json.loads(body))
        self.started.set()
        if self.mode == 'block':
            if not self.release.wait(4):
                raise RuntimeError('test timeout')
        if self.mode in ('401', '500'):
            raise HTTPFailure('safe HTTP failure', http_status=int(self.mode))
        if self.mode == 'lost':
            raise TimeoutError('secret-value test raw error body')
        result = {'id': 'gen-test-123', 'model': MODEL, 'provider': 'Google',
            'choices': [{'finish_reason': 'stop', 'message': {'content': '{"text":"你好 article"}'}}],
            'usage': {'cost': Decimal('0.0001'), 'prompt_tokens': 50, 'completion_tokens': 50}}
        if self.mode == 'missing_cost':
            result['usage'].pop('cost')
        if self.mode == 'refusal':
            result['choices'][0]['message']['refusal'] = 'raw refusal with private content'
        if self.mode == 'length':
            result['choices'][0]['finish_reason'] = 'length'
        if self.mode == 'other_model':
            result['model'] = 'other/model'
        if self.mode == 'overcharge':
            result['usage']['cost'] = Decimal('1')
        if self.mode == 'malformed_json':
            result['choices'][0]['message']['content'] = 'not json'
        return result

class TestBudgetSafety(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name) / 'ledger.json'
    def tearDown(self):
        self.directory.cleanup()
    def client(self, api, **kw):
        return BudgetClient(api_key='secret-value', ledger_path=self.path, transport=api, **kw)
    def call(self, c, **kw):
        return c.chat(messages=[{'role': 'user', 'content': 'Private article 测试'}], max_tokens=1000, **kw)
    def test_concurrent_pending_reservations_prevent_overspend(self):
        api = FakeAPI('block')
        c = self.client(api, budget_usd='0.0010')
        with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
            first = pool.submit(self.call, c)
            self.assertTrue(api.started.wait(2))
            other = [pool.submit(self.call, c) for _ in range(10)]
            for f in other:
                with self.assertRaises(BudgetError):
                    f.result()
            self.assertEqual(len(api.posts), 1)
            self.assertGreater(Decimal(c.summary()['held_usd']), Decimal('0.0008'))
            api.release.set()
            first.result()
        self.assertEqual(c.summary()['calls'], 1)
        self.assertEqual(Decimal(c.summary()['spent_usd']), Decimal('0.0001'))
        self.assertEqual(Decimal(c.summary()['held_usd']), 0)
    def test_multiple_clients_share_reservation_lock(self):
        api = FakeAPI('block')
        one = self.client(api, budget_usd='0.0010')
        two = self.client(api, budget_usd='0.0010')
        with concurrent.futures.ThreadPoolExecutor() as pool:
            f = pool.submit(self.call, one)
            self.assertTrue(api.started.wait(2))
            with self.assertRaises(BudgetError):
                self.call(two)
            api.release.set()
            f.result()
        self.assertEqual(len(api.posts), 1)
    def test_timeout_preserves_reservation_halts_and_redacts(self):
        api = FakeAPI('lost')
        c = self.client(api)
        with self.assertRaises(UnknownOutcome) as caught:
            self.call(c)
        summary = c.summary()
        self.assertTrue(summary['halted'])
        self.assertGreater(Decimal(summary['held_usd']), 0)
        with self.assertRaises(BudgetError):
            self.call(c)
        again = self.client(api)
        with self.assertRaises(BudgetError):
            self.call(again)
        self.assertEqual(len(api.posts), 1)
        saved = self.path.read_text()
        for secret in ['secret-value', 'Private article', '测试', 'raw error']:
            self.assertNotIn(secret, saved + str(caught.exception) + repr(c))
    def test_pending_from_prior_process_is_unknown(self):
        self.path.write_text(json.dumps({'version': 1, 'model': MODEL, 'budget_usd': '20',
            'max_calls': 80, 'halted': False, 'entries': [{'id': 'interrupted',
            'state': 'pending', 'reserved_usd': '0.25'}]}))
        api = FakeAPI()
        c = self.client(api)
        self.assertTrue(c.summary()['halted'])
        self.assertEqual(c.summary()['states']['unknown'], 1)
        with self.assertRaises(BudgetError):
            self.call(c)
        self.assertFalse(api.posts)
    def test_missing_cost_is_unknown_not_estimated_settlement(self):
        api = FakeAPI('missing_cost')
        c = self.client(api)
        with self.assertRaises(UnknownOutcome):
            self.call(c)
        self.assertEqual(c.summary()['states']['unknown'], 1)
        self.assertEqual(Decimal(c.summary()['spent_usd']), 0)
        self.assertGreater(Decimal(c.summary()['held_usd']), 0)
    def test_live_price_change_fails_before_post(self):
        api = FakeAPI('price_drift')
        c = self.client(api)
        with self.assertRaises(PreflightError):
            self.call(c)
        self.assertEqual(c.summary()['calls'], 0)
        self.assertFalse(api.posts)
        self.assertTrue(all(x is None for x in api.get_auth))
    def test_privacy_filter_fails_closed(self):
        api = FakeAPI('no_zdr')
        c = self.client(api)
        with self.assertRaises(PreflightError):
            self.call(c)
        self.assertFalse(api.posts)
    def test_truncation_charge_recorded_but_content_not_returned(self):
        api = FakeAPI('length')
        c = self.client(api)
        with self.assertRaises(RejectedResponse):
            self.call(c)
        self.assertEqual(c.summary()['states']['settled'], 1)
        self.assertEqual(Decimal(c.summary()['spent_usd']), Decimal('0.0001'))
    def test_refusal_rejected_charge_recorded_without_refusal_body(self):
        api = FakeAPI('refusal')
        c = self.client(api)
        with self.assertRaises(RejectedResponse):
            self.call(c)
        self.assertEqual(c.summary()['states']['settled'], 1)
        self.assertNotIn('raw refusal', self.path.read_text())
    def test_unexpected_model_halts_after_settlement(self):
        api = FakeAPI('other_model')
        c = self.client(api)
        with self.assertRaises(RejectedResponse):
            self.call(c)
        self.assertTrue(c.summary()['halted'])
        self.assertEqual(c.summary()['states']['settled'], 1)
    def test_maxcalls_guards_even_tiny_known_cost(self):
        api = FakeAPI()
        c = self.client(api, max_calls=1)
        self.call(c)
        with self.assertRaises(BudgetError):
            self.call(c)
        self.assertEqual(len(api.posts), 1)
    def test_output_bound_and_global_budget_before_network(self):
        api = FakeAPI()
        with self.assertRaises(BudgetError):
            self.client(api, budget_usd='20.000001')
        c = self.client(api)
        with self.assertRaises(BudgetError):
            c.chat(messages=[{'role': 'user', 'content': 'x'}], max_tokens=65536)
        self.assertFalse(api.posts)
    def test_json_and_exact_private_request_controls(self):
        api = FakeAPI()
        c = self.client(api)
        schema = {'type': 'object', 'properties': {'text': {'type': 'string'}},
                  'required': ['text'], 'additionalProperties': False}
        result = self.call(c, json_schema=schema)
        self.assertEqual(result.parsed['text'], '你好 article')
        req = api.posts[0]
        self.assertEqual(req['provider']['max_price'], {'prompt': .1, 'completion': .4})
        self.assertTrue(req['provider']['require_parameters'])
        self.assertTrue(req['provider']['zdr'])
        self.assertEqual(req['provider']['data_collection'], 'deny')
        self.assertFalse(req['reasoning']['enabled'])
        self.assertNotIn('usage', req)  # deprecated parameter deliberately absent
        entry = json.loads(self.path.read_text())['entries'][0]
        self.assertGreaterEqual(entry['input_token_bound'], len(json.dumps(req, ensure_ascii=False).encode('utf8')))
    def test_invalid_json_rejected_and_billed(self):
        api = FakeAPI('malformed_json')
        c = self.client(api)
        with self.assertRaises(RejectedResponse):
            self.call(c, json_schema={'type': 'object'})
        self.assertEqual(c.summary()['states']['settled'], 1)
    def test_cache_force_expiry_and_mutation_isolation(self):
        api = FakeAPI()
        c = self.client(api)
        info = c.preflight(force=True)
        self.assertEqual(len(api.get_auth), 3)
        info['provider_tags'].append('untrusted-provider')
        self.assertNotIn('untrusted-provider', c.preflight()['provider_tags'])
        self.call(c)
        self.assertEqual(len(api.get_auth), 3)
        c.preflight(force=True)
        self.assertEqual(len(api.get_auth), 6)
        with patch('plainvoice_budget_client.time.monotonic', return_value=c._preflight_cache_time + 61):
            c.preflight()
        self.assertEqual(len(api.get_auth), 9)
    def test_http_status_preserved_without_releasing_uncertain_charge(self):
        api = FakeAPI('401')
        c = self.client(api)
        with self.assertRaises(UnknownOutcome) as caught:
            self.call(c)
        self.assertEqual(caught.exception.http_status, 401)
        self.assertIn('401', str(caught.exception))
        entry = json.loads(self.path.read_text())['entries'][0]
        self.assertEqual(entry['metadata']['http_status'], 401)
        self.assertEqual(entry['state'], 'unknown')
        self.assertGreater(Decimal(c.summary()['held_usd']), 0)
        self.assertEqual(len(api.posts), 1)
    def test_server_error_stays_unknown(self):
        api = FakeAPI('500')
        c = self.client(api)
        with self.assertRaises(UnknownOutcome) as caught:
            self.call(c)
        self.assertEqual(caught.exception.http_status, 500)
        self.assertTrue(c.summary()['halted'])
        self.assertEqual(c.summary()['states']['unknown'], 1)
    def test_ledger_write_failure_prevents_post(self):
        api = FakeAPI()
        c = self.client(api)
        with patch('plainvoice_budget_client.os.replace', side_effect=OSError('disk failed')):
            with self.assertRaises(BudgetError):
                self.call(c)
        self.assertFalse(api.posts)
        self.assertTrue(c.summary()['halted'])
    def test_corrupt_ledger_never_reinitializes_budget(self):
        api = FakeAPI()
        c = self.client(api)
        self.path.write_text('{broken')
        with self.assertRaises(BudgetError):
            self.call(c)
        self.assertFalse(api.posts)
    def test_nested_provider_diagnostic_drops_private_echo(self):
        secret = 'sk-or-v1-' + 'a' * 60
        source = 'CONFIDENTIAL source text must never be emitted'
        raw = json.dumps({'error': {'message': 'Provider returned error ' + source + secret, 'code': 400,
            'metadata': {'raw': json.dumps({'error': {'code': 400, 'status': 'INVALID_ARGUMENT',
            'message': 'Unable to submit request because it has a response schema with too many states for serving. ' + source + secret}})}}}).encode()
        result = _error_diagnostic(raw)
        self.assertIn('schema_too_many_states', result)
        self.assertIn('INVALID_ARGUMENT', result)
        self.assertNotIn(source, result)
        self.assertNotIn(secret, result)
        self.assertLessEqual(len(result), 800)
    def test_arbitrary_or_oversized_error_is_never_echoed(self):
        raw = json.dumps({'error': {'message': 'private unrelated text sk-secretvalue'}}).encode()
        self.assertEqual(_error_diagnostic(raw), 'outer: unclassified_provider_error')
        self.assertEqual(_error_diagnostic(b'x' * 65537), 'error_body_unavailable')
        self.assertEqual(_error_diagnostic(b'<html>private key</html>'), 'unclassified_provider_error')
    def test_http_error_transport_exposes_only_safe_diagnostic(self):
        payload = json.dumps({'error': {'message': 'Provider returned error', 'metadata': {'raw': json.dumps(
            {'error': {'status': 'INVALID_ARGUMENT', 'message': 'Invalid JSON schema: too many states. sk-secretvalue PRIVATE_ARTICLE'}})}}}).encode()
        error = urllib.error.HTTPError('https://openrouter.ai/api/v1/chat/completions', 400,
                                      'Private reason', {}, io.BytesIO(payload))
        with patch('plainvoice_budget_client.urllib.request.build_opener') as build:
            build.return_value.open.side_effect = error
            with self.assertRaises(HTTPFailure) as caught:
                _http('POST', 'https://openrouter.ai/api/v1/chat/completions', {}, b'{}', 1)
        self.assertEqual(caught.exception.http_status, 400)
        self.assertIn('schema_too_many_states', caught.exception.diagnostic)
        self.assertNotIn('PRIVATE_ARTICLE', str(caught.exception) + caught.exception.diagnostic)
        self.assertNotIn('sk-secretvalue', str(caught.exception) + caught.exception.diagnostic)
    def test_unknown_provider_accounting_bound_halts(self):
        api = FakeAPI('overcharge')
        c = self.client(api)
        with self.assertRaises(UnknownOutcome):
            self.call(c)
        self.assertTrue(c.summary()['halted'])
        self.assertEqual(c.summary()['states']['unknown'], 1)
        self.assertEqual(Decimal(c.summary()['held_usd']), Decimal('1'))

if __name__ == '__main__':
    unittest.main(verbosity=2)

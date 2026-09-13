"""Bounded OpenRouter client. No CLI, secrets lookup, logging, or automatic retries.

API:
    client = BudgetClient(api_key=key, ledger_path=path, budget_usd='20', max_calls=80)
    info = client.preflight(force=True)  # public GETs; chat uses a 60-second cache
    result = client.chat(messages=[...], max_tokens=16384, json_schema=schema)
    result.content / result.parsed / result.metadata; client.summary()

json_schema is the JSON Schema itself (not the response_format wrapper). It is
sent as strict structured output. The client checks JSON syntax; caller owns
application-specific schema/semantic validation. No message/content/key is saved.
Each actual request is preceded by a durable reservation. Ambiguous outcomes
hold their reservations and halt new calls, including after process restart.
The $20 hard ceiling covers inference, not taxes or credit-purchase fees.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import fcntl
import json
import os
from pathlib import Path
import re
import tempfile
import threading
import time
import urllib.error
import urllib.request
import uuid

MODEL = 'google/gemini-2.5-flash-lite'
INPUT_RATE = Decimal('0.10') / 1_000_000
OUTPUT_RATE = Decimal('0.40') / 1_000_000
MAX_BUDGET = Decimal('20')
BASE = 'https://openrouter.ai/api/v1'
SAFE_ID = re.compile(r'^[A-Za-z0-9_.:/ -]{1,160}$')
_REGISTRY = {}
_REGISTRY_LOCK = threading.Lock()


class BudgetError(RuntimeError):
    """Safe static error; never includes upstream response or request content."""
    def __init__(self, message, *, http_status=None, diagnostic=None):
        super().__init__(message)
        self.http_status = http_status if type(http_status) is int and 100 <= http_status <= 599 else None
        self.diagnostic = diagnostic


class HTTPFailure(BudgetError):
    pass


class PreflightError(BudgetError):
    pass


class UnknownOutcome(BudgetError):
    pass


class RejectedResponse(BudgetError):
    pass


@dataclass(frozen=True)
class ChatResult:
    content: str
    parsed: object
    metadata: dict


def _decimal(value):
    if isinstance(value, bool):
        raise ValueError('invalid decimal')
    try:
        val = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError('invalid decimal') from None
    if not val.is_finite() or val < 0:
        raise ValueError('invalid decimal')
    return val


def _integer(value):
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError('invalid integer')
    return value


def _safe_id(value):
    return value if isinstance(value, str) and SAFE_ID.fullmatch(value) else None


def _json_loads(data):
    def constant(_):
        raise ValueError('non-finite JSON')
    return json.loads(data, parse_float=Decimal, parse_constant=constant)


def _dump(data):
    return json.dumps(data, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')


def _error_diagnostic(raw):
    """Classify bounded provider messages without returning any arbitrary text.

    Error messages can echo prompts or credentials. Only static labels and
    allowlisted protocol codes leave this function; the raw body stays in memory.
    """
    try:
        if not isinstance(raw, bytes) or len(raw) > 65536:
            return 'error_body_unavailable'
        data = _json_loads(raw)
        outer = data.get('error', data) if isinstance(data, dict) else {}
        if not isinstance(outer, dict):
            return 'unclassified_provider_error'
        messages = [('outer', outer)]
        metadata = outer.get('metadata', {})
        provider_raw = metadata.get('raw') if isinstance(metadata, dict) else None
        if isinstance(provider_raw, str):
            provider_raw = _json_loads(provider_raw)
        if isinstance(provider_raw, list) and provider_raw:
            provider_raw = provider_raw[0]
        if isinstance(provider_raw, dict):
            provider_error = provider_raw.get('error', provider_raw)
            if isinstance(provider_error, dict):
                messages.append(('provider', provider_error))
        pieces = []
        for source, error in messages:
            message = error.get('message', '')
            message = re.sub(r'(?i)sk-[a-z0-9_-]+', '[REDACTED]', message[:65536]) if isinstance(message, str) else ''
            text = message.lower()
            labels = []
            patterns = [
                ('schema_too_many_states', r'too many states'),
                ('schema_complexity', r'(schema.{0,100}(complex|too large|too deep|exceed))|((complex|too large|too deep).{0,50}schema)'),
                ('schema_unsupported_field', r'unknown name|unsupported.{0,50}(schema|field|property)|cannot find field'),
                ('schema_type_mismatch', r'(schema|type).{0,70}(mismatch|expected|invalid type)'),
                ('schema_empty_required_field', r'(should|must).{0,20}(non-empty|non empty)'),
                ('invalid_argument', r'invalid.?argument|invalid argument'),
                ('context_length_exceeded', r'context.{0,30}(length|limit)|input token count.{0,50}exceed'),
                ('max_output_tokens_invalid', r'(max_tokens|maxoutputtokens|max output tokens).{0,80}(limit|exceed|invalid|range)'),
                ('no_eligible_endpoint', r'no endpoints|no available provider|no provider available'),
                ('insufficient_credits', r'insufficient.{0,30}(credit|fund|balance)|credit.{0,30}(insufficient|exhaust)'),
                ('authentication_error', r'authentication|unauthorized|invalid api key'),
                ('permission_denied', r'permission.denied|forbidden'),
                ('rate_limit', r'rate.limit|too many requests'),
                ('provider_error', r'provider returned error|upstream error'),
            ]
            for label, pattern in patterns:
                if re.search(pattern, text):
                    labels.append(label)
            protocol = error.get('status')
            if protocol in ('INVALID_ARGUMENT', 'RESOURCE_EXHAUSTED', 'UNAUTHENTICATED',
                            'PERMISSION_DENIED', 'NOT_FOUND', 'INTERNAL', 'UNAVAILABLE',
                            'DEADLINE_EXCEEDED', 'FAILED_PRECONDITION'):
                labels.append(protocol)
            code = error.get('code')
            if type(code) is int and 100 <= code <= 599:
                labels.append('code_' + str(code))
            pieces.append(source + ': ' + ','.join(labels or ['unclassified_provider_error']))
        return '; '.join(pieces)[:800]
    except Exception:
        return 'unclassified_provider_error'


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _http(method, url, headers, body, timeout):
    # No authorization forwarding on redirects, raw error logging, or retries.
    try:
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        with urllib.request.build_opener(_NoRedirect()).open(req, timeout=timeout) as response:
            raw = response.read(16 * 1024 * 1024 + 1)
        if len(raw) > 16 * 1024 * 1024:
            raise ValueError('response too large')
        return _json_loads(raw)
    except urllib.error.HTTPError as exc:
        status = exc.code
        try:
            diagnostic = _error_diagnostic(exc.read(65537))
        except Exception:
            diagnostic = 'error_body_unavailable'
        finally:
            exc.close()
        raise HTTPFailure('HTTP operation failed; upstream details suppressed.',
                          http_status=status, diagnostic=diagnostic) from None
    except Exception as exc:
        diagnostic = 'transport:' + type(exc).__name__
        reason = getattr(exc, 'reason', None)
        if isinstance(reason, BaseException):
            diagnostic += '/' + type(reason).__name__
        raise HTTPFailure('HTTP operation failed; upstream details suppressed.', diagnostic=diagnostic) from None


class _LedgerState:
    def __init__(self, path):
        self.lock = threading.RLock()
        self.active = set()
        self.poisoned = False
        self.lock_file = open(str(path) + '.lock', 'a+b')
        os.chmod(str(path) + '.lock', 0o600)
        try:
            fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.lock_file.close()
            raise BudgetError('Ledger is already owned by another process.') from None


class BudgetClient:
    def __init__(self, *, api_key, ledger_path, budget_usd='20', max_calls=80,
                 timeout=90, transport=None):
        if not isinstance(api_key, str) or not api_key.strip() or any(c in api_key for c in '\r\n'):
            raise BudgetError('An injected API key is required.')
        try:
            budget = _decimal(budget_usd)
            _integer(max_calls)
        except ValueError:
            raise BudgetError('Invalid budget or call limit.') from None
        if not 0 < budget <= MAX_BUDGET or not 0 < max_calls <= 10000:
            raise BudgetError('Budget must be positive and at most $20; call limit must be 1–10000.')
        if not isinstance(timeout, (int, float)) or not 0 < timeout <= 300:
            raise BudgetError('Timeout must be 1–300 seconds.')
        self._key = api_key
        self._transport = transport or _http
        self._timeout = timeout
        self._preflight_lock = threading.Lock()
        self._preflight_cache = None
        self._preflight_cache_time = 0.0
        self.path = Path(ledger_path).resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.budget = budget
        self.max_calls = max_calls
        with _REGISTRY_LOCK:
            if str(self.path) not in _REGISTRY:
                _REGISTRY[str(self.path)] = _LedgerState(self.path)
            self._state = _REGISTRY[str(self.path)]
        with self._state.lock:
            if not self.path.exists():
                self._save({'version': 1, 'model': MODEL, 'budget_usd': str(budget),
                            'max_calls': max_calls, 'halted': False, 'entries': []})
            ledger = self._read()
            if ledger['budget_usd'] != str(budget) or ledger['max_calls'] != max_calls:
                raise BudgetError('Existing ledger budget/call limits differ; reuse original limits.')
            dirty = False
            for entry in ledger['entries']:
                if entry['state'] == 'pending' and entry['id'] not in self._state.active:
                    entry.update(state='unknown', reason='interrupted_process')
                    ledger['halted'] = True
                    dirty = True
            if dirty:
                self._save(ledger)

    def __repr__(self):
        return '<BudgetClient model=google/gemini-2.5-flash-lite key=REDACTED>'

    def _read(self):
        try:
            d = json.loads(self.path.read_text('utf-8'))
            if (d['version'] != 1 or d['model'] != MODEL or not isinstance(d['halted'], bool)
                    or not isinstance(d['entries'], list) or _decimal(d['budget_usd']) != self.budget
                    or d['max_calls'] != self.max_calls):
                raise ValueError()
            seen = set()
            for e in d['entries']:
                if e['state'] not in ('pending', 'settled', 'unknown') or e['id'] in seen:
                    raise ValueError()
                seen.add(e['id'])
                _decimal(e['reserved_usd'])
                if 'held_usd' in e and _decimal(e['held_usd']) < _decimal(e['reserved_usd']):
                    raise ValueError()
                if e['state'] == 'settled':
                    _decimal(e['actual_usd'])
            return d
        except Exception:
            self._state.poisoned = True
            raise BudgetError('Ledger is unreadable or invalid; client halted.') from None

    def _save(self, ledger):
        tmp = None
        try:
            fd, tmp = tempfile.mkstemp(prefix='.' + self.path.name + '.', dir=self.path.parent)
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                json.dump(ledger, f, ensure_ascii=False, indent=2, allow_nan=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, self.path)
            tmp = None
            directory = os.open(self.path.parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        except Exception:
            self._state.poisoned = True
            raise BudgetError('Cannot durably save ledger; client halted.') from None
        finally:
            if tmp:
                try:
                    os.unlink(tmp)
                except OSError:
                    pass

    def summary(self):
        with self._state.lock:
            d = self._read()
            spent = sum((_decimal(e['actual_usd']) for e in d['entries'] if e['state'] == 'settled'), Decimal(0))
            held = sum((_decimal(e.get('held_usd', e['reserved_usd'])) for e in d['entries'] if e['state'] != 'settled'), Decimal(0))
            return {'model': MODEL, 'budget_usd': str(self.budget), 'spent_usd': str(spent),
                    'held_usd': str(held), 'remaining_usd': str(self.budget - spent - held),
                    'calls': len(d['entries']), 'max_calls': self.max_calls,
                    'halted': d['halted'] or self._state.poisoned,
                    'states': {s: sum(e['state'] == s for e in d['entries']) for s in ('pending', 'settled', 'unknown')}}

    def _get(self, path):
        try:
            return self._transport('GET', BASE + path, {'Accept': 'application/json'}, None, self._timeout)
        except Exception as exc:
            status = exc.http_status if isinstance(exc, BudgetError) else None
            diagnostic = exc.diagnostic if isinstance(exc, BudgetError) else None
            raise PreflightError('Public model preflight failed; no paid call sent.',
                                 http_status=status, diagnostic=diagnostic) from None

    def preflight(self, *, force=False):
        """Public verification, cached for 60s. Use force=True before a batch."""
        with self._preflight_lock:
            now = time.monotonic()
            if not force and self._preflight_cache is not None and now - self._preflight_cache_time < 60:
                return copy.deepcopy(self._preflight_cache)
            self._preflight_cache = None
            result = self._fetch_preflight()
            self._preflight_cache = result
            self._preflight_cache_time = time.monotonic()
            return copy.deepcopy(result)

    def _fetch_preflight(self):
        """Read public APIs without an Authorization header. Never calls inference."""
        try:
            catalog = self._get('/models')['data']
            matching = [m for m in catalog if m.get('id') == MODEL]
            if len(matching) != 1:
                raise ValueError()
            model = matching[0]
            if model.get('canonical_slug') != MODEL or model.get('expiration_date') is not None:
                raise ValueError()
            params = {'max_tokens', 'response_format', 'structured_outputs', 'reasoning', 'temperature'}
            if not params.issubset(model.get('supported_parameters', [])):
                raise ValueError()
            if (_decimal(model['pricing']['prompt']) != INPUT_RATE
                    or _decimal(model['pricing']['completion']) != OUTPUT_RATE
                    or model.get('reasoning', {}).get('mandatory') is True):
                raise ValueError()
            endpoints = self._get('/models/' + MODEL + '/endpoints')['data']['endpoints']
            zdr = self._get('/endpoints/zdr')['data']
            zdr_tags = {e['tag'] for e in zdr if e.get('model_id') == MODEL and e.get('status') == 0}
            eligible = []
            for e in endpoints:
                p = e['pricing']
                if (e.get('status') == 0 and e.get('tag') in zdr_tags
                        and e.get('tag') in ('google-vertex', 'google-vertex/eu')
                        and params.issubset(e.get('supported_parameters', []))
                        and _decimal(p['prompt']) <= INPUT_RATE
                        and _decimal(p['completion']) <= OUTPUT_RATE
                        and _decimal(p.get('internal_reasoning', '0')) <= OUTPUT_RATE
                        and _decimal(p.get('request', '0')) == 0):
                    eligible.append(e)
            if not eligible:
                raise ValueError()
            return {'model': MODEL, 'canonical_slug': model['canonical_slug'],
                    'input_usd_per_million': '0.10', 'output_usd_per_million': '0.40',
                    'provider_tags': sorted(e['tag'] for e in eligible),
                    'context_length': min(_integer(e['context_length']) for e in eligible),
                    'max_completion_tokens': min(_integer(e['max_completion_tokens']) for e in eligible),
                    'verified_at_unix': int(time.time())}
        except PreflightError:
            raise
        except Exception:
            raise PreflightError('Model identity, price, capacity, or privacy capability changed; no paid call sent.') from None

    def _reserve(self, input_bound, max_tokens, metadata):
        reservation = Decimal(input_bound) * INPUT_RATE + Decimal(max_tokens) * OUTPUT_RATE
        with self._state.lock:
            d = self._read()
            if d['halted'] or self._state.poisoned or any(e['state'] == 'unknown' for e in d['entries']):
                raise BudgetError('Client halted by unresolved request or ledger failure.')
            exposure = sum((_decimal(e['actual_usd'] if e['state'] == 'settled' else e['reserved_usd']) for e in d['entries']), Decimal(0))
            if len(d['entries']) >= self.max_calls:
                raise BudgetError('Maximum paid call count reached.')
            if exposure + reservation > self.budget:
                raise BudgetError('Conservative request reservation exceeds remaining budget.')
            rid = str(uuid.uuid4())
            d['entries'].append({'id': rid, 'state': 'pending', 'reserved_usd': str(reservation),
                                 'created_at_unix': int(time.time()), 'input_token_bound': input_bound,
                                 'max_tokens': max_tokens, 'preflight': metadata})
            self._save(d)
            self._state.active.add(rid)
            return rid, reservation

    def _finish(self, rid, *, actual=None, metadata=None, reason=None, halt=False):
        with self._state.lock:
            try:
                d = self._read()
                e = next(e for e in d['entries'] if e['id'] == rid)
                if e['state'] != 'pending':
                    raise BudgetError('Reservation is not pending.')
                e['completed_at_unix'] = int(time.time())
                if actual is None:
                    e.update(state='unknown', reason=reason or 'unknown_outcome')
                    e['held_usd'] = str(max(_decimal(e['reserved_usd']),
                        _decimal((metadata or {}).get('reported_cost_usd', '0'))))
                    d['halted'] = True
                else:
                    e.update(state='settled', actual_usd=str(actual), outcome=reason or 'accepted')
                if metadata:
                    e['metadata'] = metadata
                d['halted'] = d['halted'] or halt
                self._save(d)
            finally:
                self._state.active.discard(rid)

    def chat(self, *, messages, max_tokens, json_schema=None, schema_name='plainvoice', temperature=0.7):
        """One bounded call. Raises safe errors; never retries. Returns ChatResult."""
        try:
            _integer(max_tokens)
            if not max_tokens or not isinstance(messages, list) or not messages:
                raise ValueError()
            clean_messages = []
            for m in messages:
                if not isinstance(m, dict) or set(m) != {'role', 'content'}:
                    raise ValueError()
                if m['role'] not in ('system', 'user', 'assistant') or not isinstance(m['content'], str):
                    raise ValueError()
                clean_messages.append(dict(m))
            if isinstance(temperature, bool) or not isinstance(temperature, (int, float)) or not 0 <= temperature <= 2:
                raise ValueError()
            if json_schema is not None:
                if not isinstance(json_schema, dict) or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', schema_name):
                    raise ValueError()
                # Freeze caller-owned containers before reservation/concurrent work.
                schema = json.loads(_dump(json_schema))
            else:
                schema = None
        except Exception:
            raise BudgetError('Invalid text messages, token limit, temperature, or JSON schema.') from None
        if self.summary()['halted']:
            raise BudgetError('Client halted by unresolved request or ledger failure.')
        verified = self.preflight()
        if max_tokens > verified['max_completion_tokens']:
            raise BudgetError('Output cap exceeds verified endpoint capacity.')
        body = {'model': MODEL, 'messages': clean_messages, 'max_tokens': max_tokens,
                'temperature': temperature, 'stream': False,
                'reasoning': {'enabled': False},
                'provider': {'only': verified['provider_tags'], 'allow_fallbacks': False,
                             'require_parameters': True, 'data_collection': 'deny', 'zdr': True,
                             'max_price': {'prompt': 0.10, 'completion': 0.40}}}
        if schema is not None:
            body['response_format'] = {'type': 'json_schema', 'json_schema':
                                       {'name': schema_name, 'strict': True, 'schema': schema}}
        encoded = _dump(body)
        # Every UTF-8 byte is charged as a whole prompt token, plus framing room.
        # This deliberately overestimates normal EN/ZH text and JSON schemas.
        bound = len(encoded) + 4096
        if bound + max_tokens > verified['context_length']:
            raise BudgetError('Conservative input/output bound exceeds context capacity.')
        rid, reserved = self._reserve(bound, max_tokens, verified)
        start = time.monotonic()
        try:
            response = self._transport('POST', BASE + '/chat/completions',
                                       {'Authorization': 'Bearer ' + self._key,
                                        'Content-Type': 'application/json',
                                        'Accept': 'application/json'}, encoded, self._timeout)
        except BaseException as exc:
            status = exc.http_status if isinstance(exc, BudgetError) else None
            diagnostic = exc.diagnostic if isinstance(exc, BudgetError) else None
            safe = {'http_status': status} if status is not None else {}
            if diagnostic:
                safe['http_diagnostic'] = diagnostic
            self._finish(rid, metadata=safe, reason='transport_or_interruption')
            suffix = (' HTTP status ' + str(status) + '.') if status is not None else ''
            if diagnostic:
                suffix += ' ' + diagnostic
            raise UnknownOutcome('Request outcome/cost unknown; reservation held and client halted.' + suffix,
                                 http_status=status, diagnostic=diagnostic) from None
        elapsed = round(time.monotonic() - start, 3)
        metadata = {'latency_seconds': elapsed}
        try:
            if not isinstance(response, dict) or 'error' in response:
                raise ValueError()
            usage = response['usage']
            actual = _decimal(usage['cost'])
            prompt_tokens = _integer(usage['prompt_tokens'])
            completion_tokens = _integer(usage['completion_tokens'])
            generation = _safe_id(response.get('id'))
            provider = _safe_id(response.get('provider'))
            model = _safe_id(response.get('model'))
            if (not generation or not generation.startswith('gen-')
                    or not provider or not model):
                raise ValueError()
            choices = response['choices']
            if not isinstance(choices, list) or len(choices) != 1:
                raise ValueError()
            choice = choices[0]
            finish = _safe_id(choice.get('finish_reason'))
            if not finish or not isinstance(choice.get('message'), dict):
                raise ValueError()
            metadata.update(model=model if model == MODEL else 'unexpected_model',
                            provider=provider if provider in ('Google', 'Google Vertex', 'Google Vertex (EU)') else 'unexpected_provider',
                            generation_id=generation,
                            finish_reason=finish if finish in ('stop', 'length', 'tool_calls', 'content_filter', 'error') else 'unexpected_finish',
                            prompt_tokens=prompt_tokens,
                            completion_tokens=completion_tokens, cost_usd=str(actual))
            for key, source, subkey in [('reasoning_tokens', 'completion_tokens_details', 'reasoning_tokens'),
                                        ('cached_tokens', 'prompt_tokens_details', 'cached_tokens')]:
                if isinstance(usage.get(source), dict) and subkey in usage[source]:
                    metadata[key] = _integer(usage[source][subkey])
            if actual > reserved or prompt_tokens > bound or completion_tokens > max_tokens:
                metadata['reported_cost_usd'] = str(actual)
                self._finish(rid, metadata=metadata, reason='reservation_bound_violation')
                raise UnknownOutcome('Provider exceeded a verified reservation bound; client halted.')
        except UnknownOutcome:
            raise
        except Exception:
            self._finish(rid, metadata=metadata, reason='missing_or_invalid_accounting')
            raise UnknownOutcome('Response accounting/outcome incomplete; reservation held and client halted.') from None
        rejection = None
        halt = False
        parsed = None
        message = choice['message']
        content = message.get('content')
        if model != MODEL:
            rejection, halt = 'unexpected_model', True
        elif provider not in ('Google', 'Google Vertex', 'Google Vertex (EU)'):
            rejection, halt = 'unexpected_provider', True
        elif message.get('refusal') or finish in ('content_filter', 'error'):
            rejection = 'refusal_or_filter'
        elif finish != 'stop':
            rejection = 'truncated_or_nonfinal'
        elif not isinstance(content, str) or not content.strip():
            rejection = 'empty_or_invalid_content'
        elif schema is not None:
            try:
                parsed = _json_loads(content)
            except Exception:
                rejection = 'invalid_json'
        self._finish(rid, actual=actual, metadata=metadata, reason=rejection, halt=halt)
        if rejection:
            raise RejectedResponse('Paid response rejected: ' + rejection + '; charge recorded.')
        return ChatResult(content=content, parsed=parsed,
                          metadata={**metadata, 'ledger_id': rid, 'reserved_usd': str(reserved)})

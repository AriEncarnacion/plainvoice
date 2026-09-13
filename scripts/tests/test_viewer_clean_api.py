"""Real loopback API tests for view isolation, review hashes, and read-only access."""
from contextlib import closing
import hashlib
import http.client
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from serve_data_viewer import handler


def build_database(path, view):
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {'id': 'same-id', 'collection': 'samples', 'language': 'en', 'pair_type': 'rewrite',
              'title': 'A sample', 'left': {'text': 'Body only' if view == 'clean' else 'title: Metadata\n\nBody only'},
              'right': {'text': 'AI body'}, 'alternatives': [], 'content_hash': view + '-hash'}
    deletion = {'id': 'deletion-id', 'collection': 'edits', 'language': 'zh', 'pair_type': 'rewrite',
                'title': 'Deletion', 'left': {'text': '删除内容'}, 'right': {'text': ''},
                'alternatives': [], 'content_hash': view + '-deletion-hash'}
    unpaired = {'id': 'unpaired-id', 'collection': 'unpaired', 'language': 'en', 'pair_type': 'unpaired',
                'title': 'Missing counterpart', 'left': {'text': 'Original only'}, 'right': None,
                'alternatives': [], 'content_hash': view + '-unpaired-hash'}
    with closing(sqlite3.connect(path)) as db:
        db.executescript('''
          CREATE TABLE records(rid INTEGER PRIMARY KEY,id TEXT UNIQUE,collection TEXT,language TEXT,
                               pair_type TEXT,title TEXT,hash TEXT,search_text TEXT,payload BLOB);
          CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT);
          CREATE VIRTUAL TABLE search USING fts5(search_text,content='records',content_rowid='rid');
        ''')
        db.execute('INSERT INTO metadata VALUES (?,?)', ('catalog', json.dumps({'mode': 'local', 'label': view})))
        for row in (record, deletion, unpaired):
            search_text = (row['left']['text'] + '\n' + (row.get('right') or {}).get('text', '')).lower()
            cur = db.execute('INSERT INTO records(id,collection,language,pair_type,title,hash,search_text,payload) VALUES(?,?,?,?,?,?,?,?)',
                             (row['id'], row['collection'], row['language'], row['pair_type'], row['title'],
                              row['content_hash'], search_text, zlib.compress(json.dumps(row).encode())))
            db.execute('INSERT INTO search(rowid,search_text) VALUES(?,?)', (cur.lastrowid, search_text))
        if view == 'clean':
            db.execute('ALTER TABLE records ADD COLUMN quality_status TEXT')
            db.execute("UPDATE records SET quality_status = CASE id WHEN 'same-id' THEN 'review_candidate' WHEN 'deletion-id' THEN 'quarantined' ELSE 'archive_only' END")
            db.execute('CREATE TABLE cleaning_audits(record_id TEXT PRIMARY KEY,payload BLOB)')
            db.execute('INSERT INTO cleaning_audits VALUES (?,?)', ('same-id', zlib.compress(json.dumps({
                'record_id': 'same-id', 'source_content_hash': 'raw-hash', 'changes': ['metadata_removed'],
            }).encode())))
        db.commit()


class CleanViewerAPITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.raw = self.root / 'data-viewer' / 'review.sqlite'
        self.clean = self.root / 'clean-text-v1' / 'review.sqlite'
        self.assets = self.root / 'assets'
        self.assets.mkdir()
        (self.assets / 'index.html').write_text('<html>Viewer</html>')
        (self.root / 'private.txt').write_text('not served')
        (self.assets / 'outside.txt').symlink_to(self.root / 'private.txt')
        build_database(self.raw, 'raw')
        build_database(self.clean, 'clean')
        self.raw_digest = hashlib.sha256(self.raw.read_bytes()).hexdigest()
        self.clean_digest = hashlib.sha256(self.clean.read_bytes()).hexdigest()
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), handler(self.raw, self.assets, 0))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.assertEqual(hashlib.sha256(self.raw.read_bytes()).hexdigest(), self.raw_digest)
        if self.clean.exists():
            self.assertEqual(hashlib.sha256(self.clean.read_bytes()).hexdigest(), self.clean_digest)
        self.temp.cleanup()

    def request(self, path, body=None, headers=None, method=None):
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=3)
        try:
            raw = None if body is None else json.dumps(body).encode()
            connection.request(method or ('GET' if body is None else 'POST'), path, body=raw, headers=headers or {})
            response = connection.getresponse()
            payload = response.read()
            result = json.loads(payload) if response.getheader('Content-Type', '').startswith('application/json') else payload
            return response.status, result
        finally:
            connection.close()

    def test_catalog_defaults_to_clean_and_explicit_raw_catalog_is_separate(self):
        status, catalog = self.request('/api/catalog')
        self.assertEqual(status, 200)
        self.assertEqual((catalog['label'], catalog['view'], catalog['default_view']), ('clean', 'clean', 'clean'))
        self.assertEqual(catalog['available_views'], ['clean', 'raw'])
        status, raw = self.request('/api/catalog?view=raw')
        self.assertEqual(status, 200)
        self.assertEqual(raw['label'], 'raw')
        self.assertEqual(raw['view'], 'raw')
        self.assertEqual(raw['default_view'], 'clean')

    def test_record_body_and_hash_follow_selected_view(self):
        _, clean = self.request('/api/record?id=same-id')
        _, raw = self.request('/api/record?id=same-id&view=raw')
        self.assertEqual(clean['left']['text'], 'Body only')
        self.assertIn('title:', raw['left']['text'])
        self.assertEqual(raw['content_hash'], 'raw-hash')
        self.assertEqual(clean['content_hash'], 'clean-hash')
        self.assertEqual(self.request('/api/record?id=missing')[0], 404)

    def test_search_uses_selected_database(self):
        _, raw = self.request('/api/records?q=metadata&view=raw')
        _, clean = self.request('/api/records?q=metadata')
        self.assertEqual(raw['total'], 1)
        self.assertEqual(clean['total'], 0)
        self.assertEqual(raw['view'], 'raw')
        self.assertEqual(clean['view'], 'clean')
        _, post = self.request('/api/query', {'view': 'raw', 'q': 'metadata', 'collection': 'samples'})
        self.assertEqual(post['total'], 1)
        self.assertEqual(post['records'][0]['content_hash'], 'raw-hash')
        _, chinese = self.request('/api/query', {'view': 'clean', 'q': '删除', 'language': 'zh'})
        self.assertEqual(chinese['total'], 1)

    def test_raw_reviews_remain_raw_and_do_not_approve_changed_clean_text(self):
        review = {'id': 'same-id', 'content_hash': 'raw-hash', 'decision': 'keep'}
        for view, count in [('raw', 1), ('clean', 0)]:
            status, data = self.request('/api/query', {'view': view, 'reviews': [review], 'review_filter': 'keep'})
            self.assertEqual(status, 200)
            self.assertEqual(data['total'], count)
        _, cleaned = self.request('/api/query', {'view': 'clean', 'reviews': [review], 'review_filter': 'unreviewed'})
        self.assertEqual(cleaned['total'], 3)

    def test_audit_requires_clean_and_is_record_scoped(self):
        status, audit = self.request('/api/cleaning-audit?id=same-id')
        self.assertEqual(status, 200)
        self.assertEqual(audit['source_content_hash'], 'raw-hash')
        self.assertEqual(audit['changes'], ['metadata_removed'])
        status, unchanged = self.request('/api/cleaning-audit?id=unpaired-id&view=clean')
        self.assertEqual(status, 200)
        self.assertEqual(unchanged, {'id': 'unpaired-id', 'fields': {},
                                     'message': 'No formatting changes or warnings were recorded.'})
        self.assertEqual(self.request('/api/cleaning-audit?id=missing&view=clean')[0], 404)
        self.assertEqual(self.request('/api/cleaning-audit?id=same-id&view=raw')[0], 400)

    def test_invalid_views_rejected_on_every_data_endpoint(self):
        for endpoint in ('catalog', 'record', 'records', 'cleaning-audit'):
            for view in ('unknown', ''):
                with self.subTest(endpoint=endpoint, view=view):
                    self.assertEqual(self.request('/api/' + endpoint + '?view=' + view)[0], 400)
        for view in ('unknown', '', None, ['raw']):
            with self.subTest(post_view=view):
                self.assertEqual(self.request('/api/query', {'view': view})[0], 400)

    def test_missing_clean_falls_back_only_when_not_explicitly_requested(self):
        self.clean.unlink()
        status, catalog = self.request('/api/catalog')
        self.assertEqual(status, 200)
        self.assertEqual(catalog['available_views'], ['raw'])
        self.assertEqual(catalog['default_view'], 'raw')
        self.assertEqual(catalog['view'], 'raw')
        self.assertEqual(self.request('/api/record?id=same-id')[1]['content_hash'], 'raw-hash')
        for endpoint in ('catalog', 'record', 'records', 'cleaning-audit'):
            self.assertEqual(self.request('/api/' + endpoint + '?view=clean')[0], 400)
        self.assertEqual(self.request('/api/query', {'view': 'clean'})[0], 400)
        self.assertEqual(self.request('/api/cleaning-audit?id=same-id')[0], 400)

    def test_empty_deletion_and_absent_target_remain_distinct(self):
        for view in ('raw', 'clean'):
            _, deletion = self.request('/api/record?id=deletion-id&view=' + view)
            _, unpaired = self.request('/api/record?id=unpaired-id&view=' + view)
            self.assertEqual(deletion['right'], {'text': ''})
            self.assertIsNone(unpaired['right'])

    def test_security_rejects_wrong_host_cross_origin_and_asset_escape(self):
        self.assertEqual(self.request('/api/catalog', headers={'Host': 'evil.example'})[0], 403)
        self.assertEqual(self.request('/api/query', {}, {'Origin': 'https://evil.example'})[0], 403)
        self.assertEqual(self.request('/../private.txt')[0], 404)
        self.assertEqual(self.request('/outside.txt')[0], 404)
        self.assertEqual(self.request('/api/unknown')[0], 404)
        self.assertEqual(self.request('/')[0], 200)

    def test_malformed_query_is_rejected_without_stopping_server(self):
        self.assertEqual(self.request('/api/query', [1, 2])[0], 400)
        self.assertEqual(self.request('/api/query', {'limit': 'invalid'})[0], 400)
        self.assertEqual(self.request('/api/query', method='POST', headers={'Content-Length': '-1'})[0], 400)
        self.assertEqual(self.request('/api/catalog')[0], 200)

    def test_quality_status_filter_and_list_metadata_are_clean_only(self):
        for quality_status, expected in [('review_candidate', 'same-id'), ('quarantined', 'deletion-id'), ('archive_only', 'unpaired-id')]:
            with self.subTest(quality_status=quality_status):
                status, data = self.request('/api/records?view=clean&quality_status=' + quality_status)
                self.assertEqual(status, 200)
                self.assertEqual(data['total'], 1)
                self.assertEqual(data['records'][0]['id'], expected)
                self.assertEqual(data['records'][0]['quality_status'], quality_status)
                status, post = self.request('/api/query', {'quality_status': quality_status})
                self.assertEqual(status, 200)
                self.assertEqual(post['total'], 1)
        self.assertEqual(self.request('/api/records?view=raw&quality_status=review_candidate')[0], 400)
        self.assertEqual(self.request('/api/query', {'view': 'raw', 'quality_status': 'quarantined'})[0], 400)
        self.assertEqual(self.request('/api/query', {'quality_status': 'unknown'})[0], 400)
        _, raw = self.request('/api/records?view=raw&quality_status=')
        self.assertTrue(all(row['quality_status'] is None for row in raw['records']))

    def test_explicit_custom_clean_path_is_used(self):
        custom = self.root / 'custom.sqlite'
        self.clean.rename(custom)
        self.server.RequestHandlerClass = handler(self.raw, self.assets, 0, custom)
        _, catalog = self.request('/api/catalog')
        self.assertEqual(catalog['view'], 'clean')
        self.assertEqual(self.request('/api/record?id=same-id')[1]['content_hash'], 'clean-hash')
        self.assertEqual(hashlib.sha256(custom.read_bytes()).hexdigest(), self.clean_digest)


if __name__ == '__main__':
    unittest.main()

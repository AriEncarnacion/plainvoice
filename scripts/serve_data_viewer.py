#!/usr/bin/env python3
"""Read-only loopback server for Plainvoice's raw corpus and cleaned-text view."""
import argparse
from contextlib import contextmanager
import json
import mimetypes
from pathlib import Path
import re
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse
import zlib


def handler(database, assets, port, clean_database=None):
    database = Path(database).expanduser().resolve()
    assets = Path(assets).expanduser().resolve()
    clean_database = (
        Path(clean_database).expanduser().resolve() if clean_database is not None
        else database.parent.parent / 'clean-text-v1' / 'review.sqlite'
    )

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass

        def available_views(self):
            return ['clean', 'raw'] if clean_database.is_file() else ['raw']

        def select_view(self, params):
            available = self.available_views()
            view = params.get('view', available[0])
            if view not in ('clean', 'raw'):
                raise ValueError('view must be clean or raw')
            if view not in available:
                raise ValueError('Cleaned database is not available')
            return view

        @contextmanager
        def db(self, view):
            selected = clean_database if view == 'clean' else database
            connection = sqlite3.connect(selected.as_uri() + '?mode=ro', uri=True)
            connection.row_factory = sqlite3.Row
            try:
                yield connection
            finally:
                connection.close()

        def reply(self, data, status=200, kind='application/json; charset=utf-8'):
            raw = data if isinstance(data, bytes) else json.dumps(data, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header('Content-Type', kind)
            self.send_header('Content-Length', str(len(raw)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.end_headers()
            self.wfile.write(raw)

        def loopback_hosts(self):
            # Port 0 is useful for isolated API tests and binds an ephemeral port.
            bound_port = port or self.server.server_port
            return {f'127.0.0.1:{bound_port}', f'localhost:{bound_port}'}

        def trusted(self):
            return self.headers.get('Host') in self.loopback_hosts()

        def do_GET(self):
            if not self.trusted():
                return self.reply({'error': 'Loopback host required'}, 403)
            parsed = urlparse(self.path)
            path = parsed.path
            params = {key: values[0] for key, values in parse_qs(parsed.query, keep_blank_values=True).items()}
            try:
                if path == '/api/catalog':
                    view = self.select_view(params)
                    with self.db(view) as db:
                        result = json.loads(db.execute("SELECT value FROM metadata WHERE key='catalog'").fetchone()[0])
                    available = self.available_views()
                    result.update(available_views=available, default_view=available[0], view=view)
                    return self.reply(result)
                if path == '/api/record':
                    view = self.select_view(params)
                    with self.db(view) as db:
                        row = db.execute('SELECT payload FROM records WHERE id=?', (params.get('id', ''),)).fetchone()
                    return self.reply(zlib.decompress(row[0]) if row else {'error': 'Record not found'}, 200 if row else 404)
                if path == '/api/records':
                    return self.query(params)
                if path == '/api/cleaning-audit':
                    view = self.select_view(params)
                    if view != 'clean':
                        raise ValueError('Cleaning audit is only available in clean view')
                    record_id = params.get('id', '')
                    with self.db(view) as db:
                        row = db.execute('SELECT payload FROM cleaning_audits WHERE record_id=?', (record_id,)).fetchone()
                        if row is None:
                            exists = db.execute('SELECT 1 FROM records WHERE id=?', (record_id,)).fetchone()
                    if row is not None:
                        return self.reply(zlib.decompress(row[0]))
                    if exists:
                        return self.reply({'id': record_id, 'fields': {},
                                           'message': 'No formatting changes or warnings were recorded.'})
                    return self.reply({'error': 'Record not found'}, 404)
                if path.startswith('/api/'):
                    return self.reply({'error': 'Unknown endpoint'}, 404)
                target = (assets / ('index.html' if path == '/' else path.lstrip('/'))).resolve()
                if not target.is_relative_to(assets) or not target.is_file():
                    return self.reply({'error': 'Not found'}, 404)
                content_type = mimetypes.guess_type(target)[0] or 'application/octet-stream'
                if target.suffix in ('.js', '.html', '.css', '.json'):
                    content_type += '; charset=utf-8'
                return self.reply(target.read_bytes(), kind=content_type)
            except (ValueError, sqlite3.Error, KeyError, TypeError, zlib.error) as exc:
                self.reply({'error': str(exc)}, 400)

        def do_POST(self):
            if not self.trusted():
                return self.reply({'error': 'Loopback host required'}, 403)
            origin = self.headers.get('Origin')
            if origin and origin not in {'http://' + host for host in self.loopback_hosts()}:
                return self.reply({'error': 'Same-origin requests only'}, 403)
            if self.path != '/api/query':
                return self.reply({'error': 'Unknown endpoint'}, 404)
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if length < 0:
                    raise ValueError('Content-Length must be nonnegative')
                if length > 10_000_000:
                    return self.reply({'error': 'Query too large'}, 413)
                return self.query(json.loads(self.rfile.read(length)))
            except (ValueError, sqlite3.Error, KeyError, TypeError) as exc:
                self.reply({'error': str(exc)}, 400)

        def query(self, params):
            if not isinstance(params, dict):
                raise ValueError('Query must be a JSON object')
            view = self.select_view(params)
            quality_status = params.get('quality_status', '')
            if quality_status:
                if view != 'clean':
                    raise ValueError('quality_status filtering is only available in clean view')
                if quality_status not in ('archive_only', 'review_candidate', 'quarantined'):
                    raise ValueError('Invalid quality_status')
            where, args = [], []
            offset = max(0, int(params.get('offset', 0)))
            limit = min(100, max(1, int(params.get('limit', 40))))
            for key in ('collection', 'language', 'pair_type'):
                if params.get(key):
                    where.append(f'r.{key}=?')
                    args.append(str(params[key]))
            if quality_status:
                where.append('r.quality_status=?')
                args.append(quality_status)
            query = str(params.get('q', '')).strip()[:300]
            if query:
                if re.search(r'[\u3040-\u30ff\u3400-\u9fff]', query):
                    where.append('instr(r.search_text,?)>0')
                    args.append(query.lower())
                else:
                    terms = re.findall(r'\w+', query)
                    if terms:
                        where.append('r.rid IN (SELECT rowid FROM search WHERE search MATCH ?)')
                        args.append(' AND '.join('"' + term + '"' for term in terms))
            with self.db(view) as db:
                review_filter = params.get('review_filter', '')
                reviews = params.get('reviews', [])
                if review_filter:
                    db.execute('CREATE TEMP TABLE reviewed(id TEXT,hash TEXT,decision TEXT)')
                    db.executemany('INSERT INTO reviewed VALUES (?,?,?)', [
                        (str(item['id']), str(item['content_hash']), str(item.get('decision', '')))
                        for item in reviews
                    ])
                    exists = 'EXISTS (SELECT 1 FROM reviewed v WHERE v.id=r.id AND v.hash=r.hash'
                    if review_filter == 'unreviewed':
                        where.append('NOT ' + exists + ')')
                    elif review_filter == 'reviewed':
                        where.append(exists + ')')
                    elif review_filter in ('keep', 'reject'):
                        where.append(exists + ' AND v.decision=?)')
                        args.append(review_filter)
                condition = ' AND '.join(where) or '1'
                count = db.execute('SELECT count(*) FROM records r WHERE ' + condition, args).fetchone()[0]
                quality_column = 'r.quality_status' if view == 'clean' else 'NULL AS quality_status'
                rows = db.execute(
                    'SELECT r.id,r.collection,r.language,r.pair_type,r.title,r.hash AS content_hash,'
                    + quality_column + ' FROM records r WHERE ' + condition + ' ORDER BY r.rid LIMIT ? OFFSET ?',
                    args + [limit, offset],
                ).fetchall()
            self.reply({'total': count, 'offset': offset, 'limit': limit, 'view': view,
                        'records': [dict(row) for row in rows]})

    return Handler


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', required=True, type=Path, help='Original raw viewer database')
    parser.add_argument('--clean-database', type=Path,
                        help='Cleaned view; defaults to ../clean-text-v1/review.sqlite beside the raw data-viewer directory')
    parser.add_argument('--assets', type=Path, default=Path(__file__).resolve().parents[1] / 'dist')
    parser.add_argument('--port', type=int, default=8876)
    args = parser.parse_args()
    if not args.database.expanduser().is_file():
        parser.error('Database missing. Run scripts/build_data_viewer.py first.')
    server = ThreadingHTTPServer(('127.0.0.1', args.port), handler(
        args.database, args.assets, args.port, args.clean_database,
    ))
    print(f'Plainvoice full data viewer: http://127.0.0.1:{server.server_port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

#!/usr/bin/env python3
"""Read-only loopback server for the complete Plainvoice corpus. No uploads or network access."""
import argparse,json,mimetypes,re,sqlite3,zlib
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse,parse_qs

def handler(database,assets,port):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,fmt,*args):pass
        def db(self):
            db=sqlite3.connect(database.as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row;return db
        def reply(self,data,status=200,kind='application/json; charset=utf-8'):
            raw=data if isinstance(data,bytes) else json.dumps(data,ensure_ascii=False).encode()
            self.send_response(status);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(raw)
        def trusted(self):return self.headers.get('Host') in {f'127.0.0.1:{port}',f'localhost:{port}'}
        def do_GET(self):
            if not self.trusted():return self.reply({'error':'Loopback host required'},403)
            parsed=urlparse(self.path);path=parsed.path;params={k:v[0] for k,v in parse_qs(parsed.query).items()}
            try:
                if path=='/api/catalog':
                    with self.db() as db:result=json.loads(db.execute("SELECT value FROM metadata WHERE key='catalog'").fetchone()[0])
                    return self.reply(result)
                if path=='/api/record':
                    with self.db() as db:row=db.execute('SELECT payload FROM records WHERE id=?',(params.get('id',''),)).fetchone()
                    return self.reply(zlib.decompress(row[0]) if row else {'error':'Record not found'},200 if row else 404)
                if path=='/api/records':return self.query(params)
                if path.startswith('/api/'):return self.reply({'error':'Unknown endpoint'},404)
                target=(assets/('index.html' if path=='/' else path.lstrip('/'))).resolve()
                if not target.is_relative_to(assets) or not target.is_file():return self.reply({'error':'Not found'},404)
                return self.reply(target.read_bytes(),kind=(mimetypes.guess_type(target)[0] or 'application/octet-stream')+('; charset=utf-8' if target.suffix in ['.js','.html','.css','.json'] else ''))
            except (ValueError,sqlite3.Error,KeyError) as e:self.reply({'error':str(e)},400)
        def do_POST(self):
            if not self.trusted():return self.reply({'error':'Loopback host required'},403)
            origin=self.headers.get('Origin')
            if origin and origin not in {f'http://127.0.0.1:{port}',f'http://localhost:{port}'}:return self.reply({'error':'Same-origin requests only'},403)
            if self.path!='/api/query':return self.reply({'error':'Unknown endpoint'},404)
            try:
                length=int(self.headers.get('Content-Length','0'))
                if length>10_000_000:return self.reply({'error':'Query too large'},413)
                return self.query(json.loads(self.rfile.read(length)))
            except (ValueError,sqlite3.Error,KeyError,TypeError) as e:self.reply({'error':str(e)},400)
        def query(self,p):
            where=[];args=[];offset=max(0,int(p.get('offset',0)));limit=min(100,max(1,int(p.get('limit',40))))
            for key in ['collection','language','pair_type']:
                if p.get(key):where.append(f'r.{key}=?');args.append(str(p[key]))
            q=str(p.get('q','')).strip()[:300]
            if q:
                if re.search(r'[\u3040-\u30ff\u3400-\u9fff]',q):where.append('instr(r.search_text,?)>0');args.append(q.lower())
                else:
                    terms=re.findall(r'\w+',q)
                    if terms:where.append('r.rid IN (SELECT rowid FROM search WHERE search MATCH ?)');args.append(' AND '.join('"'+t+'"' for t in terms))
            with self.db() as db:
                review_filter=p.get('review_filter','');reviews=p.get('reviews',[])
                if review_filter:
                    db.execute('CREATE TEMP TABLE reviewed(id TEXT,hash TEXT,decision TEXT)')
                    db.executemany('INSERT INTO reviewed VALUES (?,?,?)',[(str(x['id']),str(x['content_hash']),str(x.get('decision',''))) for x in reviews])
                    exists='EXISTS (SELECT 1 FROM reviewed v WHERE v.id=r.id AND v.hash=r.hash'
                    if review_filter=='unreviewed':where.append('NOT '+exists+')')
                    elif review_filter=='reviewed':where.append(exists+')')
                    elif review_filter in ['keep','reject']:where.append(exists+' AND v.decision=?)');args.append(review_filter)
                condition=' AND '.join(where) or '1'
                count=db.execute('SELECT count(*) FROM records r WHERE '+condition,args).fetchone()[0]
                rows=db.execute('SELECT r.id,r.collection,r.language,r.pair_type,r.title,r.hash AS content_hash FROM records r WHERE '+condition+' ORDER BY r.rid LIMIT ? OFFSET ?',args+[limit,offset]).fetchall()
            self.reply({'total':count,'offset':offset,'limit':limit,'records':[dict(x) for x in rows]})
    return Handler

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--database',required=True,type=Path);p.add_argument('--assets',type=Path,default=Path(__file__).resolve().parents[1]/'dist');p.add_argument('--port',type=int,default=8876);a=p.parse_args()
    if not a.database.expanduser().is_file():p.error('Database missing. Run scripts/build_data_viewer.py first.')
    server=ThreadingHTTPServer(('127.0.0.1',a.port),handler(a.database.expanduser().resolve(),a.assets.resolve(),a.port))
    print(f'Plainvoice full data viewer: http://127.0.0.1:{a.port}',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:server.server_close()

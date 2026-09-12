#!/usr/bin/env python3
"""Stream the complete local download bundle into a searchable review database."""
import argparse, collections, hashlib, json, os, sqlite3, time, zlib
from pathlib import Path
import export_dataset_records, export_other_records

def build(root, output, catalog_path=None, skip_published=False):
    output.parent.mkdir(parents=True, exist_ok=True)
    temp=output.with_suffix('.building.sqlite')
    if temp.exists():temp.unlink()
    db=sqlite3.connect(temp)
    db.executescript('''PRAGMA journal_mode=OFF; PRAGMA synchronous=OFF;
    CREATE TABLE records(rid INTEGER PRIMARY KEY,id TEXT NOT NULL UNIQUE,collection TEXT,language TEXT,pair_type TEXT,family TEXT,title TEXT,hash TEXT,search_text TEXT,payload BLOB);
    CREATE INDEX collection_records ON records(collection,rid);
    CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT);
    ''')
    counts=collections.Counter();languages=collections.Counter();types=collections.Counter();total=0;started=time.time()
    def emit(row):
        nonlocal total
        for key in ['id','collection','title','left','pair_type','language']:assert key in row,key
        assert row['left'] is not None and isinstance(row['left']['text'],str)
        right=row.get('right');assert right is None or isinstance(right['text'],str)
        canonical=json.dumps(row,ensure_ascii=False,separators=(',',':')).encode()
        row['content_hash']=hashlib.sha256(canonical).hexdigest()
        raw=json.dumps(row,ensure_ascii=False,separators=(',',':')).encode()
        search='\n'.join([row['title'],row['left']['text'],(right or {}).get('text','')]+[x.get('text','') for x in row.get('alternatives',[])]).lower()
        db.execute('INSERT INTO records(id,collection,language,pair_type,family,title,hash,search_text,payload) VALUES (?,?,?,?,?,?,?,?,?)',(row['id'],row['collection'],row['language'],row['pair_type'],row.get('family',''),row['title'],row['content_hash'],search,zlib.compress(raw,1)))
        total+=1;counts[row['collection']]+=1;languages[row['language']]+=1;types[row['pair_type']]+=1
        if total%5000==0:db.commit()
        if total%100000==0:print(json.dumps({'ingested':total,'seconds':round(time.time()-started)}),flush=True)
    other=export_other_records.export(root,emit)
    other_report=export_other_records.export.last_report
    published={'collections':[],'total_records':0}
    if not skip_published:published=export_dataset_records.export(root,emit)
    cols=[]
    for c in other+published['collections']:
        ident=c.get('collection') or c.get('slug') or c.get('id')
        assert ident in counts,(ident,c.keys())
        cols.append({'id':ident,'title':c.get('title') or c.get('collection_title') or ident,'family':c.get('family','agentic-technical'),'count':counts[ident],'description':c.get('description',''),'source_url':c.get('source_url'),'license':c.get('license') or c.get('rights'),'pair_types':c.get('pair_types',{}),'data_local_only':True})
    assert sum(c['count'] for c in cols)==total
    db.commit();print('Building keyword index…',flush=True)
    db.execute("CREATE VIRTUAL TABLE search USING fts5(search_text,content='records',content_rowid='rid',tokenize='unicode61')")
    db.execute("INSERT INTO search(search) VALUES('rebuild')")
    db.execute('CREATE INDEX type_records ON records(pair_type,rid)')
    db.execute('CREATE INDEX language_records ON records(language,rid)')
    catalog={'schema_version':'plainvoice-viewer-1','total_records':total,'collections':cols,'languages':dict(languages),'pair_types':dict(types),'default_collection':'rewrite-article-v2','scope':'all normalized records in the downloaded local bundle','generated_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'mode':'local','search_scope':'Title and all comparison/reference text. Trace/context metadata is viewable separately.'}
    db.execute('INSERT INTO metadata VALUES (?,?)',('catalog',json.dumps(catalog,ensure_ascii=False)))
    db.commit()
    assert db.execute('PRAGMA quick_check').fetchone()[0]=='ok'
    db.close();os.replace(temp,output)
    (output.parent/'source-coverage.json').write_text(json.dumps({'published_datasets':published,'other_collections':other_report},ensure_ascii=False,indent=2)+'\n')
    (output.parent/'catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n')
    if catalog_path:
        public={**catalog,'mode':'catalog','default_collection':'coggen-owid','sample_file':'public-samples.json','local_url':'http://127.0.0.1:8876'}
        catalog_path.parent.mkdir(parents=True,exist_ok=True);catalog_path.write_text(json.dumps(public,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'records':total,'collections':len(cols),'database_bytes':output.stat().st_size,'elapsed_seconds':round(time.time()-started)},ensure_ascii=False),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',required=True,type=Path);p.add_argument('--output',required=True,type=Path);p.add_argument('--public-catalog',type=Path);p.add_argument('--skip-published',action='store_true');a=p.parse_args()
    build(a.root.expanduser().resolve(),a.output.expanduser().resolve(),a.public_catalog,a.skip_published)

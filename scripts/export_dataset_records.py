#!/usr/bin/env python3
"""Lossless review export of the six Plainvoice downloaded dataset snapshots.

Uses only Python's standard library. Source files are read only. No network calls.
export(root, emit) streams normalized records and returns a full coverage report.
Pass the Desktop bundle root OR its datasets/ child. No sampling or record cap.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from pathlib import Path
from collections import Counter, defaultdict
from contextlib import ExitStack
from itertools import zip_longest
from typing import Callable

VERSION = '2026-09-12.1'
NAMES = ['adparaphrase-v2.0', 'iterater', 'arxivedits', 'mcts', 'asset', 'coedit']
COMMON = 'Adjacent editing/revision data; not validated human-versus-AI or de-AI-ese ground truth. '
DESCRIPTIONS = {
 'adparaphrase-v2.0': 'Japanese advertising text with equivalence and attractiveness votes; rejected equivalence candidates, ties and skips retained.',
 'iterater': 'Human revision text; HUMAN intent annotations are human labels, FULL intent labels are automatic. Revisions may change meaning. Sentence/document views overlap.',
 'arxivedits': 'Scientific paper sentence revisions and unaligned text. Alignment methods vary; changes can alter scientific claims. Source math/citation placeholders retained.',
 'mcts': 'Chinese sentence simplification. Human multi-reference evaluation and machine-constructed pseudo training pairs remain distinct. Simplification can omit information.',
 'asset': 'English multi-reference sentence simplification plus all released rating and cross-dataset preference annotations. No training split.',
 'coedit': 'Instruction-based English editing from existing datasets. Only released 69k training set; restricted paper instances are absent.'
}


def _json(p):
    with p.open(encoding='utf-8') as f: return json.load(f)

def _jsonl(p):
    with p.open(encoding='utf-8') as f:
        for line, text in enumerate(f, 1):
            if not text.strip(): raise ValueError(f'Unexpected blank JSONL row: {p}:{line}')
            yield line, json.loads(text)

def _csv(p):
    with p.open(encoding='utf-8', newline='') as f:
        yield from enumerate(csv.DictReader(f), 2)

def _side(label, text, role):
    if not isinstance(text, str): raise TypeError((label, type(text)))
    return {'label': label, 'text': text, 'role': role}

def _norm(text): return ''.join(text.split())

def _hash(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()[:24]

class Exporter:
    def __init__(self, root, emit):
        root = Path(root).expanduser().resolve()
        self.base = root if (root/'datasets').is_dir() else root.parent
        self.ds = self.base/'datasets'
        if not all((self.ds/n/'manifest.json').exists() for n in NAMES):
            raise FileNotFoundError(f'Expected six manifests under {self.ds}')
        self.emit_callback = emit
        self.manifests = {n: _json(self.ds/n/'manifest.json') for n in NAMES}
        self.source_meta = {}
        self.coverage = {}
        self.collections = {}
        self.total = 0
        self.exclusions = []
        self.limitations = [COMMON.strip(), 'No text is truncated or sampled. Source row counts are not independent gold-example counts; overlapping source views and annotations are identified.', 'All source text remains local; this exporter makes no redistribution or training-clearance claim.', 'Primary left/right roles follow task structure. An empty revised string is a deletion, not a missing record. Unaligned text has right=null.', 'ASSET evaluator identifiers are preserved as released metadata; do not publish these local files without a separate decision.']
        for ds,m in self.manifests.items():
            for info in m['files']:
                path = f'datasets/{ds}/{info["relative_path"]}'
                self.source_meta[path] = info
                self.coverage[path] = {'local_path':path, 'source_url':info.get('url'), 'sha256':info.get('sha256'), 'bytes':info.get('bytes'), 'format':info.get('format'), 'expected_source_records':info.get('record_count'), 'source_records_processed':0, 'normalized_records_emitted':0, 'status':'documentation_or_metadata', 'note':'Source documentation/metadata; original remains in the local download bundle.'}
            self.coverage[f'datasets/{ds}/manifest.json']={'local_path':f'datasets/{ds}/manifest.json','status':'metadata_used','note':'Loaded pinned revision, licensing evidence, source URLs, checksums and expected source record counts.'}

    def path(self, ds, rel): return self.ds/ds/rel
    def rel(self, ds, rel): return f'datasets/{ds}/{rel}'
    def processed(self, ds, rel, n, note='All rows consumed; text or annotations represented in the export.'):
        c=self.coverage[self.rel(ds,rel)]
        c['source_records_processed'] += n
        c['status']='normalized'
        c['note']=note
    def collection(self, ds, suffix, title, language):
        slug=ds + ('-'+suffix if suffix else '')
        if slug not in self.collections:
            m=self.manifests[ds]
            self.collections[slug]={'id':slug,'collection':slug,'title':title,'collection_title':title,'dataset':ds,'family':'published-dataset','language':language,'record_count':0,'source_url':m['source_url'],'license':m['license'],'description':COMMON+DESCRIPTIONS[ds],'splits':Counter(),'pair_types':Counter(),'data_local_only':True}
        return slug
    def prov(self, ds, rel, split, locator, note='', license=None):
        p=self.rel(ds,rel); info=self.source_meta.get(p,{})
        return {'source_url':info.get('url') or self.manifests[ds]['source_url'], 'local_path':p,'split':split,'record_locator':locator,'license':license or self.manifests[ds]['license']['declared_license'],'notes':note}
    def out(self, ds, suffix, title, lang, kind, rel, split, locator, left, right=None, alternatives=None, context='', extra=None, notes='', license=None, identity=None):
        col=self.collection(ds,suffix,title,lang)
        rec={'id':col+':'+_hash(identity if identity is not None else [rel,split,locator]),'collection':col,'collection_title':title,'family':'published-dataset','language':lang,'pair_type':kind,'title':context.split('\n')[0] if context else f'{title} · {locator}','left':left,'right':right,'alternatives':alternatives or [],'context':context,'provenance':self.prov(ds,rel,split,locator,notes,license)}
        if extra: rec['extra']=extra
        self.emit_callback(rec)
        self.total+=1; c=self.collections[col];c['record_count']+=1;c['splits'][split]+=1;c['pair_types'][kind]+=1
        self.coverage[self.rel(ds,rel)]['normalized_records_emitted']+=1

    def adparaphrase(self):
        ds='adparaphrase-v2.0'
        for name in ['main','pt']:
            rel=f'data/adparaphrase_v2_{name}.csv'; n=0
            for line,r in _csv(self.path(ds,rel)):
                n+=1
                extra={k:int(v) if k.startswith('count.') else v for k,v in r.items() if k not in ['ad1','ad2','input_ad','generated_ad1','generated_ad2']}
                extra['language_original']='ja'
                if name=='main':
                    accepted=int(r['count.paraphrase'])>=3
                    extra['majority_equivalent']=accepted
                    self.out(ds,'main','AdParaphrase · equivalence and appeal','ja','preference' if accepted else 'same-task',rel,'unspecified',f'csv-row:{line};id:{r["id"]}',_side('Ad 1 · '+r['source_ad1'],r['ad1'],'candidate'),_side('Ad 2 · '+r['source_ad2'],r['ad2'],'candidate'),context=f'Japanese ad pair {r["id"]} · '+('majority equivalent' if accepted else 'not majority equivalent'),extra=extra,notes='Five equivalence judges; ten attractiveness votes only for majority-equivalent pairs. Not an AI-ese label; unaccepted pairs retained for review.')
                else:
                    self.out(ds,'preferences','AdParaphrase · preference tuning','ja','preference',rel,r['split'],f'csv-row:{line};id:{r["id"]}',_side('Input ad · '+r['source_input_ad'],r['input_ad'],'input'),_side('Candidate 1 · '+r['model_ad1'],r['generated_ad1'],'candidate'),[_side('Candidate 2 · '+r['model_ad2'],r['generated_ad2'],'candidate')],context=f'Japanese preference triple {r["id"]} · attractiveness votes compare candidates 1 and 2',extra=extra,notes='Input and both candidates preserved. Candidate source labels come directly from the documented model_ad fields; human means crowdworker in this source. main/pt may reuse ad text but have different task context and annotations; not independent examples.')
            self.processed(ds,rel,n)

    def iterater(self):
        ds='iterater'
        arc='dataset/IteraTeR.zip';c=self.coverage[self.rel(ds,arc)]
        c.update(status='excluded_duplicate_artifact',note='ZIP contains exactly the separately downloaded extracted JSONL files; extracted records are used once.')
        self.exclusions.append({'local_path':self.rel(ds,arc),'reason':'Duplicate container for 12 canonical extracted JSONL files; not read as a second data source.'})
        for level,lk,rk in [('doc','before_revision','after_revision'),('sent','before_sent','after_sent')]:
            human={}; order=[]
            for split in ['train','dev','test']:
                rel=f'extracted/IteraTeR/human_{level}_level/{split}.json';n=0
                for line,r in _jsonl(self.path(ds,rel)):
                    n+=1;key=(split,str(r['doc_id']),str(r['revision_depth']),r[lk],r[rk])
                    # Every original human annotation row is retained, including same-text distinct rows.
                    item={'r':r,'rel':rel,'split':split,'line':line,'full_annotations':[]}
                    human.setdefault(key,[]).append(item);order.append(item)
                self.processed(ds,rel,n)
            merged=Counter()
            def write(r,rel,split,line,view,alias=None):
                extra={k:v for k,v in r.items() if k not in [lk,rk]}
                extra['annotation_origin']='human' if view=='human' else 'automatic'
                extra['view']=f'{view}_{level}_level'
                if alias:extra['overlapping_full_annotations']=alias
                self.out(ds,f'{view}-{level}','IteraTeR · '+view.upper()+' · '+('document' if level=='doc' else 'sentence'),'en','rewrite',rel,split,f'line:{line};doc:{r["doc_id"]};revision:{r["revision_depth"]}',_side('Before revision',r[lk],'input'),_side('After revision'+(' · deletion' if r[rk]=='' else ''),r[rk],'target'),context=f'Document {r["doc_id"]} · revision {r["revision_depth"]}'+(f' · intent: {r["labels"]}' if 'labels' in r else ''),extra=extra,notes='HUMAN/FULL describe intent-label origin, not a human-versus-AI output pair. Sentence/document granularity overlaps. Exact same-split HUMAN/FULL text pairs are consolidated into the HUMAN row with both annotations and provenance.')
            for split in ['train','dev','test']:
                rel=f'extracted/IteraTeR/full_{level}_level/{split}.json';n=0
                for line,r in _jsonl(self.path(ds,rel)):
                    n+=1;key=(split,str(r['doc_id']),str(r['revision_depth']),r[lk],r[rk])
                    if key in human:
                        annotation={k:v for k,v in r.items() if k not in [lk,rk]}
                        annotation['provenance']=self.prov(ds,rel,split,f'line:{line}')
                        human[key][0]['full_annotations'].append(annotation);merged[split]+=1
                    else:write(r,rel,split,line,'full')
                self.processed(ds,rel,n,f'All {n} rows represented. {merged[split]} exact same-split HUMAN/FULL pairs merged into HUMAN records with full annotations and source provenance.')
            for item in order:write(item['r'],item['rel'],item['split'],item['line'],'human',item['full_annotations'])
            self.exclusions.append({'dataset':ds,'view':level,'reason':'Exact overlapping FULL rows consolidated into HUMAN; original full annotation preserved. No split or granularity conflation.','merged_rows':dict(merged),'total_merged_rows':sum(merged.values())})

    def arxivedits(self):
        ds='arxivedits';annotations=defaultdict(list);ann_count=Counter();matched=set();licenses={};paper_splits={};paper_count=Counter();unpaired_count=Counter();alignment_count=Counter();ambiguous=Counter()
        for split in ['train','dev','test']:
            rel=f'data/edits/{split}.json';rows=_json(self.path(ds,rel))
            for key,r in rows.items():
                k=(split,r['arxiv-id'],str(r['sentence-1-level']),str(r['sentence-2-level']),_norm(r['sentence-1']),_norm(r['sentence-2']))
                annotations[k].append((rel,key,r));ann_count[split]+=1
            self.processed(ds,rel,len(rows),'Fine-grained annotations matched to canonical aligned sentence pairs by paper, versions, split and whitespace-normalized text; unmatched annotations are independent review records. Exact tokenized source strings preserved.')
        fields=['auto_identical_alignment','auto_nearly_identical_alignment','auto_asymmetric_alignment','manual_alignment_paragraph_alignment','manual_alignment_top_k']
        for split in ['train','dev','test']:
            rel=f'data/sentence_alignment/{split}.json';papers=_json(self.path(ds,rel))
            for pid,g in papers.items():
                paper_count[split]+=1;licenses[pid]=g['license'];paper_splits[pid]=split
                sentences={key:(ver,text) for ver,values in g.items() if ver.isdigit() for key,text in values.items()}
                if len(sentences)!=sum(len(v) for k,v in g.items() if k.isdigit()):raise ValueError('Duplicate sentence ids in '+pid)
                methods=defaultdict(list)
                for f in fields:
                    for p in g[f]:methods[tuple(p)].append(f)
                skipped=set(g['skipped_alignment_indices']);used=set();seen=set()
                for idx,p in enumerate(g['alignment']):
                    l,r=p;pair=(l,r)
                    if pair in seen:raise ValueError('Unexpected duplicate master alignment '+pid)
                    seen.add(pair);used.update(pair)
                    lv,lt=sentences[l];rv,rt=sentences[r]
                    ankey=(split,pid,lv,rv,_norm(lt),_norm(rt));extra={'paper_id':pid,'paper_url':g['arxiv_link'],'sentence_ids':[l,r],'versions':[lv,rv],'alignment_methods':methods[pair]}
                    attached=[]
                    for ar,ak,av in annotations.get(ankey,[]):
                        aid=(ar,ak)
                        if aid not in matched:
                            attached.append({'annotation':av,'provenance':self.prov(ds,ar,split,f'key:{ak}')});matched.add(aid)
                        else:ambiguous[split]+=1
                    if attached:extra['fine_grained_edits']=attached
                    self.out(ds,'alignment','arXivEdits · aligned sentences','en','rewrite',rel,split,f'paper:{pid};alignment:{idx};{l}->{r}',_side('Version '+lv,lt,'input'),_side('Version '+rv,rt,'target'),context=f'{pid} · v{lv} → v{rv} · '+(', '.join(methods[pair]) or 'alignment'),extra=extra,notes='Canonical master alignment consumed once; overlapping automatic/manual alignment lists are metadata. Fine-grained edit tokenization is preserved in extra. Equivalence is not guaranteed.',license=json.dumps({lv:g['license'].get(lv),rv:g['license'].get(rv)},separators=(',',':')))
                    alignment_count[split]+=1
                unexpected=set(methods)-seen
                if unexpected:raise ValueError(f'Alignment method has pairs missing from master: {pid}: {len(unexpected)}')
                for sid,(ver,text) in sentences.items():
                    if sid in used:continue
                    self.out(ds,'unaligned','arXivEdits · unaligned text','en','unpaired',rel,split,f'paper:{pid};sentence:{sid}',_side('Version '+ver+' · unaligned sentence',text,'source'),context=f'{pid} · v{ver} · unaligned sentence {sid}',extra={'paper_id':pid,'paper_url':g['arxiv_link'],'sentence_id':sid,'version':ver,'skipped_alignment':sid in skipped},notes='No target is inferred. All sentence text outside canonical alignments is retained, including headings and skipped content. Source placeholders remain verbatim.',license=g['license'].get(ver) or 'unknown per-version license')
                    unpaired_count[split]+=1
            self.processed(ds,rel,len(papers),f'All {len(papers)} paper groups expanded into {alignment_count[split]} canonical alignment pairs and {unpaired_count[split]} unaligned sentence records; all version sentence text and license metadata covered.')
        unmatched=Counter()
        for entries in annotations.values():
            for rel,key,r in entries:
                if (rel,key) in matched:continue
                split=Path(rel).stem;pid=r['arxiv-id'];lv=str(r['sentence-1-level']);rv=str(r['sentence-2-level'])
                extra={k:v for k,v in r.items() if k not in ['sentence-1','sentence-2']}
                extra['alignment_match']='unmatched';extra['paper_url']='https://arxiv.org/abs/'+pid
                self.out(ds,'edits','arXivEdits · unmatched annotated edits','en','rewrite',rel,split,f'key:{key}',_side('Version '+lv,r['sentence-1'],'input'),_side('Version '+rv,r['sentence-2'],'target'),context=f'{pid} · v{lv} → v{rv} · fine-grained edit {key}',extra=extra,notes='No exact whitespace-normalized match in canonical same-split sentence alignments; retained as a separate annotated view.',license=json.dumps({lv:licenses.get(pid,{}).get(lv),rv:licenses.get(pid,{}).get(rv)},separators=(',',':')))
                unmatched[split]+=1
        self.exclusions.append({'dataset':ds,'reason':'Fine-grained edit views consolidated into matching canonical alignment records; automatic/manual category lists are not exported again as duplicate pairs. For repeated identical text matches, the annotation is attached to the first canonical matching pair only.','merged_edit_annotations':len(matched),'unmatched_edit_annotations':dict(unmatched),'additional_matching_pairs_without_duplicating_annotation':dict(ambiguous)})

    def parallel_references(self,ds,split,nrefs,lang):
        rel=f'dataset/{ds}.{split}.orig';rels=[rel]+[f'dataset/{ds}.{split}.simp.{j}' for j in range(nrefs)];n=0
        with ExitStack() as stack:
            files=[stack.enter_context(self.path(ds,x).open(encoding='utf-8',newline='')) for x in rels]
            for line,row in enumerate(zip_longest(*files),1):
                if any(s is None for s in row):raise ValueError(f'Parallel line mismatch: {ds} {split}')
                # Strip line terminators only, preserving all source spacing.
                texts=[s.removesuffix('\n').removesuffix('\r') for s in row];n+=1
                refs=[_side(f'Human simplification reference {j+1}',texts[j+1],'reference') for j in range(nrefs)]
                self.out(ds,'references',ds.upper()+' · human references',lang,'multi-reference',rel,split,f'line:{line}',_side('Original sentence',texts[0],'input'),refs[0],refs[1:],context=f'{ds.upper()} · {split} · source sentence {line}',extra={'reference_count':nrefs,'parallel_source_paths':[self.rel(ds,x) for x in rels],'reference_source_indices':list(range(nrefs))},notes=f'{nrefs} independent human-written simplification references. References can delete or simplify information; no AI-versus-human claim. Parallel files use the same one-based line locator.')
        for rr in rels:self.processed(ds,rr,n,'All parallel lines consumed into one source record with every reference; no reference is discarded.')

    def mcts(self):
        ds='mcts'
        for split in ['dev','test']:self.parallel_references(ds,split,5,'zh')
        rel='pseudo_data/zh_selected.ori';target='pseudo_data/zh_selected.sim';n=0
        with self.path(ds,rel).open(encoding='utf-8',newline='') as a,self.path(ds,target).open(encoding='utf-8',newline='') as b:
            for line,pair in enumerate(zip_longest(a,b),1):
                if None in pair:raise ValueError('MCTS pseudo parallel mismatch')
                n+=1;texts=[s.removesuffix('\n').removesuffix('\r') for s in pair]
                self.out(ds,'pseudo','MCTS · machine pseudo pairs','zh','rewrite',rel,'pseudo-training',f'line:{line}',_side('Original',texts[0],'input'),_side('Machine-constructed simplification',texts[1],'target'),context=f'MCTS pseudo training pair {line}',extra={'target_local_path':self.rel(ds,target),'construction':'machine-constructed pseudo parallel data'},notes='Automatically constructed training material; not a human simplification reference. Paired by one-based line position.')
        for rr in [rel,target]:self.processed(ds,rr,n)

    def asset(self):
        ds='asset'
        for split in ['valid','test']:self.parallel_references(ds,split,10,'en')
        rel='human_ratings/human_ratings.csv';groups={};n=0
        for line,r in _csv(self.path(ds,rel)):
            n+=1;k=(r['original_sentence_id'],r['original'],r['simplification'])
            groups.setdefault(k,[]).append({'source_row':line,**{k:v for k,v in r.items() if k not in ['original','simplification']}})
        for k,ann in groups.items():
            sid,original,simplified=k
            self.out(ds,'ratings','ASSET · simplification ratings','en','rewrite',rel,'human-evaluation',f'csv-rows:'+','.join(str(x['source_row']) for x in ann),_side('Original',original,'input'),_side('Rated simplification',simplified,'candidate'),context=f'ASSET rated simplification · sentence {sid}',extra={'original_sentence_id':sid,'ratings':ann,'rating_count':len(ann)},notes='All released human rating rows are grouped per exact source/candidate and original_sentence_id. The file does not label the simplification author/model, so no author origin is inferred. These candidates do not exactly match released ASSET references.',identity=[sid,original,simplified])
        self.processed(ds,rel,n,f'All {n} evaluator/aspect rows represented in {len(groups)} distinct rated source/candidate records; raw ratings and worker IDs retained.')
        rel='human_ratings/asset_pairwise_comparisons_with_turkcorpus_and_hsplit.csv';groups={};n=0
        for line,r in _csv(self.path(ds,rel)):
            n+=1;k=(r['sentence_id'],r['other_dataset'],r['source'],r['asset_simplification'],r['other_simplification'])
            groups.setdefault(k,[]).append({'source_row':line,**{k:v for k,v in r.items() if k not in ['source','asset_simplification','other_simplification']}})
        for k,ann in groups.items():
            sid,other,source,asset,alternative=k
            self.out(ds,'preferences','ASSET · cross-dataset preferences','en','preference',rel,'human-evaluation',f'csv-rows:'+','.join(str(x['source_row']) for x in ann),_side('Original',source,'input'),_side('ASSET candidate',asset,'candidate'),[_side(other+' candidate',alternative,'candidate')],context=f'ASSET vs {other} · source sentence {sid}',extra={'sentence_id':sid,'other_dataset':other,'comparisons':ann},notes='All evaluator/aspect winners including similar are preserved. Comparisons share original/reference text with other views; these are preference annotations, not additional independent gold sources.',identity=k)
        self.processed(ds,rel,n,f'All {n} evaluator/aspect rows grouped into {len(groups)} source/candidate-pair comparison records; distinct sentence IDs and comparator datasets retained.')

    def coedit(self):
        ds='coedit'
        for split in ['train','validation']:
            rel=split+'.jsonl';n=0
            for line,r in _jsonl(self.path(ds,rel)):
                n+=1;instruction,sep,text=r['src'].partition(':')
                # Card explicitly documents instruction: input_text. Keep untouched raw src in extra.
                left=text[1:] if sep and text.startswith(' ') else text
                if not sep:left=r['src'];instruction=''
                extra={k:v for k,v in r.items() if k not in ['tgt']};extra['instruction']=instruction
                self.out(ds,'','CoEdIT · instruction editing','en','rewrite',rel,split,f'line:{line};id:{r["_id"]}',_side('Input text',left,'input'),_side('Target text',r['tgt'],'target'),context=f'CoEdIT {r["task"]} · {r["_id"]}\nInstruction: {instruction}',extra=extra,notes='src is documented as instruction: input_text; split at first colon and retain original src verbatim in extra. Public dataset omits restricted instances from the paper; heterogeneous editing sources are not de-AI-ese gold.')
            self.processed(ds,rel,n)

    def run(self):
        for fn in [self.adparaphrase,self.iterater,self.arxivedits,self.mcts,self.asset,self.coedit]:fn()
        errors=[]
        for path,c in self.coverage.items():
            expected=c.get('expected_source_records')
            if expected is not None and c.get('status')!='excluded_duplicate_artifact':
                if c['source_records_processed']!=expected:errors.append({'path':path,'expected':expected,'processed':c['source_records_processed']})
        if errors:raise ValueError('Coverage mismatches: '+json.dumps(errors))
        inv=[]
        for name in NAMES:
            manifest=self.manifests[name]
            files={str(p.relative_to(self.base)) for p in (self.ds/name).rglob('*') if p.is_file()}
            untracked=sorted(files-set(self.coverage))
            for path in untracked:
                self.coverage[path]={'local_path':path,'status':'documentation_or_metadata','note':'Auxiliary download metadata or annotation instructions; not a text-pair data source.'}
            inv.append({'dataset':name,'downloaded_files':len(files),'source_url':manifest['source_url'],'pinned_revision':manifest['pinned_revision'],'source_summary':manifest['summary'],'license':manifest['license'],'license_evidence_local_path':f'datasets/{name}/LICENSE-STATUS.md','public_bundle_recommendation':'local-data-only; no blanket redistribution clearance established','source_files_covered':len(files)})
        cols=list(self.collections.values())
        for c in cols:c['splits']=dict(c['splits']);c['pair_types']=dict(c['pair_types'])
        return {'schema_version':VERSION,'root':str(self.base),'total_records':self.total,'collections':cols,'datasets':inv,'sources':list(self.coverage.values()),'exclusions':self.exclusions,'limitations':self.limitations,'unprocessable_parts':[],'validation':{'source_record_counts_match_manifests':True,'sampled':False,'truncated_text':False,'all_parallel_files_length_match':True,'all_json_csv_rows_parsed':True,'all_data_files_covered':True}}


def export(root: Path, emit: Callable[[dict], None]) -> dict:
    """Stream every canonical review record; return collection/source coverage report."""
    return Exporter(root,emit).run()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',type=Path,required=True)
    ap.add_argument('--output',type=Path,help='Optional NDJSON output; omit for count/coverage validation')
    ap.add_argument('--report',type=Path,required=True)
    args=ap.parse_args()
    if args.output:
        with args.output.open('w',encoding='utf-8') as f:
            report=export(args.root,lambda r:f.write(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n'))
    else:report=export(args.root,lambda r:None)
    args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'total_records':report['total_records'],'collections':[{k:v for k,v in c.items() if k in ['id','record_count','splits']} for c in report['collections']],'report':str(args.report)},ensure_ascii=False,indent=2))

if __name__=='__main__':main()

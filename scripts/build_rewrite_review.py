#!/usr/bin/env python3
"""Build an offline review page from local source metadata and generated candidates."""
import argparse
import html
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("collection", type=Path)
    args = parser.parse_args()
    base = args.collection.resolve()
    records = json.loads((base / "pairs.json").read_text())
    cards = []
    for number, row in enumerate(records, 1):
        esc = html.escape
        links = (
            f'<a href="{esc(row["source_url"], quote=True)}" target="_blank" rel="noopener">官方原文 ↗</a> '
            f'<a href="{esc(row["source_local"], quote=True)}" target="_blank">完整本地副本 ↗</a>'
        )
        paragraphs = "".join(f"<p>{esc(p)}</p>" for p in row["rewrite"].split("\n\n"))
        cards.append(f'''<article id="{esc(row['id'])}">
<div class="card-top"><span class="number">{number:02}</span><div><h2>{esc(row['title'])}</h2>
<p class="meta">{esc(row['language'])} · {esc(row['source_date'])} · {esc(row['provenance_note'])}</p></div></div>
<p class="locator">定位：{esc(row['locator'])}</p><div class="links">{links}</div>
<div class="columns"><section><h3>原文片段</h3><iframe title="原文片段 {number}" src="{esc(row['excerpt_local'], quote=True)}"></iframe></section>
<section><h3>AI 自行改写</h3><div class="rewrite">{paragraphs}</div></section></div>
<div class="review" data-id="{esc(row['id'])}"><label>这组能否成为 pair？ <select aria-label="{number} pair 判断">
<option value="unreviewed">待评</option><option value="promising">值得保留为候选</option><option value="content_drift">内容发生变化</option>
<option value="no_clear_difference">没有明显差别</option><option value="unsuitable">不适合此任务</option></select></label>
<label>偏好 <select class="preference" aria-label="{number} 偏好"><option value="unreviewed">待评</option><option value="source">原文</option>
<option value="rewrite">AI 改写</option><option value="tie">平局</option><option value="both_bad">两者都不合适</option></select></label>
<textarea aria-label="{number} 备注" placeholder="哪些表达变好了或变差了？有没有遗漏条件、改变立场？"></textarea></div></article>''')
    css = '''
*{box-sizing:border-box}body{margin:0;background:#f5f3ed;color:#172721;font:16px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
main{max-width:1280px;margin:auto;padding:36px 32px 70px}header{border-bottom:1px solid #c9d0c8;padding-bottom:24px;margin-bottom:28px}
.eyebrow{font-size:12px;letter-spacing:2px;color:#55725f}h1{font-size:36px;line-height:1.2;font-weight:650;margin:12px 0}header p{max-width:850px;color:#53635a}
button{border:0;border-radius:6px;background:#214b3b;color:white;padding:11px 19px;font-size:15px;cursor:pointer}#status{margin-left:15px;font-size:14px;color:#647369}
article{background:#fff;border:1px solid #dce1d9;border-radius:10px;padding:26px;margin:24px 0}.card-top{display:flex;gap:17px;align-items:flex-start}
.number{font:24px/1.5 Georgia,serif;color:#769580}h2{font-size:22px;line-height:1.35;margin:0}h3{font-size:13px;letter-spacing:1px;color:#647b6c;margin:0 0 15px}
.meta,.locator{font-size:13px;color:#6b766f;margin:7px 0}.links{display:flex;gap:22px;margin:8px 0 20px}a{color:#285d46;text-underline-offset:3px}
.columns{display:grid;grid-template-columns:1fr 1fr;gap:26px}.columns section{background:#f8faf7;padding:20px;border-radius:6px;min-width:0}
iframe{display:block;border:0;width:100%;min-height:320px;background:white}.rewrite{font-size:17px;line-height:1.8;white-space:pre-wrap}.rewrite p:first-child{margin-top:0}
.review{border-top:1px solid #e5e9e2;margin-top:22px;padding-top:18px;display:flex;gap:18px;flex-wrap:wrap}.review label{font-size:14px}
select{font:inherit;color:#244c3d;border:1px solid #c6d1c6;border-radius:4px;padding:7px;background:white}textarea{width:100%;min-height:70px;border:1px solid #d3dcd1;border-radius:5px;padding:12px;font:14px/1.5 inherit}
footer{font-size:13px;color:#6b766f}@media(max-width:800px){main{padding:24px 14px}.columns{grid-template-columns:1fr}article{padding:18px}h1{font-size:28px}}
'''
    js = '''
const state={}; const storageKey='plainvoice-rewrite-review-2026-09-12-v1';
try{Object.assign(state,JSON.parse(localStorage.getItem(storageKey)||'{}'));}catch(e){}
function status(){document.querySelector('#status').textContent=Object.values(state).filter(x=>x.pair_status!=='unreviewed'||x.preference!=='unreviewed'||x.notes).length+' 组有评审记录';}
document.querySelectorAll('.review').forEach(el=>{const id=el.dataset.id;const fields=[el.querySelector('select'),el.querySelector('.preference'),el.querySelector('textarea')];
const old=state[id]||{}; fields[0].value=old.pair_status||'unreviewed';fields[1].value=old.preference||'unreviewed';fields[2].value=old.notes||'';
fields.forEach(f=>f.addEventListener('input',()=>{state[id]={pair_status:fields[0].value,preference:fields[1].value,notes:fields[2].value,updated_at:new Date().toISOString()};try{localStorage.setItem(storageKey,JSON.stringify(state));}catch(e){}status();}));});
document.querySelector('#export').addEventListener('click',()=>{const data={collection:'plainvoice-rewrite-pilot-2026-09-12',evaluation_mode:'unblinded_user_review',exported_at:new Date().toISOString(),reviews:state};
const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='plainvoice-user-review.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});status();
'''
    page = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Plainvoice · 改写候选审阅</title><style>{css}</style></head><body><main>
<header><div class="eyebrow">PLAINVOICE / REWRITE PILOT / 2026.09.12</div><h1>同一段内容，换一种写法</h1>
<p>{len(records)} 组真实来源片段与 AI 改写。模型收到普通改写指令，自行选择结构和措辞。这些是候选，尚未获得人类偏好标签；原文也不预设为胜者。</p>
<button id="export">导出我的评审 JSON</button><span id="status"></span></header>
{''.join(cards)}<footer>当前页面展示来源身份，属于探索性审阅，不是盲评 benchmark。浏览器允许时会本地保存草稿，请导出 JSON 留存。来源与许可见 sources/manifest.json；模型与提示见 generation/。没有外部网络请求或自动上传。</footer>
</main><script>{js}</script></body></html>'''
    (base / "review.html").write_text(page)
    print(f"Created {base / 'review.html'} with {len(records)} candidate pairs")


if __name__ == "__main__":
    main()

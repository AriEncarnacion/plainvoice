#!/usr/bin/env python3
"""Build a self-contained, offline full-article review page from local files.

Usage:
    python3 build_article_review.py /path/to/article-v2/article-results.json
    python3 build_article_review.py /path/to/article-v2

No article text is stored in this script. Files named in the input manifest are
read only at build time. The output is review.html beside article-results.json.
"""

import argparse
import hashlib
import html
import json
import re
import sys
from pathlib import Path


REQUIRED = (
    "id", "title", "language", "source_path", "content_path",
    "shuffled_packet_path", "rewrite_path", "source_metrics",
    "rewrite_metrics", "qa_status", "notes",
)
PATH_FIELDS = ("source_path", "content_path", "shuffled_packet_path", "rewrite_path")
TEXT_LABELS = {
    "source_path": "整篇原文", "rewrite_path": "整篇 AI 正文",
    "content_path": "SVO 内容卡", "shuffled_packet_path": "打乱后的 packet",
}
ESC = html.escape


class ReviewInputError(Exception):
    """An actionable problem with the local review input."""


def display(value):
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, indent=2)
    if value is None or value == "":
        return "未提供"
    return str(value)


def read_manifest(path):
    try:
        raw = path.read_bytes()
        rows = json.loads(raw.decode("utf-8-sig"))
    except FileNotFoundError as exc:
        raise ReviewInputError(f"找不到 {path}。请先生成 article-results.json。") from exc
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ReviewInputError(f"无法读取 UTF-8 JSON：{path}；{exc}") from exc
    if not isinstance(rows, list) or not rows:
        raise ReviewInputError("article-results.json 顶层应为非空列表，每项对应一篇文章。")
    seen = set()
    for index, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            raise ReviewInputError(f"第 {index} 项应为 JSON 对象。")
        missing = [key for key in REQUIRED if key not in row]
        if missing:
            raise ReviewInputError(f"第 {index} 项缺少字段：{', '.join(missing)}。")
        for key in ("id", "title", "language"):
            if not isinstance(row[key], str) or not row[key].strip():
                raise ReviewInputError(f"第 {index} 项的 {key} 应为非空字符串。")
        if row["id"] in seen:
            raise ReviewInputError(f"文章 id 重复：{row['id']}；请使用唯一 id。")
        seen.add(row["id"])
        for key in ("source_metrics", "rewrite_metrics"):
            if not isinstance(row[key], dict):
                raise ReviewInputError(f"文章 {row['id']} 的 {key} 应为对象；无指标时请填 {{}}。")
    return rows, raw


def read_local_files(base, row):
    files = {}
    for field in PATH_FIELDS:
        value = row[field]
        if not isinstance(value, str) or not value.strip():
            raise ReviewInputError(f"文章 {row['id']} 的 {field} 应为相对路径字符串。")
        relative = Path(value)
        if relative.is_absolute():
            raise ReviewInputError(f"文章 {row['id']} 的 {field} 必须相对于 article-v2：{value}")
        target = (base / relative).resolve()
        # Relative paths may point to an audited source beside article-v2,
        # for example ../source-audit/<article>/article.txt.
        try:
            raw = target.read_bytes()
            text = raw.decode("utf-8-sig")
        except FileNotFoundError as exc:
            raise ReviewInputError(f"文章 {row['id']} 缺少{TEXT_LABELS[field]}文件：{target}") from exc
        except (OSError, UnicodeError) as exc:
            raise ReviewInputError(f"文章 {row['id']} 的 {field} 无法作为 UTF-8 文本读取：{exc}") from exc
        if not text.strip():
            raise ReviewInputError(f"文章 {row['id']} 的{TEXT_LABELS[field]}为空：{target}")
        files[field] = {
            "text": text, "name": target.name,
            "mime": "application/json" if target.suffix.lower() == ".json" else "text/plain",
            "sha256": hashlib.sha256(raw).hexdigest(),
        }
    return files


def lengths(text):
    return {
        "characters": len(text),
        "non_whitespace_characters": sum(not char.isspace() for char in text),
        "han_characters": len(re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff\U00020000-\U0002fa1f]", text)),
        "latin_words": len(re.findall(r"[A-Za-z]+(?:['’\-][A-Za-z]+)*", text)),
    }


def download_button(element_id, file):
    return (
        f'<button type="button" class="secondary download" data-target="{ESC(element_id)}" '
        f'data-filename="{ESC(file["name"], quote=True)}" '
        f'data-mime="{ESC(file["mime"])}">下载文本</button>'
    )


def select_field(index, name, label, options):
    choices = [("unreviewed", "待评"), *options]
    rendered = "".join(f'<option value="{ESC(value)}">{ESC(text)}</option>' for value, text in choices)
    return (
        f'<label for="{name}-{index}">{ESC(label)}'
        f'<select id="{name}-{index}" data-field="{name}">{rendered}</select></label>'
    )


def article_card(index, row, files):
    source = lengths(files["source_path"]["text"])
    rewrite = lengths(files["rewrite_path"]["text"])
    ratio = rewrite["non_whitespace_characters"] / source["non_whitespace_characters"]
    metric_rows = "".join(
        f'<tr><th scope="row">{label}</th><td>{source[key]:,}</td><td>{rewrite[key]:,}</td></tr>'
        for key, label in (
            ("characters", "字符（含空白）"),
            ("non_whitespace_characters", "非空白字符"),
            ("han_characters", "汉字"),
            ("latin_words", "拉丁字母词"),
        )
    )
    panes = []
    for field, class_name in (("source_path", "source"), ("rewrite_path", "rewrite")):
        file = files[field]
        element_id = f"text-{index}-{class_name}"
        panes.append(
            f'<section class="text-column {class_name}"><div class="pane-title">'
            f'<h3>{TEXT_LABELS[field]}</h3>{download_button(element_id, file)}</div>'
            f'<pre id="{element_id}" class="article-text" tabindex="0" '
            f'aria-label="{ESC(row["title"], quote=True)}：{TEXT_LABELS[field]}">{ESC(file["text"])}</pre></section>'
        )
    supporting = []
    for field, key in (("content_path", "content"), ("shuffled_packet_path", "packet")):
        file = files[field]
        element_id = f"text-{index}-{key}"
        supporting.append(
            f'<details class="support"><summary>{TEXT_LABELS[field]}</summary>'
            f'<div class="support-actions">{download_button(element_id, file)}</div>'
            f'<pre id="{element_id}" tabindex="0">{ESC(file["text"])}</pre></details>'
        )
    controls = "".join((
        select_field(index, "preference", "综合偏好", [
            ("source", "原文"), ("rewrite", "AI 正文"), ("tie", "平局"),
            ("both_bad", "两者都不合适"), ("abstain", "无法判断"),
        ]),
        select_field(index, "factual_preservation", "事实与立场是否保留", [
            ("pass", "未发现漂移"), ("drift", "存在事实 / 立场漂移"), ("uncertain", "尚不能确定"),
        ]),
        select_field(index, "content_omission", "全文内容遗漏", [
            ("none_found", "未发现遗漏"), ("minor", "少量内容遗漏"),
            ("major", "关键内容遗漏"), ("uncertain", "尚不能确定"),
        ]),
        select_field(index, "organization_similarity", "与原文的组织相似度", [
            ("low", "低：有独立组织"), ("medium", "中：部分沿用顺序"),
            ("high", "高：基本沿用原文"), ("uncertain", "尚不能确定"),
        ]),
    ))
    metadata = {key: row[key] for key in REQUIRED}
    metadata["displayed_text_lengths"] = {"source": source, "rewrite": rewrite}
    metadata["file_sha256"] = {field: value["sha256"] for field, value in files.items()}
    return f'''<article id="article-{index}" data-id="{ESC(row['id'], quote=True)}">
<div class="article-heading"><span class="number">{index:02}</span><div>
<h2>{ESC(row['title'])}</h2><p class="meta">{ESC(row['language'])} · {ESC(row['id'])}</p></div></div>
<div class="evidence-top"><section><h3>整篇文本长度</h3>
<table><thead><tr><th>统计口径</th><th>原文</th><th>AI 正文</th></tr></thead><tbody>{metric_rows}</tbody></table>
<p class="small">AI / 原文非空白字符：{ratio:.2f}×。长度依据本地全文计算，不代表内容覆盖率。</p></section>
<section class="qa"><h3>全文内容覆盖 / QA（输入记录）</h3><pre>{ESC(display(row['qa_status']))}</pre>
<p class="small">以下左右栏嵌入各自文件的全部文本；是否覆盖原文的全部内容，请结合内容卡与全文判断。</p>
<details><summary>生成记录备注与原始指标</summary><h4>备注</h4><pre>{ESC(display(row['notes']))}</pre>
<h4>原文指标</h4><pre>{ESC(display(row['source_metrics']))}</pre>
<h4>AI 正文指标</h4><pre>{ESC(display(row['rewrite_metrics']))}</pre></details></section></div>
<div class="view-controls"><label><input type="checkbox" class="sync-scroll"> 按比例同步滚动</label>
<button type="button" class="secondary expand" aria-expanded="false">展开全部高度</button>
<span class="small">逐段检查事实与条件；再看段落推进、论证顺序是否仍沿用原文。</span></div>
<div class="columns">{''.join(panes)}</div><div class="support-grid">{''.join(supporting)}</div>
<form class="review" autocomplete="off"><div class="review-fields">{controls}</div>
<label for="notes-{index}">评审备注<textarea id="notes-{index}" data-field="review_notes" rows="3"
placeholder="可写出遗漏的事实、发生漂移的条件，以及仍像原文的组织方式或更好的表达。"></textarea></label>
<p class="saved small" aria-live="polite">待评</p></form>
<pre class="record-metadata" hidden>{ESC(json.dumps(metadata, ensure_ascii=False))}</pre></article>'''


CSS = """
:root{color-scheme:light;--ink:#182923;--muted:#586b63;--line:#d6dfd8;--accent:#246047}
*{box-sizing:border-box}body{margin:0;background:#f3f4ef;color:var(--ink);font:16px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
main{max-width:1640px;margin:auto;padding:30px 28px 70px}h1{font-size:34px;line-height:1.25;margin:10px 0 16px}h2{font-size:25px;line-height:1.35;margin:0}h3{font-size:15px;margin:0 0 10px}h4{font-size:14px;margin:14px 0 5px}
header>p{max-width:1050px;color:var(--muted)}a{color:var(--accent);text-underline-offset:3px}.eyebrow{font-size:12px;letter-spacing:2px;color:var(--muted)}
.toolbar{position:sticky;top:0;z-index:10;background:rgba(243,244,239,.97);border-block:1px solid var(--line);padding:12px 0;display:flex;gap:15px;align-items:center;flex-wrap:wrap}
button{font:inherit;cursor:pointer;border:1px solid var(--accent);border-radius:6px;background:var(--accent);color:#fff;padding:8px 15px}.secondary{background:#fff;color:var(--accent);padding:5px 10px;font-size:13px}
button:focus-visible,select:focus-visible,textarea:focus-visible,pre:focus-visible,a:focus-visible{outline:3px solid #80b598;outline-offset:3px}
#jump{max-width:500px}.small,.meta{font-size:13px;color:var(--muted)}.warning{color:#944019!important}#status{font-size:13px}.article-heading{display:flex;gap:16px;align-items:flex-start}.number{font:27px/1.3 Georgia,serif;color:#668772}
article{scroll-margin-top:85px;background:#fff;border:1px solid var(--line);border-radius:10px;padding:25px;margin:25px 0}.meta{margin:8px 0 0}.evidence-top{display:grid;grid-template-columns:minmax(280px,.8fr) minmax(320px,1.2fr);gap:24px;margin:20px 0}
table{border-collapse:collapse;width:100%;font-size:13px;font-variant-numeric:tabular-nums}th,td{text-align:left;border-bottom:1px solid var(--line);padding:5px 9px}thead{background:#f0f4f0}tbody th{font-weight:400}
.qa{background:#f8f8f3;border:1px solid #e7e6d8;border-radius:7px;padding:15px}.qa pre{margin:5px 0;max-height:220px;overflow:auto;font-size:13px}.qa details pre{max-height:180px}
.view-controls{display:flex;align-items:center;gap:16px;flex-wrap:wrap;padding:12px 0;font-size:14px}.view-controls label{white-space:nowrap}.columns{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:20px;align-items:start}
.text-column{min-width:0;border:1px solid var(--line);border-radius:7px;overflow:hidden}.pane-title{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:12px 16px;background:#eef4ef}.pane-title h3{margin:0}.rewrite .pane-title{background:#f4f0e7}
pre{white-space:pre-wrap;overflow-wrap:anywhere;word-break:normal;font:inherit}.article-text{height:68vh;min-height:350px;max-height:850px;margin:0;overflow:auto;padding:22px;font-size:17px;line-height:1.9;tab-size:4}.expanded .article-text{height:auto;max-height:none;min-height:0}
.support-grid{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:17px}.support{min-width:0;border:1px solid var(--line);border-radius:6px;padding:12px 16px}.support pre{font:13px/1.7 ui-monospace,SFMono-Regular,Consolas,monospace;max-height:360px;overflow:auto;padding:10px;background:#f7f8f5}.support-actions{margin-top:10px}summary{cursor:pointer;color:var(--accent);font-size:14px}
.review{margin-top:22px;border-top:1px solid var(--line);padding-top:20px}.review-fields{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px}.review label{display:block;font-size:14px}.review select{width:100%;margin-top:6px}select{font:inherit;padding:8px;color:var(--ink);border:1px solid #bdcbbc;border-radius:5px;background:#fff}
textarea{display:block;width:100%;font:inherit;font-size:15px;line-height:1.6;padding:12px;border:1px solid #bdcbbc;border-radius:5px;resize:vertical;margin-top:7px}.review>label{margin-top:15px}.saved{margin:8px 0 0}footer{font-size:13px;color:var(--muted);max-width:1000px}
@media(max-width:1000px){.review-fields{grid-template-columns:1fr 1fr}.evidence-top{grid-template-columns:1fr 1fr}.article-text{font-size:16px;padding:16px}}
@media(max-width:720px){main{padding:20px 12px 50px}h1{font-size:28px}h2{font-size:21px}article{padding:16px}.columns,.support-grid,.evidence-top{grid-template-columns:1fr}.article-text{height:58vh;min-height:240px}.toolbar{position:static}article{scroll-margin-top:15px}.review-fields{grid-template-columns:1fr 1fr}.toolbar #jump{max-width:100%}}
@media print{.toolbar,.review,.view-controls,button{display:none}.article-text{height:auto;max-height:none;overflow:visible}.columns{grid-template-columns:1fr 1fr}article{break-before:page}}
"""


JS = r"""
'use strict';
const root = document.querySelector('main');
const fingerprint = root.dataset.fingerprint;
const storageKey = 'plainvoice-article-review-2026-09-12-v2:' + fingerprint;
const articles = Array.from(document.querySelectorAll('article'));
const state = Object.create(null);
let storageAvailable = true;
try {
  const saved = JSON.parse(localStorage.getItem(storageKey) || '{}');
  if (saved && typeof saved === 'object' && !Array.isArray(saved)) {
    for (const article of articles) {
      const old = saved[article.dataset.id];
      if (old && typeof old === 'object' && !Array.isArray(old)) state[article.dataset.id] = old;
    }
  }
} catch (error) { storageAvailable = false; }
function hasReview(record) {
  return record && Object.entries(record).some(([key, value]) =>
    key !== 'updated_at' && value && value !== 'unreviewed');
}
function updateStatus() {
  const count = articles.filter(article => hasReview(state[article.dataset.id])).length;
  const status = document.querySelector('#status');
  status.textContent = count + ' / ' + articles.length + ' 篇有评审记录' +
    (storageAvailable ? ' · 草稿保存于此浏览器' : ' · 浏览器本地保存不可用，请导出 JSON');
  status.classList.toggle('warning', !storageAvailable);
}
function saveArticle(article) {
  const record = Object.create(null);
  article.querySelectorAll('[data-field]').forEach(field => { record[field.dataset.field] = field.value; });
  record.updated_at = new Date().toISOString();
  state[article.dataset.id] = record;
  try { localStorage.setItem(storageKey, JSON.stringify(state)); storageAvailable = true; }
  catch (error) { storageAvailable = false; }
  article.querySelector('.saved').textContent = storageAvailable ? '已保存本篇草稿' : '当前修改仅在此页内存中，请导出 JSON';
  updateStatus();
}
function downloadText(text, name, mime) {
  const url = URL.createObjectURL(new Blob([text], {type: mime + ';charset=utf-8'}));
  const link = document.createElement('a');
  link.href = url; link.download = name; document.body.appendChild(link); link.click(); link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
articles.forEach(article => {
  const old = state[article.dataset.id] || {};
  article.querySelectorAll('[data-field]').forEach(field => {
    const value = old[field.dataset.field];
    if (typeof value === 'string' && (field.tagName !== 'SELECT' || Array.from(field.options).some(option => option.value === value))) field.value = value;
    field.addEventListener('input', () => saveArticle(article));
  });
  if (hasReview(old)) article.querySelector('.saved').textContent = '已恢复此内容版本的草稿';
  article.querySelector('form').addEventListener('submit', event => event.preventDefault());
  article.querySelector('.expand').addEventListener('click', event => {
    const expanded = article.classList.toggle('expanded');
    event.currentTarget.textContent = expanded ? '恢复独立滚动' : '展开全部高度';
    event.currentTarget.setAttribute('aria-expanded', String(expanded));
  });
  const panes = Array.from(article.querySelectorAll('.article-text'));
  let synchronizing = false;
  panes.forEach((pane, index) => pane.addEventListener('scroll', () => {
    if (synchronizing || !article.querySelector('.sync-scroll').checked || article.classList.contains('expanded')) return;
    const maximum = pane.scrollHeight - pane.clientHeight;
    if (maximum <= 0) return;
    synchronizing = true;
    const other = panes[1 - index];
    other.scrollTop = pane.scrollTop / maximum * Math.max(0, other.scrollHeight - other.clientHeight);
    requestAnimationFrame(() => { synchronizing = false; });
  }, {passive:true}));
});
document.querySelectorAll('.download').forEach(button => button.addEventListener('click', () => {
  downloadText(document.getElementById(button.dataset.target).textContent, button.dataset.filename, button.dataset.mime);
}));
document.querySelector('#jump').addEventListener('change', event => {
  const target = document.getElementById(event.target.value);
  if (target) target.scrollIntoView({behavior:'smooth', block:'start'});
});
document.querySelector('#export').addEventListener('click', () => {
  const reviews = articles.map(article => {
    const metadata = JSON.parse(article.querySelector('.record-metadata').textContent);
    const review = Object.create(null);
    article.querySelectorAll('[data-field]').forEach(field => { review[field.dataset.field] = field.value; });
    review.updated_at = state[article.dataset.id]?.updated_at || null;
    return {article: metadata, review};
  });
  const result = {
    schema_version: 'plainvoice.article-review.v2', collection: 'article-v2',
    evaluation_mode: 'unblinded_exploratory_full_article_review',
    input_manifest: root.dataset.manifest, content_fingerprint: fingerprint,
    exported_at: new Date().toISOString(), reviews
  };
  downloadText(JSON.stringify(result, null, 2), 'plainvoice-article-review-' + fingerprint.slice(0, 10) + '.json', 'application/json');
});
updateStatus();
"""


def build_page(manifest_path):
    base = manifest_path.parent.resolve()
    rows, raw = read_manifest(manifest_path)
    files_by_article = [read_local_files(base, row) for row in rows]
    digest = hashlib.sha256(raw)
    for files in files_by_article:
        for field in PATH_FIELDS:
            digest.update(bytes.fromhex(files[field]["sha256"]))
    fingerprint = digest.hexdigest()
    cards = "".join(article_card(index, row, files) for index, (row, files) in enumerate(zip(rows, files_by_article), 1))
    options = "".join(f'<option value="article-{index}">{index:02} · {ESC(row["title"])}</option>' for index, row in enumerate(rows, 1))
    page = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Plainvoice · 整篇文章审阅</title>
<style>{CSS}</style></head><body><main data-fingerprint="{fingerprint}" data-manifest="{ESC(manifest_path.name, quote=True)}">
<header><div class="eyebrow">PLAINVOICE / ARTICLE V2</div><h1>比较整篇内容与组织方式</h1>
<p>{len(rows)} 篇完整原文与 AI 正文。先检查事实、条件与内容覆盖，再判断新的组织方式和写作偏好。每篇可展开 SVO 内容卡及打乱后的 packet。</p>
<p><a href="../review-paragraph-v1.html">← 查看 paragraph-v1 段落审阅页</a></p></header>
<div class="toolbar"><button type="button" id="export">导出我的评审 JSON</button>
<label for="jump" class="small">跳至</label><select id="jump"><option value="">选择文章</option>{options}</select>
<span id="status" role="status" aria-live="polite"></span></div>
{cards}<footer>此页展示来源身份，属于探索性全文审阅。标签未预填，也不自动成为训练偏好。
草稿只对应本次内容版本，与 paragraph-v1 分开保存；请导出 JSON 留存。全部文本已嵌入本地页面，内容卡和 packet 可离线查看、下载；无自动上传或网络依赖。</footer>
</main><script>{JS}</script></body></html>'''
    return page, len(rows)


def main(argv=None):
    parser = argparse.ArgumentParser(description="为 article-v2 构建离线整篇文章审阅页。")
    parser.add_argument("input", type=Path, help="article-results.json 或其所在的 article-v2 目录")
    args = parser.parse_args(argv)
    path = args.input.expanduser().resolve()
    if path.is_dir():
        path = path / "article-results.json"
    try:
        page, count = build_page(path)
        output = path.parent / "review.html"
        output.write_text(page, encoding="utf-8")
    except ReviewInputError as exc:
        print(f"无法构建整篇审阅页：{exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"无法写入审阅页：{exc}", file=sys.stderr)
        return 2
    print(f"Created {output} with {count} full-article pairs (offline, no network dependencies)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

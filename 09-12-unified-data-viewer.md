# Unified Data Viewer

A single interface for reviewing every normalizable record this project has downloaded or generated. Full body text is read through a local SQLite index and loaded page by page in the browser; there is no need to load 1.25M rows into the page at once.

## Coverage

| Source | Records |
|---|---:|
| Six full-article rewrites v2 + six paragraph rewrite sets v1 | 12 |
| Agentic / technical local samples | 77 |
| AdParaphrase | 31,058 |
| IteraTeR | 230,141 |
| arXivEdits | 219,598 |
| MCTS | 692,197 |
| ASSET | 3,177 |
| CoEdIT | 70,783 |
| This round's low-cost model AI candidates and diagnostics | 848 |
| **Total** | **1,247,891** |

There are 28 filterable collections in total. The records are not mutually independent, already-validated training pairs: human revisions, multi-reference simplification, machine synthesis, same-task reports, preference annotation, and unpaired text are each marked separately. Chinese, English, and Japanese are all labeled according to the actual data; AdParaphrase is Japanese. For one-sided samples, column B does not fabricate an answer.

The full text, all reference answers, task instructions, split, file and line location, source URL, and license notes are all preserved. The content cards and QA for article v2, and every event in a real trace, can be expanded and inspected. A full re-check found 2,650 empty targets and 116 empty source texts in the source database (whitespace-only strings count as empty), preserving deletion and insertion semantics respectively; 62,595 null targets are retained as unpaired. ASSET's 4,500 ratings and 2,154 comparison annotations are merged per sample, with none discarded. 3,054 IteraTeR HUMAN/FULL exact overlaps and 978 arXiv annotation overlaps were merged with their sources preserved; 22 unmatched arXiv annotations are listed separately.

The technical samples include SWE-Hero, SWE-smith, DRB II, CogGen/OWID, FreshWiki, Code2Doc, and ResearcherBench, 77 items in total. "All" here means the bounded sample actually downloaded earlier, not these upstream datasets in full. 12 candidate copies in the existing training directory have the same text as paragraph v1 and are not shown twice; 36 fictitious program test fixtures do not count as research data.

For the new AI comparisons, see [this round's delivery notes](09-12-low-cost-ai-enrichment.md). 839 target sources are covered in total; 11 drafts carry specific semantic issue flags, and the other drafts have not been through human acceptance either. The viewer opens on the new article collection by default, and old records and individual reviews are unchanged.

## How to review

The latest default is the [cleaned body text](09-12-text-cleaning.md). You can switch to the raw version, view the per-item cleaning record, filter by candidate/quarantine status, and download the comparison text currently shown. Reviews of the raw text and of the cleaned text are kept separate by content hash.

Select a dataset and filter by language, pairing type, keyword, or review status. The A/B full texts scroll independently, and you can also scroll them in sync, adjust font size, and hide source labels. For multi-reference samples you can switch which B is shown. J/K move to the next or previous item. Queries cover titles and the comparison/reference body text; the additional JSON for task context and traces can be inspected in the detail view and is not included in the full-text search index.

For each item you can record keep/revise/exclude, expression preference, content fidelity, an AI-ese comparison, and notes. Annotations are saved in the current browser's localStorage, and can be exported as JSON and imported again to restore them. Record ID, content hash, and B-candidate number together identify a review, so a change in text version does not silently inherit the old review. The labels are still personal judgment; hiding source labels is not the same as strict blind evaluation, since the body text may reveal the source's identity.

## Starting the full database

Requires Python 3.10+ with SQLite FTS5; everything uses the standard library, with no third-party install step.

```sh
python3 scripts/build_data_viewer.py \
  --root "$HOME/Desktop/plainvoice/data/local" \
  --output "$HOME/Desktop/plainvoice/data/local/data-viewer/review.sqlite"

python3 scripts/serve_data_viewer.py \
  --database "$HOME/Desktop/plainvoice/data/local/data-viewer/review.sqlite"
```

Open the [full local viewer](http://127.0.0.1:8876). The first build reads every source and creates a derived index of roughly 2.51 GB; after that, run the second command directly. Input files are not modified. The server binds to loopback only, the API is read-only, and reviews are not uploaded to any server. After stopping it, just run the start command again.

## Hosted entry point and public code

The [hosted viewer](https://plainvoice-data-review.jason62-h.chatgpt.site) uses the same front end and provides a source directory for the 28 collections, plus one OWID example that has a CC BY 4.0 basis and its attribution fully preserved. It can link through to the full database on the current computer. The hosted entry point follows the Sites default of owner-only access; the GitHub repository's public visibility and Sites access permissions are two separate things.

GitHub holds the front end, the parsers, the build/serve scripts, the statistics directory, and the licensed example described above. The full desktop text, the SQLite database, the raw download package, and individual reviews are not uploaded. Being publicly downloadable does not automatically mean something is suitable for any training or redistribution use; each record retains its original evidence of rights.

Public example: Max Roser, "Smoking: How large of a global problem is it? And how can we make progress against it?", Our World in Data, 2021-07-14. [Original](https://ourworldindata.org/smoking-big-problem-in-brief), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The body text comes from the CogGen download snapshot; the cleaned version removes webpage metadata and layout without rewriting the wording. Attribution, the original link, the license, and the modification note are retained in the source information; externally linked images are not downloaded or displayed.

For verification scope, see the [QA record](qa/09-12-viewer-qa.md).

# Plainvoice

[English](README.md) · [简体中文](README.zh-CN.md)

Research into making content rewriting more natural and more informative while preserving facts, purpose, and the author's voice. Four scenarios have equal priority: Chinese, English, technical docs, and marketing.

Current phase: background research, data collection, and content rewriting experiments. Most recently, Gemini Flash-Lite was used to produce 848 candidates and diagnostic outputs, covering complete articles, segments, model comparisons, and early diagnostics; all of them use content extraction followed by shuffled recomposition. There is no trained model, no validated judge, no real benchmark score, and no gold confirmed by independent human review.

## Local directory and startup

2026-09-15: the complete Git repository was moved to `~/Desktop/plainvoice`, preserving the existing Git history and `origin`. Code lives in `scripts/`, and literature research in `research/`. The original desktop data package has been moved into `data/local/`; that directory is excluded in its entirety by `.gitignore`, while `data/README.md` remains under version control.

Double-click `Open Plainvoice Viewer.command` in the repository root, or run this from the repository directory:

```bash
python3 scripts/serve_data_viewer.py --database data/local/data-viewer/review.sqlite
```

Open <http://127.0.0.1:8876/?view=clean> in your browser. The old absolute paths in historical data and QA are retained as provenance from the time of collection; to locate the corresponding file, replace `~/Desktop/plainvoice-data-2026-09-12/` with this repository's `data/local/`.

## Start here

- **[Repo-wide body-text cleaning](09-12-text-cleaning.md)**: unifying source/AI formats, body-text export, switching to the raw version, and quality quarantine.

- **[Unified Data Viewer](09-12-unified-data-viewer.md)**: all 1,247,891 local records across 28 collections, with side-by-side full text, filtering, reference answers, traces, and review import/export. The [local entry point](http://127.0.0.1:8876) requires starting the database first; the [hosted entry point](https://plainvoice-data-review.jason62-h.chatgpt.site) provides a source directory and permission-cleared examples, with access controlled by Sites account permissions.
- **[Bilingual AI candidate enrichment and model comparison](09-12-low-cost-ai-enrichment.md)**: counts added, source coverage, actual cost, gaps, and semantic QA; review the new collections in the local viewer first.
- [Full-article rewrite v2: content extraction, shuffling, and independent composition](09-12-article-reconstruction-v2.md): the latest method, six sources, limitations in completeness and structural change, and the reusable prompts and scripts. The latest desktop entry point is `human-rewrite-pairs/article-v2/review.html`.
- [Desktop data package and the first rewrite sample](09-12-local-data-and-rewrite-pilot.md): data already downloaded, agentic/technical writing samples, and six rewrite candidates that can be reviewed collection by collection.
- [Existing literature: research context and the most relevant papers](research/09-12-literature-review.md): start with what existing research did, what it found, and which questions remain open.
- [Directly related humanizer prior art](research/09-12-humanization-prior-art.md): DIPPER, HUMPA, CoPA, and the community Unslopper; distinguishing detector metrics from writing quality.
- [Ground truth acquisition plan](09-12-ground-truth-acquisition.md): verified datasets, real model drafts and human edits, blind evaluation, an 80-item collection pilot, and SFT/DPO data shapes.
- [Research conclusions and experiment plan](09-12-research-and-experiment-plan.md): a critical look at ground truth, evaluators, training methods, model scale, and experiment cost.
- [Style and domain literature](research/09-12-style-literature.md): linguistic evidence for "AI-ese", counter-evidence, and Chinese-language and domain boundaries.
- [Evaluation literature](research/09-12-evaluation-literature.md): detectors, human evaluation, judge bias, and fidelity.
- [Training literature](research/09-12-training-literature.md): SFT, LoRA/QLoRA, DPO, RL, and model candidates.
- [Data and task literature](research/09-12-data-and-task-literature.md): editing datasets, writing benchmarks, and ground truth sources.
- [Annotation protocol](09-12-annotation-protocol.md), [baseline prompt templates](prompts/README.md), [data conventions and examples](data/README.md).
- [Research coverage and verification record](qa/09-12-research-qa.md).

## Next experiment

First complete a human rubric pilot of 20 items per scenario, 80 items in total. Use human disagreement to revise the evaluation criteria, then compare strong prompting against harness approaches, and only then decide whether to train. Final success is determined by independent human testing and actual use; AI detection scores may serve only as a research diagnostic.

## Working conventions

Literature facts, results reported by authors, this project's inferences, and experiment proposals must be kept distinct. New results must state the model checkpoint, data split, prompt version, random seed, total call cost, and limitations. Examples, automatic labels, and scores from the literature must not be written up as this project's own measurements.

Third-party source texts and data are imported only after usage rights have been verified item by item; this round stores only research notes, links, and original demos. A personal project does not automatically inherit usage rights to company materials. Raw data and future model artifacts stay in separate directories and are kept out of Git by default.

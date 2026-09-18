# Agentic Trace and Technical Writing: Public Data Verification and Small Samples

Verification date: 2026-09-12. The goal was to find material that can be paired across AI text, verifiable task/execution evidence, and high-quality human writing. This round read official papers, author repositories, and data cards, and inspected the fields of actual samples; no generative model was run, no training was done, and no software environment was replayed.

**Conclusion: observable tool trajectories and final engineering summaries have been obtained, and one AI report–human reference article pair with a verified identical prompt has been found; no ready-made gold data was found that could be called "same content, facts unchanged, AI first draft refined by a human."** The most suitable entry point for tool trajectories is NVIDIA's SWE-Hero; for research reports, start with DeepResearch Bench II and CogGen. Code-comment data is closer to technical documentation, but its human source and quality still need to be verified item by item.

The data itself is stored in the user-specified desktop directory: `~/Desktop/plainvoice/data/local/agentic-technical/`. `source-manifest.json` records the source, revision, sample selection, license notes, and file checksums; third-party body text is kept only on the desktop and is not brought into this repository.

## 1. First distinguish four kinds of "pairing"

| Type | Questions it can answer | What it cannot directly establish |
|---|---|---|
| A human article and an AI article on the same topic | Exploration of stylistic differences | That information content, facts, purpose, and length are controlled |
| Two articles for the same task/prompt | Overall output quality under the same requirement | That the two articles express the same set of facts; that the human draft is a revision of the AI draft |
| Human and AI output from the same code/brief/evidence | Generation quality on a shared factual basis | That rewrite preferences with fully equivalent facts have been obtained |
| An AI first draft plus a human-refined draft, with fact verification | The targets needed for rewrite SFT/DPO | That every human change is necessarily an improvement |

Another independent dimension is trace. A log carrying `assistant.tool_calls` together with the matching `tool` observations is an observable record of the interaction; a model narrating "I searched..." or a `thought` / rationale field is not evidence that the tool actually ran. An exported message history is also not guaranteed to contain every retry, environment state, hidden step, or replayable dependency.

## 2. Actual samples to look at first

| Data | Obtained on the desktop | Pairing and trace level | Priority use |
|---|---|---|---|
| **SWE-Hero / OpenHands** | 3 trajectories; 143, 145, and 117 messages respectively; each keeps its final assistant turn, `finish.message`, and `model_patch` | Observable actions/observations + a final engineering summary; no human revision | Establish execution-evidence constraints for the final summary, then collect human refinements |
| **DeepResearch Bench II** | Software Development idx 41–50: 5 Chinese, 5 English; 10 Doubao final reports; the corresponding tasks, rubrics, and links to the human source articles | Same-task AI reports + expert source criteria; this package has no full text of the human source articles and no trace | Evaluating Chinese and English technical research reports with fact and style separated |
| **CogGen / OWID** | 20 human reference body texts and their tasks; 2 official AI examples, of which deforestation has been verified to have a verbatim identical query | **1 exact-same-task AI–human reference pair**, not a same-content rewrite; no complete trace published | The most direct starting point for comparing AI and human research writing |
| **STORM / FreshWiki** | 10 technical, scientific, and related business encyclopedia articles, keeping the body text, source URLs, and references | Human reference pool; no corresponding AI output/trajectory found in the official releases | Exploratory construction of content cards and human references |
| **Code2Doc** | First 20 rows of test: Java 10, Python 8, TypeScript 2; code plus existing documentation | An existing docstring for the same code; no AI comparison, no human revision chain | Technical documentation source pool; needs added version/author verification and a new comparison |
| ResearcherBench (supplementary) | The first 10 questions, the expert rubric, and Claude's answers, aligned by id | Same-task AI answers + expert criteria; no human reference articles and no trace | Fidelity evaluation of technical questions, and a source of AI first drafts |

These are readable exploratory samples, not a representative benchmark. Apart from DRB II's 5+5 bilingual tasks, the content available this round is mainly English, and there is no four-cell balance between marketing and technical; it cannot replace the stratified sampling of the main plan.

### SWE-Hero: real execution trajectories and finals are both present, suitable for going on to collect refinements

The [NVIDIA official data card](https://huggingface.co/datasets/nvidia/SWE-Hero-openhands-trajectories) states that this data uses OpenHands and Qwen3-Coder-480B-A35B-Instruct, and releases 34,269 trajectories over 11,766 issues. The issues come from SWE-Gym, R2E-Gym, and SWE-rebench, and some of the issue descriptions are themselves synthetic. The [technical report](https://arxiv.org/abs/2604.01496) is *From SWE-ZERO to SWE-HERO: Execution-free to Execution-based Fine-tuning for Software Engineering Agents* (Ludwig, Ahmad, Majumdar, Ginsburg, 2026).

This package used the HF rows API to download the first 3 rows, all of them pandas tasks; the API's `truncated_cells` is empty. Tool calls such as `execute_bash`, environment echoes, the final `finish` call, and its summary text are all actually visible. The last turn is stored separately in `traces/swe-hero-openhands/samples/row-*.final.json` so it can be read first; the complete record is in `trajectories.3.jsonl`.

Limitations: there is no same-content human revision; the assistant text in a trajectory is not necessarily all user-visible execution updates. `model_patch` is not the same as a patch verified correct in this round, and claims in the final such as "succeeded" or "everything works" have not yet been checked point by point against the logs. This round only checked fields, end states, and whether the API truncated anything; no tests were rerun. The data card declares CC BY 4.0 while each row keeps its source repository's license; these 3 rows are BSD-3-Clause.

### DeepResearch Bench II: the criteria come from expert articles, and the article body text is not in the task files

The [author repository](https://github.com/imlrz/DeepResearch-Bench-II) and the [paper](https://arxiv.org/abs/2601.08536) describe 132 tasks and 9,430 rubrics. In practice the `content` of `tasks_and_rubrics.jsonl` holds `task`, `rubric`, and `blocked`; the last of these stores the source title, author, and URL, not the original body text. The task requires the agent under test not to read that source article; this is part of how the benchmark is built, not a record of a human editing an AI first draft.

The 10 tasks in this package align by idx with `Doubao-DeepResearch/idx-*.md` in the [official HF model report release](https://huggingface.co/datasets/muset-ai/DeepResearch-Bench-II-Dataset), covering low-code, reinforcement learning, Kubernetes scheduling, observability, video encoding, cloud autoscaling, and more. A spot check confirmed that the body-text titles of idx 41/42 match their tasks; no quality annotation was made of all the semantics, citations, and metrics.

The licenses must be kept apart: repository code is Apache-2.0; the tasks/rubrics carry a per-item source license. The authors' current `DATA_LICENSE` states that 129 entries are CC BY 4.0, that idx 26/110 are CC BY-NC 4.0, and that idx 119 is CC0. The 41–50 used here are all CC BY 4.0. The HF model report card is separately labeled Apache-2.0, which cannot be used to override the license of the human source articles.

### CogGen: one pair really does share the same prompt, but the content is still not controlled

The [author repository](https://github.com/NJUNLP/CogGen) and the [data card](https://huggingface.co/datasets/tk1111/coggen-benchmark) list 50 OWID reports as human expert references, keeping the author, date, source URL, and Markdown body text. Another 20 WildSeek references were generated by Gemini Deep Research; **the latter cannot be treated as human ground truth**.

This round keeps OWID main_001–019 plus main_033. The query in `global_deforestation/config.json` is verbatim identical to the `owid_main_033` query, and the latter maps through `source_report_id` to the OWID human article; the pairing file is `coggen/samples/deforestation.same-task-pair.json`. This verifies that the task source is the same; it does not verify that the AI draft and the human draft cover the same facts, nor does it mean that a human read or edited this AI draft. The other oil/gas IoT example has only an AI draft; no human pairing was fabricated for it.

The authors' code can generate logs, context pools, and similar files, which does not mean those complete trajectories have been published. What can be found in the current repository is two final report examples and a config. The OWID text data card is labeled CC BY 4.0 with the original author/links retained; third-party charts and data licenses have to be handled separately. No images were downloaded this round; only the URLs already present in the text are kept.

### FreshWiki and Code2Doc: suitable as raw material, not directly as a preference gold standard

The [FreshWiki data card](https://huggingface.co/datasets/EchoShao8899/FreshWiki) publishes 100 English Wikipedia articles, with sampling focused on heavily edited pages from 2022-02 to 2023-09. The [STORM paper](https://aclanthology.org/2024.naacl-long.347/) studies the pipeline from topic to long article. The 10 samples carry fields such as `title/url/summary/content/references`. The main repository, the paper's archive branch, and the HF file listing turned up no publicly released generation results or conversation logs corresponding to these references; this conclusion is limited to the releases checked this round. The text is CC BY-SA 4.0, and the MIT license of the STORM code cannot be carried over to it. An article's publication date/history window is likewise not proof of authorship free of machine assistance.

The [Code2Doc data card](https://huggingface.co/datasets/kaanrkaraman/code2doc) claims 13,358 code–documentation pairs covering five **programming languages**. The quality and AI-source filtering in the [paper](https://arxiv.org/abs/2512.18748) rely on heuristics; it does not supply this project with human-verified "AI-free" provenance labels or "de-AI-ese" win/loss labels. The existing fields include repo, file path, line number, code, documentation, and quality_score, but not a chain of historical revisions. The data card's CC BY 4.0 and the attribution of the original repositories' MIT/Apache/BSD still have to be preserved together. Splitting randomly by row may also leak the same repo/style into the test set.

## 3. Other targets checked, and why they were excluded

| Target | Verification result | Significance for this project |
|---|---|---|
| [WildSeek](https://huggingface.co/datasets/YuchengJiang/WildSeek) | The official data point is topic + user goal; the standalone release is not a set of human articles, AI reports, or trajectories | A reference for the distribution of needs; do not mistake "real user needs" for "real human writing" |
| [ResearcherBench](https://github.com/GAIR-NLP/ResearcherBench) | 65 frontier AI research questions; Claude assists in distilling insights, then experts construct weighted rubrics; final answers from multiple systems are public | Having expert evaluation criteria does not amount to 65 high-quality human articles. No LICENSE was found in the revision that was checked, so training/redistribution rights are unverified |
| [DeepResearch Bench I](https://github.com/Ayanami0730/deep_research_bench) | 100 research tasks, criteria, reference, and the models' final report files; this round did not establish item-by-item evidence that the reference was written by a human | Usable as a reference for evaluation design, but a gold human draft cannot be inferred from the filename `reference` alone |
| [ReportBench](https://github.com/ByteDance-BandAI/ReportBench) | Research needs and reference bases constructed from expert reviews; the tasks and the citation ground truth are public | The content scope of the human references and of the generation tasks still needs to be aligned; no ready-made human-refined AI draft, nor a full-trajectory triple, was found |
| [Meta DocAgent](https://github.com/facebookresearch/DocAgent) | A multi-agent method for generating code documentation; public code/small examples, using automated checks and LLM evaluation; the [paper](https://arxiv.org/abs/2504.08725) discusses the lack of a gold reference | Methodologically relevant, but no directly downloadable high-quality human–AI rewrite pairs were found; note the distinction from the multimodal DocAgent of the same name |
| [CodeSearchNet](https://github.com/github/CodeSearchNet) | Data and collection method for code and its existing function comments | A raw technical documentation source pool, with no ready-made AI comparison, human revision labels, or workflow trace |

### SWE-smith: 3 extra rows downloaded, kept as a data QA counterexample

The first 3 rows of the tool split in the [official SWE-smith release](https://huggingface.co/datasets/SWE-bench/SWE-smith-trajectories) do have 49/43/65 messages, tool calls, and observations, ending with `submit`; there is no API cell truncation. However, `patch` is empty for two of them, and for the third the `instance_id` is apispec while the patch path is `flashtext/keyword.py`. This is a **suspected correspondence anomaly** found in a local spot check; these 3 rows cannot be used to conclude that the whole dataset is broken, nor can this column be taken directly as the correct final patch.

The [official conversion code](https://github.com/SWE-bench/SWE-smith/blob/main/swesmith/train/traj_mgr/utils.py) also states explicitly that the export of the message history is approximate and that some blocked-action requery entries are not saved in full. The downloaded `tool` table keeps the tool structure, which is more reliable than treating rationale text as a trajectory, but it still cannot be called a lossless record of every event in the environment. So SWE-Hero is the first choice for trace this round, and SWE-smith is kept only under `traces/swe-smith/` for inspection.

## 4. How to build this out into data genuinely suitable for rewrite

1. **Final engineering summary route**: start from SWE-Hero's final and its observable trace. First extract an evidence packet of the actual changes, the tests actually executed and their results, and the unresolved limitations; then have an engineer revise the original final under the same packet. Strictly separate facts supported by the logs from success the agent claims for itself. Keep code/tool/action/observation unchanged; the rewrite touches only the designated user-visible text.
2. **Technical research report route**: start from DRB II's Chinese and English tasks and AI first drafts, and have a research editor refine them after separately verifying sources/facts. CogGen's same-task pair can help in discussing style, but the two full texts cannot be dropped straight into chosen/rejected: the information gap and the coverage gap are not yet controlled.
3. **Technical documentation route**: pin the repo commit, the code, and the context; keep the existing documentation and generate an AI comparison; ask maintainers/technical writers to choose or revise under the same code evidence. Code2Doc's heuristic quality_score is not used as a final weight or a source gold standard.
4. **Annotation and splitting**: first factual pass/fail/uncertain, then compare information density, actionability, tone, and repetition; a style DPO pair is formed only when both sides preserve fidelity. Targets that have been human-refined and have passed review can be used for SFT. Split train/dev/test by repo/project/document family/original task; multiple traces, language versions, and passages must follow their parent task.

The desktop samples in this round have not yet been through the human refinement and fact verification described above, so they are labeled only `candidate/source/example`; they are not given the `human_preferred`, `style_gold`, or `same_content` labels.

## 5. Reproduction and reading coverage

- The GitHub README, the license, and data files use the commit resolved at fetch time; the HF README and directly downloadable files use the dataset revision. See the two manifests for details.
- Code2Doc, SWE-Hero, and SWE-smith use bounded requests to the HF rows API. The actual response and SHA are kept locally; the API row view has not been shown to match the data card revision downloaded at the same time exactly, so it is recorded as a snapshot at access time.
- What was actually verified: that the JSON/JSONL parses, the sample counts, the tools and end states of the 3+3 traces, that the API did not truncate, that one CogGen query is exactly equal, that DRB II's 10 tasks split 5+5 between Chinese and English, and the file hashes. No third-party code was executed, no environment was replayed, and no full-coverage semantic quality judgment was made.
- Reading coverage: for STORM/Co-STORM, ResearcherBench, DRB II, DocAgent, and Code2Doc, the papers' relevant methods/limitations and the official release notes were read; for CogGen, ReportBench, DRB I, and CodeSearchNet, mainly the authors' release notes and file structure; for the newly added SWE-Hero, mainly the official data card and the actual row records, and for SWE-smith, the official export function as well. No claim of full-text reproduction of each paper is made on this basis.

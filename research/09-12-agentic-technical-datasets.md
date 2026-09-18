# Agentic Trace and Technical Writing: Public Data Verification and Small Samples

Verification Date: 2026-09-12. The goal was to find pairable material between AI text, verifiable task/performance evidence, and high-quality human writing. This round involved reading official papers, author repositories, and data cards, and examining actual sample fields; no generative models, training, or replay software environments were run.

**Conclusion:** Observable tool trajectories and final engineering summaries have been obtained, and a verified AI report—a human-referenced article pair—with the same prompt has been found. No readily available gold data could be directly described as "the same content, unchanged facts, and a human-refined AI draft." The most suitable entry point for tool trajectories is NVIDIA's SWE-Hero; for research reports, DeepResearch Bench II and CogGen are recommended. Code comment data is closer to technical documentation, but the human source and quality still need to be verified item by item.

The data is actually stored in the user-specified desktop directory:`~/Desktop/plainvoice/data/local/agentic-technical/`.`source-manifest.json` Record the source, revision, sample selection, license description, and document verification; third-party text is only saved on the desktop and is not included in this repository.

## 1. First, distinguish between the four types of "pairing".

| Type | Answerable Questions | Cannot Directly Infer Anything |
|---|---|---|
| Real-person articles and AI-generated articles on the same topic | Exploring stylistic differences | Controlled information content, facts, purpose, and length |
| Two articles from the same task/prompt | Overall output quality under the same requirements | Both articles express the same set of facts; the real-person draft is a revision of the AI draft |
| Human and AI output under the same code/brief/evidence | Generation quality with shared factual basis | Rewriting preference based on completely equivalent facts |
| AI initial draft and human-refined version, with fact-checking | Goals required for rewriting SFT/DPO | Every human modification is guaranteed to be better |

Another independent dimension is trace. `assistant.tool_calls` Corresponding `tool` The observation log is a record of observable interactions; the model describes "I retrieved..." or `thought` The `/ratione` field is not evidence that the tool actually executed. The exported message history is also not guaranteed to include all retries, environment states, hidden processes, or replayable dependencies.

## 2. Prioritize viewing actual samples

| Data | Desktop Acquired | Pairing and Trace Level | Preferred Use |
|---|---|---|---|
| **SWE-Hero / OpenHands** | 3 tracks; 143, 145, and 117 messages respectively; each retains the final assistant turn,`finish.message` and `model_patch` | Observable actions/observations + final project summary; no human review | Establish execution evidence constraints for the final summary, then collect data for human review |
| **DeepResearch Bench II** | Software Development idx 41–50: 5 in Chinese, 5 in English; 10 Doubao final reports; corresponding tasks, rubrics, and links to human-sourced articles | AI reports for the same task + expert source standards; this package does not include full-text human-sourced articles or traces | Fact and style separation assessment of Chinese and English technical research reports |
| **CogGen / OWID** | 20 human reference texts and tasks; 2 official AI examples; deforestation has been verified to have a verbatim identical query | **1 exact-same-task AI-human reference pair**, not same-content rewrite; no published complete trace | The most intuitive starting point for comparing AI/human research writing |
| **STORM / FreshWiki** | 10 technical, scientific, and related business encyclopedia articles, retaining the text, source URLs, and references | Human reference pool; no corresponding AI output/trajectory found in official releases | Exploratory construction of content cards and human references |
| **Code2Doc** | First 20 lines of test: Java 10, Python 8, TypeScript 2; Code and existing documentation | Existing docstring for the same code; No AI comparison, no human revision chain | Technical documentation source pool; Version/author verification and new comparison needed |
| ResearcherBench (Supplement) | Top 10 questions, expert rubric, Claude answers, aligned by ID | AI answers for the same task + expert criteria; no human reference articles or traces | Fidelity assessment of technical issues and AI initial draft source |

These are readable exploratory samples, not representative benchmarks. Apart from the 5+5 bilingual task in DRB II, the available content in this round is mainly in English, and there is no four-panel balance between marketing and technical; therefore, it cannot replace the stratified sampling of the main scheme.

### SWE-Hero: It contains both the actual execution trajectory and the final result, making it suitable for further collection and refinement.

[NVIDIA official data card](https://huggingface.co/datasets/nvidia/SWE-Hero-openhands-trajectories)This data was generated using OpenHands and Qwen3-Coder-480B-A35B-Instruct, resulting in 34,269 tracks and 11,766 issues. The issues originated from SWE-Gym, R2E-Gym, and SWE-rebench, and some issue descriptions were also synthesized.[Technical Report](https://arxiv.org/abs/2604.01496)From SWE-ZERO to SWE-HERO: Execution-free to Execution-based Fine-tuning for Software Engineering Agents (Ludwig, Ahmad, Majumdar, Ginsburg, 2026).

This package uses the HF rows API to download the first 3 rows, all of which are pandas tasks; API `truncated_cells` Empty. Actually visible. `execute_bash` Tool calls, environment feedback, and final `finish` The call and its summary text. The final round is placed separately. `traces/swe-hero-openhands/samples/row-*.final.json` For easy reading first; complete record in `trajectories.3.jsonl`.

Limitations: No real-person content revisions; assistant text in the trajectory is not necessarily an update visible to the user.`model_patch` This does not equate to a correct patch verified in this round. Claims such as "success" and "all normal" in the final statement have not been individually compared with the logs. This round only checked fields, end states, and API truncation; no tests were rerun. The data card declares CC BY 4.0, while retaining the source repository license in each line; these three lines are BSD-3-Clause.

### DeepResearch Bench II: The standards are derived from expert articles, but the full text of these articles is not included in the task file.

[Author's Repository](https://github.com/imlrz/DeepResearch-Bench-II)and[paper](https://arxiv.org/abs/2601.08536)It introduces 132 tasks and 9,430 rubrics. (Actual) `tasks_and_rubrics.jsonl` of `content` Include `task`,`rubric`,`blocked` The latter stores the source title, author, and URL, not the original text. The task requires the tested agent not to read this source article; this is part of the benchmark construction and not a record of human editing of the AI's initial draft.

This package contains 10 tasks and [HF Official Model Report Released](https://huggingface.co/datasets/muset-ai/DeepResearch-Bench-II-Dataset)middle `Doubao-DeepResearch/idx-*.md` Aligned by idx, covering low-code, reinforcement learning, Kubernetes scheduling, observability, video encoding, and cloud scaling. A spot check of the text titles and task correspondence in idx 41/42 revealed that not all semantics, citations, and metrics were quality-annotated.

Licenses must be separated: repository code Apache-2.0; task/rubrics uses a line-by-line license. The author currently... `DATA_LICENSE` It specifies that 129 entries are CC BY 4.0, idx 26/110 are CC BY-NC 4.0, and idx 119 is CC0. Entries 41–50 in this report are all CC BY 4.0. The HF model report card is also labeled Apache-2.0, which cannot be used to override the licenses of human-derived articles.

### CogGen: A pair of people did indeed receive the same prompt, but the content is still not under control.

[Author's Repository](https://github.com/NJUNLP/CogGen)and[Data card](https://huggingface.co/datasets/tk1111/coggen-benchmark)Fifty OWID reports are listed as human expert references, retaining the author, date, source URL, and Markdown text. An additional 20 WildSeek references were generated by Gemini Deep Research; **the latter cannot be considered as human ground truth.**

This time, we retain OWID main_001–019 and add main_033.`global_deforestation/config.json` query and `owid_main_033` The queries are identical word for word, the latter is obtained through... `source_report_id` Corresponding OWID human articles; the pairing file is `coggen/samples/deforestation.same-task-pair.json` This verifies that the fact that the AI and human drafts from the same task source have the same coverage does not mean that humans have seen/modified the AI draft. Another oil/gas IoT example only has an AI draft; no fake human pairings were found.

The author's code can generate logs, context pools, and other files, but this does not mean that these complete tracks have been published. The current repository contains two final report examples and a configuration file. OWID text data is CC BY 4.0, and the original author/link is retained; third-party charts and data licenses need to be handled separately. No images were downloaded this time; only URLs existing within the text are retained.

### FreshWiki and Code2Doc: Suitable as primary source material, not directly used as preferred gold labels.

[FreshWiki Data Card](https://huggingface.co/datasets/EchoShao8899/FreshWiki)Published 100 English Wikipedia articles, focusing on high-editability pages from February 2022 to September 2023.[STORM paper](https://aclanthology.org/2024.naacl-long.347/)The study examines the process from topic selection to the development of a full-length article. Ten sample articles are available. `title/url/summary/content/references` Fields such as [list of fields]. No publicly generated results or conversation logs corresponding to these references were found in the main repository, paper archive branch, and HF file list; this conclusion is limited to publications examined in this round. The text is CC BY-SA 4.0 and cannot be used with the STORM code MIT. The article publication date/history window is also not a non-machine-assisted proof of authorship.

[Code2Doc Data Card](https://huggingface.co/datasets/kaanrkaraman/code2doc)It claims 13,358 code-document pairs, covering five **programming languages**.[paper](https://arxiv.org/abs/2512.18748)The quality and AI source filtering rely on heuristics; there are no human-verified "AI-free" identity labels or "AI-free" win/loss labels for this project. Existing fields include repo, file path, line number, code, documentation, and quality_score, but not a historical modification chain. Data cards CC BY 4.0 and their original MIT/Apache/BSD repository affiliations should still be preserved. Randomly splitting by line may allow similar repo/style leaks to the test suite.

## 3. Other verification targets and reasons for exclusion

| Object | Verification Results | Significance to this Project |
|---|---|---|
| [WildSeek](https://huggingface.co/datasets/YuchengJiang/WildSeek) Official data points are topic + user goals; independently published content is not real-person articles/AI reports/trajectory sets | Demand distribution reference; do not mistake "real user needs" for "real-person writing" |
| [ResearcherBench](https://github.com/GAIR-NLP/ResearcherBench) | 65 cutting-edge AI research questions; Claude helps refine insights, then experts construct weighted rubrics; publicly available final answers from multiple systems | Expert evaluation criteria are included, but this does not equate to 65 high-quality articles by real researchers. No license found for the revision check; training/redistribution permissions not verified.
| [DeepResearch Bench I](https://github.com/Ayanami0730/deep_research_bench) | 100 research tasks, criteria, references, and the final model report; evidence of human writing for which no references were established in this round | Can be used as a reference for evaluation design; do not infer the quality of a gold-level human manuscript solely from filename references |
| [ReportBench](https://github.com/ByteDance-BandAI/ReportBench) | The research needs and references are constructed from expert reviews; the task and citation ground truth are made public. | The content scope of human references and generated tasks still needs to be aligned; no ready-made human-refined AI drafts or full-track three-piece sets were found.
| [Meta DocAgent](https://github.com/facebookresearch/DocAgent) | Methods for generating multi-agent code documentation; public code/small examples, using automatic checks and LLM evaluation;[paper](https://arxiv.org/abs/2504.08725)The discussion lacks a gold reference | Methodologically related, no high-quality human-AI rewrite pairs were found that can be directly downloaded; note the distinction from the multimodal DocAgent with the same name |
| [CodeSearchNet](https://github.com/github/CodeSearchNet) | Data and collection methods for code and existing function comments | Original technical documentation source pool, no ready-made AI comparisons, human revision tags, or workflow traces |

### SWE-smith: Download 3 additional records, keep them for data QA counterexamples.

[Official SWE-smith release](https://huggingface.co/datasets/SWE-bench/SWE-smith-trajectories)The first three entries of the tool split do indeed contain 49/43/65 messages, tool calls, and observations. `submit` End; no API cell truncation. However... `patch` Two are empty, the other one `instance_id` The patch path is for apispec. `flashtext/keyword.py` This is a **suspected anomaly** discovered during local sampling. These three rows do not indicate that the entire dataset is invalid, nor can they be directly taken as the correct final patch.

[Official conversion code](https://github.com/SWE-bench/SWE-smith/blob/main/swesmith/train/traj_mgr/utils.py)It also explicitly states that the exported message history is approximate, and some blocked-action requeries are not fully saved. (Downloaded) `tool` While preserving the tool structure is more reliable than using rationale text as a trace, it still cannot be considered a lossless record of all events in the environment. Therefore, SWE-Hero is the preferred choice for this round of tracing, while SWE-smith is only used for... `traces/swe-smith/` For inspection.

## 4. How to supplement the data to be truly suitable for rewriting?

1. **Final Project Summary Roadmap:** Starting with the final and observable traces of SWE-Hero. First, extract evidence packets containing actual changes, actual test execution and results, and unresolved limitations; then have engineers revise the original final version using the same packets. Strictly distinguish between facts supported by logs and agent-reported success. Keep code/tools/actions/observations unchanged, and rewrite only the specified text visible to the user.
2. **Technical Research Report Roadmap:** Starting with the English-Chinese task and AI draft of DRB II, please have the research editor refine the report after verifying the sources/facts. CogGen's same-task pair can help with discussion style, but two full papers cannot be directly placed in chosen/rejected: information gap and coverage gap have not yet been controlled.
3. **Technical Documentation Approach:** Fixed repo commits, code, and context; existing documentation preserved and AI-generated comparisons generated; maintainers/technical authors should select or revise under the same code evidence. Code2Doc's heuristic quality_score is not used as the final weight or source gold standard.
4. **Annotation and Segmentation**: First, perform factual pass/fail/uncertainty checks, then compare information density, operability, tone, and repetition; only when both are accurate are style DPO pairs formed. Human-refined and verified targets can be used for SFT. Divide into train/dev/test segments by repo/project/document family/original task; multiple traces, language versions, and paragraphs must follow the parent task.

The desktop samples in this round have not yet undergone the aforementioned manual refinement and fact-checking, so they are only labeled... `candidate/source/example` Not granted `human_preferred`,`style_gold` or `same_content` Label.

## 5. Reproduction and Reading Coverage

- The GitHub README, license, and data files use the commits parsed at the time of retrieval; the HF README and directly downloadable files use the dataset revision. See both manifests for details.
- Code2Doc, SWE-Hero, and SWE-smith use bounded requests to the HF rows API. The actual response and SHA remain local; the API row view is not proven to be completely consistent with the concurrently downloaded data card revision, and is therefore recorded as a snapshot at the time of access.
- The test verified JSON/JSONL parsing capability, sample size, 3+3 trace tools and termination status, API untruncation, CogGen query complete equality, DRB II 10 tasks with 5+5 Chinese and English characters, and file hashing. No third-party code was executed, the replay environment was not tested, or full semantic quality assessment was performed.
- Reading level: For STORM/Co-STORM, ResearcherBench, DRB II, DocAgent, and Code2Doc, focus on the paper's methods/limitations and official release notes; for CogGen, ReportBench, DRB I, and CodeSearchNet, focus on the author's release notes and file structure; for the newly added SWE-Hero, focus on the official data card and actual line records; for SWE-smith, also read the official export functions. This does not constitute a claim of fully reproducing each paper.

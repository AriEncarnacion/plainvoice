# Desktop data packets and first rewrite sampling

2026-09-12. The user explicitly requested that the data be downloaded to the desktop; the original data and a copy of the article are stored on [location missing]. `~/Desktop/plainvoice/data/local/` This Git repository was not uploaded. The following is the actual completion record, which differs from the previous collection suggestions.

## Six sets of publicly available data have been downloaded.

`datasets/` A total of 105 files, 610,783,737 bytes (approximately 611 MB, including the IteraTeR compressed package and decompressed data). All six sets contain the complete publicly available data files selected for this study, without any partial files truncated due to size limitations; versions not published by the authors or otherwise restricted are not included.

| Source | Locally measured scale |
|---|---|
| [AdParaphrase v2.0](https://github.com/CyberAgentAILab/AdParaphrase-v2.0) | main 22,337 pairs, of which 16,460 pairs were won by an equal majority; pt 8,721 triples |
| [IteraTeR](https://github.com/vipulraheja/iterater) | FULL 196,987 sentence pairs / 31,631 document revisions; HUMAN 4,018 sentence pairs / 559 document revisions |
| [arXivEdits](https://github.com/chaojiang06/arXivEdits) | 751 papers, 1,790 versions; 1,000 punctuation marks |
| [MCTS](https://github.com/blcuicall/mcts) | 723 Original sentences × 5 Manual references; 691,474 Machine-generated sentence pairs |
| [ASSET](https://github.com/facebookresearch/asset) | 2,359 Original sentences × 10 Manually reviewed |
| [CoEdIT](https://huggingface.co/datasets/grammarly/coedit) | train 69,071; validation 1,712 |

The original README, license file or data card declaration, fixed revision, file URL, SHA-256, record count, and human/machine origin are all preserved in the package manifest. JSON/JSONL/CSV parsing, parallel row count, ZIP CRC, and SHA-256 checks of the 104 manifest files pass. Records at different granularities overlap, so numbers in the table cannot be directly added together.

Previously, MCTS only read the Git LFS pointer; this time, the GPLv3 LICENSE content has been obtained. This does not automatically indicate the training rights for all upstream news content. The unpublished instances of IteraTeR Plus/v2 and CoEdIT were not obtained through other channels. Downloading and verifying the architecture does not equate to completing training from all sources or confirming the intended use for redistribution.

## Agentic trace and technical writing

`agentic-technical/` Save separate source descriptions and small samples. See the distinction between research and fields. [Agentic/Technical Writing Data Survey](research/09-12-agentic-technical-datasets.md).

A more relevant entry point for rewriting engineering summaries is [NVIDIA SWE-Hero OpenHands trajectories](https://huggingface.co/datasets/nvidia/SWE-Hero-openhands-trajectories)This study selected three tracks with observable tool calls, environmental feedback, and final engineering summaries. These provide constrained and rewriteable execution data, but no corresponding human revisions are yet available. The model's description of "successful testing" should not be taken as independently verified fact; the tracks should be reviewed.

Research report data is further divided into "Task + Expert Standards + AI Report", "Human Reference Articles", and "Human and AI Reports on the Same Topic". Same topic does not guarantee content equivalence, and publishing the final draft does not equate to publishing the complete action trace. In this round, no complete "trajectory + AI draft + high-quality human revised draft with the same content" triple was found that could be directly used for this project.

## Six sources and six sets of generated short fragment rewrites

The entrance is `human-rewrite-pairs/review.html` The page displays source snippets and AI rewrites side-by-side, allowing users to record whether the content is suitable for pairing, personal preferences, notes, and export JSON. It's an exploratory review with visible sources, not a blind review experiment.

| Source | Publication Date / Source Boundary | Length of this Input |
|---|---|---:|
| [Howard Marks: How Quickly They Forget](https://www.oaktreecapital.com/docs/default-source/memos/2011-05-25-how-quickly-they-forget.pdf) | May 25, 2011, PDF Authorization and Date | 108 English Words |
| [Howard Marks: There They Go Again . . . Again](https://www.oaktreecapital.com/docs/default-source/memos/there-they-go-again-again.pdf) | 2017-07-26, PDF Authorization and Date | 119 English Words |
| [Stripe: Designing robust and predictable APIs with idempotency](https://stripe.com/blog/idempotency) | Brandur Leach, 2017-02-22 | 99 English words |
| [Stripe: Idempotent requests](https://docs.stripe.com/api/idempotent_requests) The current document has no confirmed original date or individual author; it cannot be considered as definitive pre-AI human text. | 104 English words |
| [Ruan Yifeng: RESTful API Design Guide](https://www.ruanyifeng.com/blog/2014/05/restful_api.html) 2014-05-22 | 171 Chinese characters / 257 total characters |
| [Ruan Yifeng: How to reduce the complexity of software?](https://www.ruanyifeng.com/blog/2018/09/complexity.html) | 2018-09-10; Chinese notes based on Ousterhout's speech and book review | 164 Chinese characters / 240 total characters |

Complete official documents and extracted text are available at `sources/` Page numbers/sections and original dates are evidenced in the metadata of each source. Historical articles are saved as the current download version, without verbatim comparison with historical web archives. The quality of authorship and dates is not guaranteed. All six groups are maintained... `unreviewed_candidate` The original text does not presuppose that the winner is the winner.

## Actual generation process and limitations

1. Initially, I tried using the native Codex CLI 0.144.6 to call the configuration. `gpt-6-astra` The service returned a "Model requires update CLI" message, therefore the attempt did not result in a rewrite; the failure log is kept separately. `generation-cli-failed/` No user configuration was upgraded or changed.
2. Six rewrites were then generated using the new Codex subagent.`fork_turns=none` This task does not inherit the previous discussion; the input consists of six short fragments, and the instructions require rewriting them in your own structure and wording while retaining the facts. There are no requirements to disable a vocabulary or "intentionally add an AI flavor".
3. The original six sets of outputs from the sub-agent are saved directly; the main agent does not refine them further. The actual prompts, inputs, responses, and operational instructions are provided below. `generation/` Output IDs/quantity, consistency with original text fragments, and a small number of technical identifiers passed mechanical checks; however, mechanical checks were not treated as semantic equivalence or human evaluation.

Limitations: The six paragraphs were generated in the same task and are still subject to Codex system/developer instructions. The returned tool metadata does not provide precise backend checkpoints, token usage, or costs; the execution log indicates that no data was exposed and no false data was generated. This short text generation is not a complete agent tool trajectory. It can only explore word and paragraph rhythm and cannot prove the argumentation, structure, or technical integrity of the entire article.

This batch of materials has not yet undergone independent review, nor has a judge or rewrite model been trained. Good original texts may not necessarily become worse after being rewritten by a model; reviewers should allow for model wins, ties, and content changes. Only manually approved pairs will proceed to the next step of annotation and usage classification.

## Reusable auxiliary scripts

- `scripts/build_rewrite_review.py` Use local `pairs.json` Build review HTML without external dependencies.
- `scripts/run_rewrite_pilot.py` This is a CLI sampling assistant that records prompts, structured output, and runtime status. Attempts with the older local CLI failed, and this path cannot be reported as a successful generator for this round; the actual successful path is the isolated subagent mentioned above.

Third-party original texts, rewritten content, downloaded corpora, and runtime logs are only stored in the local data package; this Git repository stores original research notes and auxiliary scripts.

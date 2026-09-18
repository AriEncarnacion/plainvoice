# Desktop data packet and the first rewrite sampling

2026-09-12. The user explicitly asked for the download to go to the desktop; the raw data and the copies of the articles are stored at `~/Desktop/plainvoice/data/local/` and were not uploaded to this Git repository. What follows is a record of what was actually completed, as distinct from the earlier collection proposals.

## Six public datasets downloaded

`datasets/` holds 105 files totalling 610,783,737 bytes (about 611 MB, including the IteraTeR archive and the extracted data). For all six sets the complete public data files selected for this round were obtained, with no partial files truncated for size; versions the authors have not released, or that are otherwise restricted, are not included.

| Source | Locally measured scale |
|---|---|
| [AdParaphrase v2.0](https://github.com/CyberAgentAILab/AdParaphrase-v2.0) | main 22,337 pairs, of which 16,460 pairs passed an equivalence majority vote; pt 8,721 triples |
| [IteraTeR](https://github.com/vipulraheja/iterater) | FULL 196,987 sentence pairs / 31,631 document revisions; HUMAN 4,018 sentence pairs / 559 document revisions |
| [arXivEdits](https://github.com/chaojiang06/arXivEdits) | 751 paper sets, 1,790 versions; 1,000 human-annotated sentence pairs |
| [MCTS](https://github.com/blcuicall/mcts) | 723 source sentences × 5 human references; 691,474 machine-constructed sentence pairs |
| [ASSET](https://github.com/facebookresearch/asset) | 2,359 source sentences × 10 human references |
| [CoEdIT](https://huggingface.co/datasets/grammarly/coedit) | train 69,071; validation 1,712 |

The original README, the license file or data-card statement, the pinned revision, the file URL, SHA-256, record counts, and human/machine provenance are all kept in each package's manifest. JSON/JSONL/CSV parsing, parallel line counts, ZIP CRC, and the SHA-256 checks on the 104 manifest-listed files all pass. Records at different granularities overlap, so the numbers in the table cannot simply be added together.

Previously only the Git LFS pointer could be read for MCTS; this time the body of the GPLv3 LICENSE was obtained, which does not automatically establish training rights over all the upstream news content. The unreleased instances of IteraTeR Plus/v2 and CoEdIT were not obtained through other channels. Downloading and structural verification is not the same as having confirmed training and redistribution use for every source.

## Agentic trace and technical writing

`agentic-technical/` holds separate source notes and small samples. For the research and the differences between fields, see [agentic / technical writing dataset survey](research/09-12-agentic-technical-datasets.md).

The entry point closest to rewriting an engineering summary is [NVIDIA SWE-Hero OpenHands trajectories](https://huggingface.co/datasets/nvidia/SWE-Hero-openhands-trajectories): this round extracted 3 trajectories with observable tool calls, environment feedback, and a final engineering summary. They supply execution material that can constrain a rewrite, but there is as yet no corresponding human-edited draft. Statements the model narrates, such as "the test succeeded", must not be taken as independently verified fact; the trajectory should be checked back against.

Research-report data divides further into "task + expert criteria + AI report", "human reference articles", and "human and AI reports on the same topic". The same topic does not guarantee equivalent content, and publishing a final draft is not the same as publishing the complete action trace. This round found no ready-made "trajectory + AI draft + high-quality human rewrite of the same content" triple complete enough to be used directly in this project.

## Six sources and six generated short-fragment rewrites

The entry point is `human-rewrite-pairs/review.html`. The page presents the source fragment and the AI rewrite side by side, and supports recording whether they are suitable as a pair, personal preference, and notes, as well as exporting JSON. It is an exploratory review with the sources visible, not a blind evaluation experiment.

| Source | Publication date / source boundary | Input length this round |
|---|---|---:|
| [Howard Marks: How Quickly They Forget](https://www.oaktreecapital.com/docs/default-source/memos/2011-05-25-how-quickly-they-forget.pdf) | 2011-05-25, PDF byline and date | 108 English words |
| [Howard Marks: There They Go Again . . . Again](https://www.oaktreecapital.com/docs/default-source/memos/there-they-go-again-again.pdf) | 2017-07-26, PDF byline and date | 119 English words |
| [Stripe: Designing robust and predictable APIs with idempotency](https://stripe.com/blog/idempotency) | Brandur Leach, 2017-02-22 | 99 English words |
| [Stripe: Idempotent requests](https://docs.stripe.com/api/idempotent_requests) | Current documentation, with no confirmed original date or individual author; it cannot be treated as definitively pre-AI human text | 104 English words |
| [Ruan Yifeng: RESTful API Design Guide](https://www.ruanyifeng.com/blog/2014/05/restful_api.html) | 2014-05-22 | 171 Chinese characters / 257 total characters |
| [Ruan Yifeng: How to reduce the complexity of software?](https://www.ruanyifeng.com/blog/2018/09/complexity.html) | 2018-09-10; Chinese notes based on Ousterhout's talk and a book review | 164 Chinese characters / 240 total characters |

The complete official files and the extracted text are in `sources/`, and the page/section numbers and the evidence for the source date are in each source's metadata. For the older articles what is stored is the version downloaded this time, which was not compared word-for-word against historical web archives. A byline and a date do not guarantee quality either. All six sets stay at `unreviewed_candidate`; the source text is not presumed to be the winner.

## The actual generation process and its limits

1. The first attempt used the local Codex CLI 0.144.6 to call the configured `gpt-6-astra`. The service returned "the model requires a newer CLI", so that attempt produced no rewrite; the failure log is kept separately in `generation-cli-failed/`, and no user configuration was upgraded or changed.
2. Six sets of rewrites were then generated through a fresh Codex subagent with `fork_turns=none`, which does not inherit the earlier discussion in this task; the input was the six short fragments, and the instruction asked for a rewrite in the model's own structure and wording while preserving the facts, with no banned-word list and no requirement to "deliberately add AI-ese".
3. The subagent's six raw outputs are saved as they came; the main agent did not polish them again. The actual prompt, inputs, responses, and run notes are in `generation/`. Output IDs and counts, consistency with the source fragments, and a small number of technical identifiers passed a mechanical check; the mechanical check was not treated as semantic equivalence or as a pass in human evaluation.

Limits: the six passages were generated within the same task and are still subject to the Codex system/developer instructions. The tool metadata returned did not provide a precise backend checkpoint, token usage, or cost; the run record states that these were not exposed, and nothing was filled in falsely. This short-text generation is not a complete agent tool trajectory. It can only explore wording and paragraph rhythm; it cannot prove the argument, structure, or technical completeness of a whole article.

This batch of material has not yet undergone independent human evaluation, and no judge or rewrite model has been trained. A good source text does not necessarily get worse when a model rewrites it; review should allow for model wins, ties, and changes in content. Only a pair a human has approved goes on to the next step of annotation and use classification.

## Reusable helper scripts

- `scripts/build_rewrite_review.py`: builds a dependency-free review HTML from a local `pairs.json`.
- `scripts/run_rewrite_pilot.py`: a CLI sampling helper that records the prompt, the structured output, and the run status. The attempt with the old local CLI failed, so this path cannot be reported as this round's successful generator; the actual successful path is the quarantined subagent described above.

Third-party source texts, rewritten content, the downloaded corpora, and run logs are kept only in the local data packet; this Git repository holds the original research notes and the helper scripts.

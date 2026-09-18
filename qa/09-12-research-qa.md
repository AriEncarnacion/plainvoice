# Research coverage and verification record

This round is targeted background research, not a PRISMA-style systematic review. The search runs through 2026-09-12; the first round was research only, after which, under the user's authorization, the desktop data download and the generation of six short-fragment candidates were completed. Independent human evaluation, model training, and a real benchmark have not yet been carried out. The goal is to cover four equally prioritized cells — Chinese/English and technical/marketing; the six sources here are exploratory sampling, not a balanced four-cell benchmark.

## Scope of the evidence

The four literature memos list 40 paper/dataset studies in total, plus 5 official model cards and release evidence. The emphasis covers linguistic style and homogenization, AI source detection and bias, editing and style transfer, human/LLM evaluation, parameter-efficient training, preference optimization, and industry writing experiments.

A same-day follow-up added a literature-first reading guide and filled in the direct humanization prior art that the first round covered weakly: the three papers DIPPER, HUMPA, and CoPA, plus the community Unslopper model card, listed separately by evidence level. CoPA's human evaluation table and Unslopper's quality table have been read back, making clear the different conclusions relative to the source draft and relative to a weak baseline; no claim of having reproduced the effect is made on that basis.

The primary sources are mainly ACL Anthology, arXiv author versions, PNAS, Nature, Science Advances, ICML/ICLR, and publisher body text. Model configurations come from the publishing organization's model cards and official release notes. Commercial promotion, social posts, and second-hand interpretation encountered in the search carry no evidential weight for the conclusions.

Each memo records its reading scope and limits; for some datasets only the official abstract and metadata were verified, and no complete reproduction was falsely claimed. All scores from the literature belong to the models, tasks, and populations the papers specify, not to Plainvoice. Some 2026 studies are still at preprint stage, or the reading scope differs between the published version and the author version, which has been noted.

## Search directions

- AI writing style / AI-ese / grammatical and rhetorical variation / lexical overrepresentation / homogenization.
- Human and LLM judge bias / non-native detection bias / RAID / M4 / style transfer evaluation / factual preservation.
- Text editing instruction tuning / CoEdIT / IteraTeR / Chinese revision and simplification.
- WritingBench / marketing creativity / copywriting / technical writing evaluation / real marketing experiments.
- LoRA / QLoRA / DPO / online preference coverage / reward overoptimization / current official model cards.

## Important corrections

1. Dense syntax and a shortage of useful information can coexist; the two are not contradictory.
2. A historical human source does not automatically equal high quality; AI-source discrimination cannot be used as a quality label.
3. The base/instruct comparison did not isolate SFT, RLHF, or any other specific post-training factor, so it cannot support single-factor causal attribution.
4. No sufficient direct empirical evidence was found this round for overuse of the Chinese `不是，而是` (*"not X, but rather Y"*) construction, so it is kept as a product hypothesis awaiting verification.
5. Wine Access's custom small model and the prompted Claude sit in different experimental rounds, so they cannot be treated as a controlled ablation of training versus prompting.
6. FActScore-style precision does not capture recall of necessary information; embedding similarity is likewise not enough to prove the absence of stance drift.
7. A model card supplies existence, structure, and licensing information; it cannot prove that the recommended size is optimal for this task. Qwen's LM parameter count is not the total storage of the complete multimodal checkpoint.
8. The VRAM table distinguishes the theoretical lower bound for weights from actual device planning; the price example is a hypothetical sensitivity analysis, not a procurement quote or spending already incurred.
9. The rating scales, learning curves, and arm numbering in each memo are research options; the unified version to be executed is in the main plan and the annotation protocol, whose entry points are marked.

## Independent methodology review

A separate independent review of the main plan found and filled in three rules:

- Handling of both sides failing, cases that cannot be judged, missing evaluations, empty output, no majority among reviewers, and factual disputes: keep the full task denominator; undecided labels are given as upper and lower bounds and must not be deleted.
- The non-inferiority margin and the ceiling on major errors for each cell must be fixed before the final test; finding no significant degradation cannot be read as having proved non-inferiority.
- Agreement statistics use only the independent raw scores from before adjudication, and must not mix in an adjudicator who only rates disagreements.

The annotation estimate of 800 items × 3 people × 3–5 minutes = 120–200 hours was re-checked; n=200 per cell was confirmed to be insufficient to support very narrow effect or low error-rate commitments. Cost and sample size still need pilot calibration.

## Results not yet established

Collection follow-up: six public datasets totalling 105 files / 610,783,737 bytes; structure, parallel line counts, ZIP CRC, and manifest SHA-256 all pass. The MCTS license went from previously unread to the body of the GPLv3 LICENSE having been obtained, which still does not extrapolate to upstream news usage rights. The six official source texts and the six independent-context subagent rewrites are all saved on the desktop; the output mapping and a small number of technical identifiers have been checked, and every human-evaluation label is empty. The failed call from the old CLI and the actual subagent generation are archived separately. HTML local references and the six source frames pass their checks; no claim is made of having passed human evaluation or a full browser interaction test.

Ground truth follow-up: the author entry points for AdParaphrase v2.0, IteraTeR, arXivEdits, MCTS, ASSET, and CoEdIT were verified, and an independent collection plan was added. It distinguished ad paraphrase/preference labels from AI-ese labels, human editing from automatic labelling, and the scale used in the papers from the scale actually released. The license for the complete MCTS data was not verified this round; CoEdIT's 82K is the paper's scale, while the public `train` split is about 69K. The full corpus was not downloaded, and the proposed 80-item collection plan is not counted as gold already collected.

The collection plan went through an independent methodology review: the arithmetic of 80 items, 20 in each of the four cells, and 160 pair reviews from two first-pass raters holds. It was made explicit that anything entered as DPO chosen must pass the constraints, and that ties, cases where both drafts fail, and unresolved `uncertain` do not convert directly into ordinary DPO win/loss labels.

There is no credible basis for declaring one model or training method the winner across the four scenarios, and there is no calibrated, unified "AI-ese" score. No bulk training license for historical marketing copy has been obtained, no company material has been collected, no training weights have been downloaded, and no paid compute has been started. The current repository is a research starting point that can be carried forward.

Markdown internal links, the file listing, and the Git commit diff are checked before pushing. Only this project's original research documents and templates go into the personal repository; the parent management workspace files are not included.

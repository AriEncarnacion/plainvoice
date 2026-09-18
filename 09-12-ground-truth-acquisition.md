# Where ground truth comes from, and how it becomes training data

2026-09-12. Status: literature verification and a collection plan; there is as yet no collected, independently human-evaluated Plainvoice gold. The quantities below are pilot proposals, not data already obtained or an optimal scale proven by any paper. The four cells of Chinese/English × technical documentation/marketing have equal priority. Scoring and anomaly handling follow the [annotation protocol](09-12-annotation-protocol.md) and the [main plan](09-12-research-and-experiment-plan.md).

## 1. The most useful unit: rewrite comparison under the same input

The user's framing — "the same content, one heavy with AI-ese, the other natural and easy to read" — is a good pairing idea. A more precise unit of record is:

`task and audience + source draft + content basis and constraints + candidates A/B + independent human evaluation`

"The same content" has to be pinned down to facts, intent, conditions, and certainty, not merely to the same topic or product. When two articles about the same product are compared, if one of them supplies extra price, customer-story, or feature information, then content differences have been mixed into the preference and it can no longer be attributed to the writing alone.

Whether the author is a human or a model is stored separately from quality. A human-written piece can also be full of boilerplate, and a model draft can also need no revision; both sides may come from models. Do not fix a winner before evaluation, and do not force every pair to produce a clear "good/bad" verdict. Retain tie, both-sides-unqualified, and cannot-judge outcomes.

Naturalness, readability, and actual adoption preference are evaluated separately. A technical specification may be formal and may repeat necessary constraints; an advertisement may use rhythm or metaphor. A sentence pattern cannot become a negative example merely because it occurs.

A strict "pure style" subset requires that important propositions are preserved in both directions. If the source draft itself contains an error and the editor corrects it on the basis of the source pack, that should be labelled separately as a fact-repair task; such improvements cannot all be counted as the effect of removing AI-ese. Without an external basis, one can only check fidelity relative to the source draft, and cannot claim that the facts are correct in reality.

## 2. Existing papers and public data: what can actually be obtained

The entry points below were verified in the initial research round; later the same day, public data was downloaded to the desktop at the user's request — see the [actual collection record](09-12-local-data-and-rewrite-pilot.md). Paper data can supply candidates and auxiliary tasks; when reused, this project's own human evaluation still has to be added.

| Data and entry point | Actual data | Use and boundaries for this project |
|---|---|---|
| [AdParaphrase v2.0, Findings ACL 2025](https://aclanthology.org/2025.findings-acl.788/); [author data repository](https://github.com/CyberAgentAILab/AdParaphrase-v2.0) | Japanese advertising: 16,460 semantically equivalent copy pairs, each with attractiveness preferences from 10 annotators; plus 8,721 same-input two-candidate records for preference tuning. | The data construction method closest to this project, but it is not Chinese or English and it has no AI-ese labels. Borrow the method; it cannot serve directly as four-cell gold. The repository is marked CC BY-NC-SA 4.0; permission for commercial training use cannot be assumed. |
| [IteraTeR, ACL 2022](https://aclanthology.org/2022.acl-long.250/); [author repository](https://github.com/vipulraheja/iterater) | Real English revisions. The HUMAN subset has 4,018 sentence pairs with human edit-intent labels; FULL has 196,987 sentence pairs whose intent labels are model-predicted. | Filter first for language and clarity edits, exclude meaning-changed, then re-check whether the later draft is actually better. A human edit cannot be taken as a guarantee. The original version is public; Plus/v2 additionally requires Newsela access and contacting the authors. The root repository's Apache-2.0 does not by itself establish that the source texts from every origin fall under the same license. |
| [arXivEdits, EMNLP 2022](https://arxiv.org/abs/2210.15067); [author repository](https://github.com/chaojiang06/arXivEdits) | 1,039 adjacent-version pairs from 751 papers; plus 2,122 edits with human intent annotation across 1,000 sentence pairs. | The Improve Language subset can supply technical-writing candidates; papers and product documentation still differ in domain. Edits that update an experiment or a claim must be separated out. Source-text licenses are granted per paper/version; one repository license cannot cover every text. |
| [MCTS, LREC-COLING 2024](https://aclanthology.org/2024.lrec-main.969/); [author repository](https://github.com/blcuicall/mcts) | 723 original Chinese news sentences, each with 5 human simplification references. Plus 691,474 machine-constructed pseudo-parallel training sentence pairs. | Auxiliary evaluation of readability, not marketing/technical-documentation gold. Simplification is allowed to drop non-essential information, so information retention has to be re-checked. Pseudo-parallel training data cannot count as human gold. The same-day download follow-up obtained the GPLv3 LICENSE body text from Git LFS; the specific permitted use of the upstream news text still has to be verified source by source. |
| [ASSET, ACL 2020](https://aclanthology.org/2020.acl-main.424/); [author repository](https://github.com/facebookresearch/asset) | 2,359 original English sentences, each with 10 human simplification references; officially dev/test, with no train split. | Shows that "one draft can have several reasonable rewrites" and suits simplification diagnostics; it is not an AI-ese label, and deletion cannot be treated as fidelity by default. CC BY-NC 4.0. |
| [CoEdIT, EMNLP 2023](https://aclanthology.org/2023.findings-emnlp.350/); [data card](https://huggingface.co/datasets/grammarly/coedit); [public-version notes](https://github.com/vipulraheja/coedit) | English edit instruction / source text / target rewrite. The paper's training set is 82K and the public train split about 69K; roughly 13K train and 1.5K validation are withheld for licensing reasons. | Auxiliary editing SFT. Grammar, formalization, simplification and similar tasks have to be kept apart and cannot be treated uniformly as positive examples of natural style. The data card is marked Apache-2.0, yet source and task are still recorded; do not confuse the data license with the model-weights license. |

What is specifically worth reusing from AdParaphrase is its two-stage annotation: 5 people first judge whether the pair is a paraphrase, filtering by majority vote, and then attractiveness preferences are collected from 10 people. Its `main` raw file retains non-equivalent candidates, so the whole table cannot be treated as passing pairs. `pt`, by contrast, collects preferences directly over two rewrites of the same source draft; a DPO win/loss cannot be assembled from two unrelated comparisons. [Field and filtering notes in the author repository](https://github.com/CyberAgentAILab/AdParaphrase-v2.0)

There is also [CAMERA, ACL 2024](https://aclanthology.org/2024.acl-long.54/), which supplies Japanese landing-page/query → advertising data, but the same product can correspond to different appeals; generation references of this kind cannot be treated as content-equivalent style pairs without review. No off-the-shelf complete gold has been found that directly covers Chinese/English × marketing/technical documentation while also carrying fidelity and naturalness labels; that is the conclusion of this search round, not an assertion that "no relevant data exists".

## 3. Obtaining the main gold: real model draft → editor rewrite → independent blind evaluation

This route is closest to actual product input and is proposed as the main source.

1. **Establish the content basis.** Technical documentation uses versioned documents with clear usage rights, interface contracts, or original feature descriptions; marketing uses a licensed/original product brief listing price, features, target audience, channel, brand tone, and promises that can be supported. Chinese and English are each collected natively; do not fill half the sample with translations.
2. **Obtain source drafts with a realistic distribution.** Collect from real writing tasks that are explicitly consented to for research use, or generate several model drafts from the same source pack. Cover both the default prompt and a strong writing prompt; record the full model and prompt version. Do not specifically ask a model to "write in a particularly AI-like way", or the negative examples become too easy.
3. **Rewritten by a suitable editor.** Editors may delete redundancy, reorder information, change sentence patterns, and adjust pacing; they may not invent cases, numbers, or promises. Keep the reason for each change; returning the text unchanged is also allowed. Technical editors are responsible for technical semantics; marketing editors need to know the target market. An edited draft is a candidate first, not automatically the answer.
4. **Independent evaluation.** Evaluation hides the human/model origin and randomizes the A/B order; constraints are checked first, then naturalness and adoption preference are judged. Editors do not evaluate their own drafts. In the pilot, each pair is first scored independently by two people, disagreements go to a third person, and the raw votes are kept permanently.
5. **Form data for different uses.** A rewrite with a credible improvement that passes the constraints can serve as an SFT target; a clear preference can feed DPO; ties are kept as evaluation material and as training material for the no-revision-needed case. Faulty samples stay in the failure set and are not deleted from the benchmark denominator merely because they hurt the numbers.

This step needs real human editors and independent judgment. I can prepare the source pack, candidate generation, and the comparison and annotation interface, and I can propose edit candidates; a result written by me and then evaluated by me counts only as an automatic candidate and cannot pass itself off as independent human gold.

## 4. Three supplementary routes and their biases

| Route | How to obtain it | Why it does not count directly as gold |
|---|---|---|
| Good human source draft → model rewrite | Use historical or newly written text you have the right to use, and let several models process it under real editing instructions to form same-content candidates. | The model may improve the source draft. The human draft must not be assumed to win; synthetic degradation that forces "adding AI-ese" is used only as a small share of diagnostic data, to avoid learning nothing more than to invert one model's fingerprint. |
| Natural revision history | Obtain from public, suitably licensed version records, or from before/after pairs supplied by the author; prefer revisions that change expression only. | A new version may add features, change prices, or correct facts, which does not suit a pure-style comparison. A human's later draft may also be worse, so it still has to be re-checked. |
| Multi-model / multi-prompt candidates from the same source draft | Keep the source draft and the constraints fixed, let different candidate methods rewrite it, then compare anonymously. | This is an efficient source of DPO candidates, and the winner need not come from a human. Model-judge labels that have not been independently re-checked count as silver; the final test cannot be self-certified by the same optimization objective. |

Pre-ChatGPT source texts can help establish source history, but "written early" provides no quality guarantee; old text may also have been seen in base-model pretraining. Newly written, unpublished original test material can fill this gap. Do not collect only classic good articles and mediocre model drafts, or period, subject matter, information density, and author skill all get mixed into the label.

## 5. What to do first: an 80-task collection pilot

The following is the proposed allocation. 20 independent source tasks per cell; the total is still the agreed 80, not a second benchmark started from scratch.

| Collection route | Chinese technical | English technical | Chinese marketing | English marketing | Total |
|---|---:|---:|---:|---:|---:|
| Real model source draft + human edit candidate | 10 | 10 | 10 | 10 | 40 |
| Human source draft + natural revision / model rewrite candidate | 6 | 6 | 6 | 6 | 24 |
| Diagnostic tasks: good drafts needing no revision, reasonable comparisons, factual traps | 4 | 4 | 4 | 4 | 16 |
| Total | 20 | 20 | 20 | 20 | 80 |

Each task may have several candidates, but the initial human evaluation covers one pair, giving 160 independent pair reviews plus disagreement adjudication; this figure excludes content preparation and 40 items of editing labor. 80 tasks do not guarantee 80 training pairs with a clear winner. Keep every label; the actual pass rate, disagreement rate, and per-item time determine the cost of scaling up.

Public paper data serves first as a separate auxiliary review pool, spot-checking content equivalence and task fit; its few thousand reference answers cannot replace the four-cell target tasks. The roles of the training set, the judge calibration set, and the test set must be recorded explicitly; a pilot used to revise the rubric or the few-shot examples no longer serves as the final test.

The pilot has to answer: can evaluators point to consistent problems? Can editors reliably improve a strong baseline? Are the improvements merely shortening or fact correction? Do the four cells show different preferences? Only if these results support continuing do we expand the human gold and use a calibrated filtering pipeline to produce a larger silver training set. Whether it is a few thousand or tens of thousands is decided by the learning curve; papers cannot supply a fixed answer in place of this task.

## 6. How to confirm that the content is the same and the labels are credible

- **Check the propositions first.** List the facts and intents that must be preserved, and check for added unsupported statements, omitted conditions, and changes to numbers, negation, degree, and certainty. Code, commands, url values, and identifiers are checked separately. An automatic diff or a model can assist, but embedding similarity alone cannot be the basis for passing.
- **Record the use constraints.** Preserve length, channel, audience, and brand requirements. Shorter does not win automatically; more attractive does not make up for a wrong promise. Where no additional facts were requested, do not let a rewrite gain an advantage from added content.
- **Preserve subjective differences.** Naturalness and overall adoption are voted on separately; require the problem excerpt and the reason, and allow tie/abstain. Look at pre-adjudication agreement first; a majority preference is evidence for a given population and context, not the one objective answer.
- **Split by collection.** The same document, brand campaign, historical versions, translations, and model-derived drafts all belong to one source family, and candidates are derived only after the split. Five rewrites of the same source draft cannot count as five independent test samples.
- **Label provenance and usage rights.** Keep the file version, date, editor/model origin, and license; for now this project saves notes and links. Licenses for data import, training, and redistribution are verified separately.
- **Keep the data that failed.** Rejected rewrites, ties, and hard-to-judge cases all have a use; the main test keeps the full-task denominator and the failure rules. Do not report only the flattering win rate of the "fidelity-passing subset".

## 7. How one body of annotation serves judge, SFT, and DPO

| Use | Data shape | Key conditions |
|---|---|---|
| Judge calibration and evaluation | `context, draft, A, B, constraints, original per-dimension scores and preferences` | Same-input comparison; the judge is checked against human evaluation, rather than the judge defining all the gold. The final test is quarantined. |
| SFT | `context + draft → accepted_rewrite` | The target draft passes the constraints and suits the task; there can be several reasonable targets, and there should also be samples that need no revision. There is no need to manufacture an obviously bad draft for every item first. |
| DPO | `context + draft, chosen_rewrite, rejected_rewrite` | Both drafts address the same input, the preference is labelled directly, and chosen must pass the factual and task constraints. tie, both-drafts-unqualified, and unresolved uncertain do not convert directly into a win or a loss. rejected may fail, but the failure type has to be stored; analyse separately the style-preference subset in which both drafts pass the constraints. |

A set of "AI source draft A / edited draft B" can be used directly to build the SFT pair A→B. If it is used for DPO, A can be kept as-is as a legitimate candidate and compared directly with B; the more common approach is to generate B and C from A and then label the B/C preference directly. Good and bad outputs belonging to different source drafts must not be pasted together arbitrarily.

The final delivery should contain: tasks and candidates with provenance, pre-adjudication human evaluations and disagreements, the applicable training/evaluation split, the scope of use, and the evidence behind each label. Model-generated candidates, automatically filtered silver, and human-re-checked gold are counted separately; what this round delivers is this collection plan and the source verification — this real data has not been produced yet.

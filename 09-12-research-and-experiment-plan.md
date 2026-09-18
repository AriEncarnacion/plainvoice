# Plainvoice: A Research and Experiment Plan for Reducing AI-ese in Rewritten Content

The product objective worth validating is this: given the source draft, the audience, the intended use, and the factual material, make the rewritten draft fit the specific context better, be more useful, and preserve more of the author's voice, without changing the key meaning. Post-training is a candidate implementation path; whether it is worth adopting has to be judged against seriously optimized prompts and editing workflows.

This plan covers four equally prioritized scenarios: Chinese/English × technical docs/marketing. It is a research and experiment design; there are as yet no human evaluation results, training results, or measured costs for this project. Literature and model information were verified as of 2026-09-12. Sample sizes, thresholds, and hyperparameters are all proposals and need to be revised by the pilot.

## 1. Assessment of the initial plan

Establishing evaluation criteria first is the right direction, but there is no need to train a judge first. The first step should be to establish a small number of interpretable human evaluation anchors that come with counterexamples, and to test whether people can reach sufficient agreement on what the problems are and what counts as an improvement. Then score with existing models against the rubric, measure their error across the four scenarios, and only then decide whether it is worth distilling into a dedicated evaluator.

Excellent historical writing is valuable, but "before ChatGPT" can only serve as one part of the source evidence. Old marketing drafts may be full of boilerplate, and old technical docs may be vague; modern AI drafts may be clear and accurate. Setting up a binary classification between historical human drafts and modern default model drafts easily ends up training an era/genre/channel detector instead. Source labels, naturalness, and writing quality should be stored separately.

"Humanizing rewriting" and "filling in missing content" need to be kept apart. If the source draft does not have enough facts, pure rewriting can cut empty phrasing and improve the ordering, but it cannot reliably create insights, case studies, or product evidence. The system should accept an evidence packet; if supplementary material is to be retrieved, that should be an independent experimental variable, so that every method gets the same material.

The most valuable training material is usually "source draft + specific editing requirements + evidence → a rewritten draft the editor approved," rather than excellent articles detached from any input. The latter may teach a prose style, but it does not teach preserving facts, respecting constraints, or knowing when not to edit. CoEdIT and IteraTeR provide directly relevant task precedents, but neither can directly prove that this project will succeed.[^1][^2]

## 2. How "AI-ese" becomes a measurable construct

The recommendation is to record three outcomes at the same time, rather than collapsing them into a single "AI probability":

1. **Source information**: human, model, mixed, unknown, plus how credible the evidence is. Used only for stratified analysis, never given to the quality judge.
2. **Reader perception**: how templated, vacuous, or contextually ill-fitting the text seems in a given language, audience, and scenario. This is a subjective evaluation, not authorship identification.
3. **Editing quality**: whether readers can understand, decide, or complete a task faster; whether information, meaning, and brand/author voice are preserved.

The table below gives working definitions for the pilot to test; it cannot claim that a unified academic standard already exists. For how these correspond to linguistics and industry research, and where that correspondence has limits, see [Style literature](research/09-12-style-literature.md).

| Dimension | Observable problem | Judgment in technical docs | Judgment in marketing |
|---|---|---|---|
| Useful information | Several sentences in a row add no new fact, condition, step, or basis for judgment | Whether premises, failure conditions, or runnable steps are missing; necessary explanation does not count as padding | Whether the target, use, difference, evidence, and action are made clear; a tagline need not be stuffed with specifications |
| Discourse function | Unsupported grand openings, fake contrasts, generic summaries | A contrast must help distinguish behaviors, conditions, or concepts | A contrast must serve real positioning, and cannot inflate the product out of nothing |
| Syntax and rhythm | The same skeleton repeated over and over; connectives standing in for logic | Keep terminology stable and steps clear; avoid swapping words merely for variety | Short sentences, white space, and parallel structure are allowed, but must fit the brand and the channel |
| Context and voice | Applicable to any industry, with the audience and the author gone | Repeating common knowledge to experts, or omitting necessary background for novices | If the whole text still applies after the brand name is swapped, it may be over-generic |
| Cognition and pragmatics | Unevidenced confidence, empty praise, excessive hedging | Be explicit about must/may, limits, conditions, and unknowns | Avoid unsupported guarantees, exaggerated figures, and invented user experiences |
| Cross-text diversity | Each piece passes on its own, but read in bulk they always have the same structure | Staying consistent across similar operations is a virtue; do not chase variation mechanically | Different briefs should produce different angles; the same brand voice still has to stay continuous |

`不是 X，而是 Y` (*"not X, but rather Y"*) is sometimes a necessary clarification — for example, `令牌过期返回 401，不会自动重试` (*"an expired token returns 401 and is not retried automatically"*). What should be penalized is a contrast that draws no real distinction and adds no new proposition, not the sentence pattern itself. Likewise, headings, em dashes, parallelism, and formal wording are not error labels in themselves.

It is also necessary to distinguish **linguistic syntactic density** from **the amount of effective information the reader receives**. Noun stacking can make the syntax denser while making the content harder to understand and conveying no more information. Lexical rarity, perplexity, and sentence-length variation can serve only as diagnostic features; they should not be optimized directly.[^3]

## 3. Constructing ground truth

Build four layers of material: source anchors, quality anchors, controlled comparisons, and counterfactual minimal pairs. For detailed candidate data and usage restrictions, see [Data literature](research/09-12-data-and-task-literature.md).

**Source anchors** should prefer content with a fixed historical version and an author/editor record. Keep date evidence and usage rights; for historical marketing texts without permission, build only a list of links. Pre-ChatGPT text may also have gone into base-model pretraining, so it cannot carry the whole test set.

**Quality anchors** are rated by editors in the corresponding language and domain. A text can be "very AI-like but good," and it can also be "obviously human but bad." All four source/quality combinations should appear, and there should also be examples of an excellent source draft that needs no change, to keep the model from over-editing in order to show that it did work.

**Controlled comparisons** start from the same brief: with identical facts, audience, channel, and length requirements, you obtain a human draft, several default model drafts, a strongly prompted draft, and a human-revised draft. Do not generate a model draft from a one-sentence prompt and then compare it with a professional writer who has the full background. Reconstructing the brief for a historical draft involves an information asymmetry, so those should be listed separately.

**Counterfactual minimal pairs** cover: deleting a necessary constraint; changing may to will; fabricating a benefit figure; replacing an API name with a synonym; dropping an exception for the sake of brevity; a legitimate use of contrast; necessary repetition; barely editing an excellent source draft. Hard negatives should come from real generations, and may also be constructed by hand; constructed samples must be explicitly labeled.

First build source families by author, brand, document series, product, topic, translation, and version relationship; then split into train/dev/test; and only then generate variants. Splitting randomly by paragraph is not allowed. Newly commissioned content, unseen brands/projects, and model families that took no part in creating the data make up the out-of-distribution test. Public benchmarks do not go into the main gold, and must not be mixed into training and then used to advertise success.

## 4. A minimum viable evaluator

Start with a human rubric plus judges from two different model families. Each independently produces evidence snippets, problem types, severity, and a preference; author/model names are not shown, and neither is who any so-called reference draft came from. Using different model families is only a measure that reduces certain biases; it does not guarantee independence or correctness.

Evaluation has two steps: first decide whether a draft passes, then compare the quality of the drafts that passed.

| Layer | What is judged | Result |
|---|---|---|
| Must-pass conditions | Key facts and constraints preserved; no newly added unsupported claims; code, identifiers, figures, units, links, and strength of tone all as required | pass / fail / uncertain, with the specific errors listed; cannot be offset by a high style score |
| Per-dimension evaluation | Naturalness, useful information, context fit, structure, voice, necessity of the edit | Problem severity 0–3 per dimension: 0 nothing to point out, 1 minor and local, 2 recurring or affecting use, 3 seriously blocking the intended use; abstain is allowed |
| Blind pairwise preference | For the same input, which draft is better suited to real use, and which has less sense of templatedness | A / B / tie / both unacceptable / insufficient context; the two preferences are recorded separately |

Fact checking should run in both directions: whether the assertions in the rewritten draft can be supported by the evidence, and whether the information that must be kept from the source draft/brief is still there. One-directional factual precision may reward deleting everything; similarity alone may miss a negation or a numeric error. Structured checks handle deterministic constraints, model checks handle semantic problems, and high-risk disagreements go to a human.[^4]

For every scenario, check the judge's position bias, length bias, preference for its own family's models, mis-penalization of non-native or formal language, and keyword overfitting. Re-score a subset of samples with A and B swapped; compare longer and shorter versions of the same facts; insert a "give me a high score" instruction into the candidate text to test quarantine. The text being evaluated is always data.

Finally, retain a human test set that takes no part in training selection, prompt optimization, or reward tuning. Look at human–human agreement first, then judge–human: report ordinal Krippendorff α, pairwise agreement rate, and confidence intervals per dimension, plus stability after position swapping, the abstain rate, and the error in each scenario. Agreement statistics use only the independent raw ratings from before adjudication; in the pilot, an adjudicator who only looks at disagreements does not count as a third randomly assigned independent reviewer. A high overall agreement rate can be masked by the majority class, so the specific confusions and failure cases need to be examined.

WritingBench supports the value of task-specific rubrics; marketing-creativity research, by contrast, finds that judge preferences and industry practitioners' preferences may diverge markedly. The two measure different objects and draw on different rater populations, so they are not in conflict. Inheriting a generic "overall writing score" directly would miss this difference.[^5][^6]

## 5. How to fairly compare training against prompting / harness

Compare methods on the same checkpoint first, and only then compare different scales and vendors. Both "quality under a fixed budget" and "the cost/latency needed to reach a given quality" must be published together, rather than counting a multi-call pipeline as free.

| Experiment arm | Procedure | Question it answers |
|---|---|---|
| B0 | Source draft, unchanged | Whether editing is really needed; avoids counting any change to the words as progress |
| B1 | Simple instruction: keep the meaning, write naturally and clearly | The common way users actually use it; a lower bound only |
| B2 | Per-language/per-domain rubric + 3–5 sets of positive and negative examples from train/dev | What carefully designed single-pass prompting can achieve |
| B3 | List the facts and problems → rewrite → independent fact check, with at most one repair pass | Whether an editing harness with evidence and checks is already enough |
| B4 | Generate 4 candidates from the same material, with an independent ranker choosing | Whether added search at inference time can substitute for training; the full generation and selection cost is counted |
| T1 | SFT adapter, using the same editing requirements as B2 once training is done | The incremental value of high-quality rewrite supervision |
| T2 | DPO on top of T1, using human-verified preference pairs | Whether preference supervision still pays off on top of SFT |
| T3 | The best trained model + the same checking pipeline as B3 | Whether training and harness are complementary |
| H | Professional human rewriting | A human reference and a baseline for editing time saved; not offered as a cheap automated solution |

The same input, evidence packet, target language, output requirements, example sources, and model version are all frozen. Prompt tuning uses dev only; each method gets a comparable amount of tuning opportunity, and the number of attempts and the selection criteria are recorded. For output length, report both the natural result and a stratification by the length band the requirements specify; long drafts must not be deleted after the fact in the name of "fairness," nor may content be altered by trimming.

Sampling temperature values are not necessarily comparable across models; save every supported decoding parameter and use dev to pick suitable settings. For reasoning models, record the thinking budget, the billing for hidden reasoning, and the final output length. For key arms, at least assess generation randomness; re-check any leading result from a training arm with multiple random seeds, without running the full factorial of combinations up front.

The final main comparison locks in, in advance, one winning trained system and one strongest untrained system, and compares them on a test split that has not been touched. B0 and the hard subset continue to serve as regression checks. Ablations cover at least: no examples, no independent verifier, no preference stage, no genre conditioning, using only default weak AI negatives, and the share of synthetic bad drafts.

## 6. Training path and model scale

The recommended order is **strong baseline → SFT on edit pairs → DPO on preferences → online RL if necessary**. LoRA is a parameter-efficient adaptation method, QLoRA is a training method that pairs a quantized base with an adapter, and SFT/DPO are different supervision objectives; these are not mutually exclusive options at the same level. For a detailed treatment of training, the original papers, and the official model cards, see [Training literature](research/09-12-training-literature.md).

SFT first learns concrete ways of editing and when to leave the original text alone. A DPO chosen/rejected pair must come from the same task and the same factual material, and the chosen side must itself have been fact-checked; do not build preference labels solely from "shorter" or "lower vocabulary-detector score." For the high-frequency style errors that show up often in training, the supervision signal should include the editing rationale or the location of the problem, though the final rewrite output need not carry an explanation.

The first round of candidates centers on a **roughly 8–9B Chinese–English bilingual base**, with a **roughly 4B** one as a low-cost control; then one of **12–14B** or **27–32B** is chosen to test whether capacity limits fidelity on long texts. Verifiable concrete candidates include Qwen3.5-4B, Qwen3.5-9B, Qwen3-14B, and Qwen3.8-27B; these are candidates still to be evaluated, not a ranking that has already been produced. Cross-family candidates and their architecture/licensing are verified one by one from the model cards.

The four scenarios first use the same model with explicit language/genre conditioning, and negative transfer is observed; if Chinese marketing improves while English technical docs suffer, then compare per-domain adapters. A larger model may improve instruction following and fidelity, but it does not guarantee better naturalness — model family, training data, and preference objective may all matter more. For multimodal/hybrid-architecture models, the text-only path, the trainable adapter modules, the attention implementation, and quantization support all need to be verified first.

Do not start from online RL for now: at this point the reward very likely does not yet have stable enough human grounding, and online optimization would amplify the evaluator's shortcuts. Only once credible, stable errors that SFT/DPO cannot readily fix have appeared, and the reward is reliable against external human evaluation, is that extra cost worth incurring.

Do not open by doing continued pretraining directly from excellent human articles. It can serve as a later style-adaptation ablation, but keep it distinct from editing-instruction supervision. Also do not pick 70B at the outset: first establish whether a small model fails on capacity or on data/evaluation; otherwise scaling the model only repeats the same mistake more expensively.

## 7. Phased sample sizes and stopping conditions

| Phase | Balanced allocation across the four scenarios | Deliverable and condition for moving to the next step |
|---|---|---|
| Rubric pilot | 80 independent tasks, 20 per cell; 2 initial raters + 1 adjudicator for disagreements | See whether people can point to consistent problems and improvements; revise the dimensions, keep the disagreement records, and do not treat the pilot as the final test |
| Baseline development | 240 new tasks, 60 per cell | Tune B1–B4, review failures and loss of author voice; if the harness already meets the requirements and cost is not a problem, it is fine to stop here |
| First-round SFT | Suggested 2,000 independent, verified rewrite pairs, about 500 per cell | Look at the learning curve and held-out dev first; then expand to 5K–10K for the scenarios that still show gains — quantity is no guarantee of quality |
| Preference stage | Start with a small number of genuinely ambiguous preferences; expand to 1K–3K pairs if necessary | Enter only if a stable style bias remains after SFT; preference examples must satisfy the factual constraints, and ties must be kept |
| Locked final test | 800 new tasks, 200 per cell; 3 independent reviewers per pair in the main comparison | Training beats the strongest baseline and satisfies fidelity, per-scenario regression, and real cost constraints |

These quantities are adjustable budget proposals. The 800-item main pairwise comparison, at 3 reviewers and 3–5 minutes of reading and rating each, takes roughly **120–200 hours**, not counting recruitment, rubric training, long-document review, re-rating, and adjudication. Several thousand high-quality preference labels cannot be treated as a free byproduct. Prioritizing all four scenarios equally means every cell needs the corresponding domain expertise.

The primary metric is the quality preference score for each task after the three reviewers are aggregated; the failure rate for each side, uncertain, and the naturalness preference are listed separately alongside it. Taking the trained system as A, the scoring rules are as follows. The conditional win rate over pairs where both sides passed serves as a secondary metric, so that filtering down to passing samples alone does not create survivorship bias.

| Case | Predefined handling and A's relative score |
|---|---|
| A passes, B confirmed failed | 1; B's absolute failure is recorded separately |
| A confirmed failed, B passes | 0; A's absolute failure is recorded separately |
| Both sides confirmed failed | 0.5, a relative tie, with an absolute failure of 1 recorded for each side; it cannot be claimed that either side's quality passed |
| Both sides pass | For each reviewer, map A/B/tie to 1/0/0.5 and take the mean; with one vote each for A, B, and tie the score is 0.5, and the no-consensus flag is kept |
| A reviewer returns both_unacceptable | First check whether the task went unrecorded or a hard constraint failed; if it is only that neither is good enough, score the pairwise vote 0.5 and separately record that neither is usable |
| Any reviewer flags a major factual error | An independent fact adjudicator handles it on the evidence, not by a majority of the style votes; it cannot be judged as passing before adjudication |
| A system produces empty output, times out, or still fails after the agreed retries | Count it as a task failure for that system and score it by the one-sided/both-sided failure rules above; the cost is still counted |
| Insufficient material, still uncertain after fact adjudication, or a missing reviewer | First add a rating or verify; if it still cannot be judged, keep the task and use 0 and 1 to give the lower and upper bound of its effect on the overall result — no silent removal, and no neutral 0.5 to paper over the unknown |

Every planned task stays in the overall denominator; when tasks remain undecided, report the partial-identification interval and the coverage rate, and it passes only if the conservative bound still meets the threshold. If a task packet is itself found to be invalid, replace it under a pre-registered rule that is blind to the model results and keep an audit record; tasks are not dropped according to who won or lost.

Macro-average the four cells with equal weight, and report each cell separately. Compute intervals with a cluster bootstrap over independent tasks / source families; multiple reviewers of the same draft, repeated sampling, and A/B reordering do not count as additional independent samples. Analysts need to look at rubric agreement and population differences, and must not adjudicate every aesthetic disagreement into a single "ground truth."

An example threshold can be pre-registered: an overall quality preference score reaching 0.55 with the lower bound of the 95% interval above 0.50; every cell meeting a predefined non-inferiority condition; and a serious factual error rate that meets the specific product requirement. **0.55 is the minimum gain proposed on the product side, not a threshold recognized in the literature.** After the pilot and before the final test, each cell must also have its allowed regression margin, its ceiling on serious errors, and the confidence rule for multiple comparisons locked in; failing to detect a significant decrease is not the same as non-inferiority, and insufficient evidence is marked inconclusive. For a binomial result near 0.5 with n=200 per cell, the ordinary approximate 95% interval has a half-width of about 7 percentage points, and about 3.5 percentage points for the overall n=800; ties, clustering, and multiple comparisons change that precision. This scale therefore cannot be used to claim a significant 5-percentage-point improvement in every cell.

Fidelity needs uncertainty too: with 200 independent tasks in a cell and zero serious errors, the commonly used rule-of-three approximate upper bound is still about 1.5%, which does not prove the true error rate is below 1%. To commit to a lower error rate, enlarge the inspection sample and define the errors and confidence requirements in advance. Sample sizes are ultimately recomputed from the variance, tie rate, cluster correlation, and required effect observed in the pilot.

## 8. What the two product types still need to be tested on

For technical docs the endpoint is whether readers can carry out the operation correctly, find the information they need, and whether they misread the conditions. Preserve code and identifiers, and where necessary run user tasks or reading-comprehension tests. Livelier sentences cannot offset an error in the instructions.

For marketing the endpoint depends on the channel: editorial adoption rate, brand fit, reader comprehension, and, where conditions allow, a real conversion experiment. CTR, conversion, and naturalness may point in different directions and cannot stand in for one another. A real campaign needs its own budget and experiment design; this round does not trigger any campaign. Existing research on marketing systems indicates that input material, retrieval, and workflow are all worth including in the comparison.[^7]

Also measure time-to-publishable version: have blinded editors revise the output until it is usable, and record editing minutes, the number of factual fixes, and the final adoption rate. This identifies approaches where "the judge score is high but human rework is still heavy." A first measurement is research; assumptions about editor cost should not be written up as actual business ROI.

The cost account covers annotation, training, hyperparameter tuning, inference, candidate selection, verification, and rework together. The break-even call volume can be written as `additional one-time cost / (baseline total cost per draft − trained total cost per draft)`; when the denominator is not greater than zero, there is no cost recovery based on call volume. GPU and API prices are verified when the experiments are actually run; the research phase does not draw on a compute budget in advance.

## 9. The hypotheses most worth testing right now

- The four scenarios may share some problems, but there is no single banned-word list that holds across languages/domains.
- Given sufficient material, an 8–9B editing model may reach the quality of a strong harness at lower inference cost; that is more worth testing than presuming it must beat every frontier model.
- Factual fidelity and useful-information constraints, together with professional editors' preferences, may provide a better optimization signal than AI detection scores.
- If prompting already solves most style problems, the value of training may lie mainly in stability, latency, private deployment, or cost, rather than in higher average literary polish.
- When author voices are themselves diverse, a single preference model may write everyone into the same "natural register"; configurable voice and positive examples that need no editing are required.

The smallest executable next step is to build a rubric pilot of 20 items in each of the four cells and collect real disagreements from professional editors. There is no need yet to procure GPUs, crawl a large corpus, or train a standalone discriminator.

## References

[^1]: Raheja, Kumar, Koo & Kang. [CoEdIT: Text Editing by Task-Specific Instruction Tuning](https://aclanthology.org/2023.findings-emnlp.350/). Findings of EMNLP, 2023.
[^2]: Du et al. [Understanding Iterative Revision from Human-Written Text](https://aclanthology.org/2022.acl-long.250/). ACL, 2022.
[^3]: For the original papers of style research, their scope of observation, and their conflicting results, see [Style literature](research/09-12-style-literature.md); "amount of effective information" here is a functional definition this project proposes to adopt.
[^4]: For the original sources on factual evaluation, detector limitations, and judge bias, see [Evaluation literature](research/09-12-evaluation-literature.md); the two-directional fidelity protocol is this project's own design and cannot be taken as already covered by an off-the-shelf metric.
[^5]: Wu et al. [WritingBench: A Comprehensive Benchmark for Generative Writing](https://arxiv.org/html/2503.05244v4). 2025, v4.
[^6]: Bhat, Browne & Bingemann. [Creativity Benchmark: A benchmark for marketing creativity for LLM models](https://arxiv.org/html/2509.09702v1). 2025, preprint.
[^7]: Liu, Tahmasbi, Haque & Jain. [LLMs for Customized Marketing Content Generation and Evaluation at Scale](https://arxiv.org/html/2506.17863v1). 2025, preprint.

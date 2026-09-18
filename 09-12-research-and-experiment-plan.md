# Plainvoice: A Research and Experimental Plan for Reducing the AI-like Appearance in Rewritten Content

A viable product objective is to, given the original text, audience, intended use, and factual material, make the revised text more relevant to the specific context, more useful, and more faithful to the author's voice, while preserving the key meaning. Post-training is a candidate implementation path; its suitability depends on comparison with carefully optimized prompts and editing workflows.

This proposal covers four scenarios with equal priority: Chinese/English × technical documents/marketing. It is a research and experimental design; human evaluation results, training results, or cost measurements for this project are not yet available. Literature and model information verification is as of September 12, 2026. Sample size, threshold, and hyperparameters are suggestions and require revision during pilot testing.

## 1. Judgment of the initial plan

Establishing evaluation criteria first is the right direction, but it's unnecessary to train a judge first. The first step should be to establish a small number of interpretable human evaluation anchors with counterexamples to test whether people can reach sufficient consensus on the problem and its improvement. Then, use the existing model to score according to rubrics, measure its error in four scenarios, and then decide whether it's worthwhile to distill it into a dedicated evaluator.

Excellent historical writing is valuable, but "before ChatGPT" can only serve as part of the source evidence. Old marketing articles may be full of clichés, and old technical documents may be vague; modern AI-generated articles may be clear and accurate. Binary classification of historical human-written articles and modern default model articles makes it easier to train a date/topic/channel identifier. Source tags, naturalness, and writing quality should be saved separately.

It's necessary to separate "personification rewriting" from "content supplementation." If the original text lacks sufficient facts, pure rewriting can remove empty rhetoric and improve the order, but it cannot reliably create insights, case studies, or product evidence. The system should accept evidence packets; if supplementary information needs to be retrieved, it should be treated as an independent experimental variable, ensuring all methods obtain the same data.

The most valuable training material is usually "original manuscript + specific editorial requirements + evidence → edited version approved by the editor," rather than excellent articles detached from the input. The latter may teach a writing style, but not how to preserve facts, adhere to constraints, or know when not to revise. CoEdIT and IteraTeR provide directly relevant task precedents, but neither can directly prove the success of this project. [^1][^2]

## 2. How can the "AI flavor" become a measurable construct?

It is recommended to record the three results simultaneously, rather than combining them into a single "AI probability":

1. **Source Information:** Human input, model-based, mixed, unknown, and the credibility of the evidence. Used only for stratified analysis, not provided to the quality judge.
2. **Reader perception:** To what extent does the text appear templated, vague, or out of context in a given language, audience, and setting? It is a subjective evaluation, not an author's assessment.
3. **Editorial quality:** Can readers understand, make decisions, or complete tasks more quickly? Are the information, meaning, and brand/author's voice preserved?

The table below provides the working definitions for pilot testing; it cannot be claimed that a unified academic standard already exists. For the correspondence and limitations with linguistics and industry research, see [link to table].[Style Documents](research/09-12-style-literature.md).

| Dimensions | Observable Issues | Judgments in Technical Documentation | Judgments in Marketing |
|---|---|---|---|
| Useful Information | Multiple sentences do not add new facts, conditions, steps, or judgment criteria | Are there any missing premises, failure conditions, or feasible steps? Necessary explanations are not superfluous | Have the object, purpose, differences, evidence, and actions been clearly stated? Slogans do not need to be crammed with parameters |
| Discourse Function | Unfounded grand introductions, false comparisons, and vague summaries | Comparisons must help distinguish between behaviors, conditions, or concepts | Comparisons must serve the true positioning and cannot arbitrarily elevate the product |
| Syntax and Rhythm | Continuously repeat the same framework; use conjunctions instead of logic. | Retain stable terminology and clear steps; avoid changing words for the sake of variation. | Short sentences, white space, and parallel structures are allowed, but must conform to brand and channel requirements.
| Context and Voice | Applicable to all industries, audience and author disappear | Repeats common sense to experts, or omits necessary background for novices | The entire text remains applicable after a brand name change, indicating potential over-generalization |
| Cognition and Pragmatics | Unsupported Confidence, Empty Praise, Excessive Reservation | Clearly Define Must/May, Limitations, Conditions, and Unknowns | Avoid Unsupported Assurances, Exaggerated Figures, and Fictitious User Experiences |
| Cross-text diversity | Individually, each article is acceptable, but when viewed in batches, the structure remains the same | Maintaining consistency in similar operations is an advantage; avoid mechanically pursuing variation | Different briefs should produce different perspectives; the same brand message should remain consistent |

"Not X, but Y" is sometimes a necessary clarification, such as "Token expired returns 401, will not automatically retry." The punishment should be for comparisons that lack genuine distinction or new propositions, not for the sentence structure itself. Similarly, headings, dashes, parallelism, and formal wording are not necessarily error labels.

It is also necessary to distinguish between **linguistic syntactic density** and **the amount of effective information obtained by the reader**. Noun stacking can make the syntax denser, but it also makes the content more difficult to understand and does not provide more information. Lexical rarity, confusion level, and sentence length variation can only be used as diagnostic features and are not suitable for direct optimization. [^3]

## 3. Construction of Ground Truth

A four-layer material structure was established, consisting of source anchors, quality anchors, controlled controls, and counterfactual minimum pairs. Detailed candidate data and usage limitations can be found in [link to relevant documentation].[Data Literature](research/09-12-data-and-task-literature.md).

**Source Anchors** prioritize content with fixed historical versions and author/editor records. Date evidence and usage rights are retained; unauthorized historical marketing texts are only listed as links. Previous ChatGPT texts may also be included in the pedestal pre-training, therefore they cannot be used for the entire test set.

**Quality anchors** are evaluated by editors in the relevant language and domain. A text can be "very AI-like but of good quality" or "obviously human-made but of poor quality." All four source/quality combinations should be present, along with examples of excellent original texts that require no modification, to prevent the model from being over-edited to demonstrate workload.

**Controlled Comparison** Starting from the same brief: identical facts, audience, channels, and length requirements, each draft yields a human-written draft, multiple default drafts, a strongly prompted draft, and a human-revised draft. Do not generate a draft using a single-sentence prompt and then compare it with a professional author who possesses complete background information. Reconstructing historical briefs presents information asymmetry and should be presented separately.

**Counterfactual minimum pair** coverage: Remove necessary restrictions; replace "may" with "will"; fabricate revenue figures; replace API names with synonyms; remove exceptions for brevity; use contrast appropriately; use necessary repetition; and make minimal changes to the excellent original. Difficult negative examples should be generated from real data, but can also be artificially constructed; constructed samples must be explicitly labeled.

First, establish source families based on author, brand, document series, product, theme, translation, and version relationships. Then, divide them into train/dev/test categories, and finally generate variants. Random segmentation by paragraph is not allowed. Newly commissioned content, model families without visible brands/projects, and models not involved in data generation constitute the external distribution test. Publicly available benchmarks should not be included in the main gold standard, nor should they be mixed into training data for successful promotion.

## 4. The minimum feasible solution for the Evaluator

The evaluation begins with a human rubric plus two judges from different model families. Each family independently provides evidence fragments, problem types, severity levels, and biases; they do not display author/model names or the sources of any so-called references. The different model families are merely measures to reduce certain biases and do not guarantee independence or correctness.

The evaluation process involves two steps: first, determining whether the manuscript is acceptable, and then comparing the quality of the acceptable manuscripts.

| Layer | Decision Content | Result |
|---|---|---|
| Required Conditions | Key facts and limitations must be retained; no new additions or supporting claims; code, identifiers, numbers, units, links, and tone strength must meet requirements | pass/fail/uncertain, with specific errors listed; cannot be offset by a high style score |
| Dimensional Evaluation | Naturalness, Useful Information, Contextual Fit, Structure, Sound, Editing Necessity | Each dimension has a severity rating of 0–3: 0 No identifiable problem, 1 Minor local issue, 2 Repetitive or affecting use, 3 Severely hindering use; Abstaining is permissible |
| Blind Pairing Preferences | Which draft is more suitable for practical use and less template-like under the same input? | A / B / tie / both unacceptable / insufficient context; record the two preferences separately |

Fact checking should be conducted in two directions: whether the assertions in the revised draft are supported by evidence; whether the information that must be retained in the original draft/brief is still there. One-way fact accuracy may reward the deletion of everything; simple similarity may miss negations or numerical errors. Structured checks are used for deterministic constraints, model checks are used for semantic issues, and high-risk disagreements are handled manually. [^4]

Each scenario requires checking the judge's positional bias, length bias, preference for its own model, mis-penalties for non-native/formal languages, and keyword overfitting. Partial sample swapping and A/B re-evaluation are performed; different versions of the same fact of varying lengths are compared; and "give me a high score" instructions are added to candidate texts to test isolation. The evaluated text is always data.

Finally, a human-based test set is retained, which is not used for training selection, suggestion optimization, or reward parameter tuning. First, human-to-human consistency is assessed, followed by judge-to-human consistency: Ordinal Krippendorff α, pairwise consistency rate, and confidence interval are reported dimensionally, along with stability after position swapping, the percentage of absence, and errors for each scenario. Consistency statistics only use the independent raw scores before the decision; in the pilot test, only the decision-makers with disagreements are considered, excluding the third random independent reviewer. High overall consistency rates may be masked by the majority class; specific confusion and failure cases need to be examined.

WritingBench supports the value of task-related rubrics; however, marketing creative research has found that judges may have significantly different preferences from industry professionals. The two measure different subjects and evaluate different groups, which is not contradictory. Directly inheriting a generic "total writing score" would miss this difference. [^5][^6]

## 5. How to fairly compare training with prompting/harnessing

Compare methods at the same checkpoint first, then compare different scales and suppliers. Both "quality under a fixed budget" and "cost/delay required to achieve a certain quality" must be published simultaneously, rather than including frequently called processes for free.

| Experimental arm | Procedure | Questions answered |
|---|---|---|
| B0 | Original draft unchanged | Is it really necessary to make changes?; Avoid equating progress with just minor text changes |
| B1 | Simple instructions: Keep the meaning clear and natural | Common user usage patterns, just the lower limit |
| B2 | Language/Domain-Specific Rubric + 3–5 Training/Development Sets with Positive and Negative Examples | What can a carefully designed single prompting session achieve? |
| B3 | First list the facts and issues → rewrite → independent fact-checking, with a maximum of one revision | Is an editor with evidence and checks sufficient? |
| B4 | Generate 4 candidates from the same material, select independently by a ranking algorithm | Can adding search during inference replace training? Consider the total generation and selection costs. |
| T1 | SFT adapter, with the same editing requirements as B2 after training | Incremental value of high-quality rewriting of supervision |
| T2 | Based on T1, DPO is performed, and preference pairs are manually validated. | Does preference supervision still offer benefits on top of SFT? |
| T3 | Optimal training model + same checking process as B3 | Are training and harness complementary? |
| H | Professional human editing | Based on human reference and time-saving editing standards, not intended as a cheap automated solution |

The same input, evidence packet, target language, output requirements, example sources, and model version are all frozen. Optimization is only performed using the dev method; each method is given an equal opportunity for optimization, and the number of attempts and selection criteria are recorded. For generated lengths, both natural results and length ranges specified in the requirements are reported; long drafts cannot be deleted afterward for the sake of "fairness," nor can content be altered by pruning.

Sampling temperature values may not be comparable across different models; save all supported decoding parameters and use dev to select appropriate settings. For reasoning models, record the thinking budget, hidden inference cost, and final output length. For critical arm models, at least evaluate generation randomness; validate the leading results of training the arm with multiple random seeds, without running all full factorial combinations initially.

The final main comparison pre-selects a winning trained system and a strongest untrained system, comparing them on untouched test sets. B0 and the hard subset continue as regression checks. Ablation covers at least: no examples, no independent verifiers, no preference stage, no generation conditioning, using only default weak AI negative examples, and the percentage of synthetic bad examples.

## 6. Training Path and Model Size

The recommended order is **strong baseline → edit SFT → favor DPO → online RL if necessary**. LoRA is an efficient parameter fitting method, QLoRA is a training method using a quantization base with an adapter, and SFT/DPO are different supervision targets; these are not mutually exclusive options at the same level. For detailed training explanations, the original paper, and official model cards, see [link to training documentation].[Training literature](research/09-12-training-literature.md).

SFT first learns specific revision methods and when to retain the original text. The DPO's chosen/rejected materials must be from the same task and factual material, and the chosen materials themselves must be fact-checked; do not create preference labels solely based on "shorter" or "lower vocabulary detector scores." For common high-frequency style errors encountered during training, the supervision signal should include the reasoning for the edit or the problem location, but the final rewritten output does not necessarily need to include explanations.

The first round of candidates primarily consists of a **bilingual (approximately 8–9 bytes) Chinese-English base**, with an **approximately 4 bytes** as a low-cost control. Then, one of either a **12–14 bytes** or a **27–32 bytes** base will be selected to verify whether capacity limits long text fidelity. Verifiable candidates include Qwen3.5-4 bytes, Qwen3.5-9 bytes, Qwen3-14 bytes, and Qwen3.8-27 bytes; these are candidates to be evaluated, not already ranked. Cross-family candidates and their architecture/licenses will be verified one by one using model cards.

First, use the same model and explicit language/genre conditions in all four scenarios to observe negative transfer. If improvements in Chinese marketing harm English technical documentation, then compare adapters by domain. Larger models may improve instruction compliance and fidelity, but do not guarantee better naturalness; model family, training data, and preference targets may all be more important. For multimodal/hybrid architecture models, plain text paths, trainable adapter modules, attention implementation, and quantization support need to be validated first.

Let's not start with online RL: at this point, the reward may not yet have sufficiently stable human support, and online optimization would amplify the evaluator's shortcuts. Only when reliable, stable, and SFT/DPO errors have emerged, and the reward is reliable in external evaluations, is it worthwhile to incur this additional cost.

Don't start with continued pretraining from excellent human articles. You can use it for subsequent style adaptation ablation, but distinguish it from editorial supervision. Also, don't choose 70B from the beginning: first determine whether the small model fails due to capacity or data/evaluation; otherwise, scaling up the model will only lead to more expensive repetition of the same mistake.

## 7. Phased sampling and stopping conditions

| Phase | Balanced arrangement of four scenarios | Delivery and conditions for proceeding to the next step |
|---|---|---|
| Rubric pilot | 80 independent tasks, 20 per segment; 2 initial evaluators + 1 dissent arbitrator | Assess whether evaluators can point out consistent issues and improvements; revision dimensions, retain dissent records, the pilot should not be used as the final test |
| Baseline development | 240 new tasks, 60 per frame | Adjust B1–B4, review failures and author voice loss; stop here if harness requirements are met and there are no cost issues |
| First Round SFT | Suggests 2,000 independent, verified rewrite pairs, approximately 500 per cell | First assess the learning curve and held-out dev; then expand to 5K–10K for scenarios still generating revenue. Quantity is not a guarantee of quality. |
| Preference stage | First, perform a small number of truly ambiguous preferences; expand to 1K–3K pairs if necessary | Only proceed if there is still a stable style bias after SFT; preference examples must satisfy factual constraints and be saved |
| Final Testing Locked | 800 new tasks, 200 per grid; 3 independent reviewers per pair for the main comparison | Training outperforms the strongest baseline while meeting fidelity, regression requirements for various scenarios, and practical cost constraints |

These figures represent an adjustable budget proposal. 800 primary pairwise comparisons, with 3 reviewers and 3–5 minutes per reading and evaluation, would require approximately **120–200 hours**, excluding recruitment, rubric training, lengthy document review, re-evaluation, and adjudication. Thousands of high-quality preference tags cannot be considered a free byproduct. Prioritizing all four scenarios means that each segment requires corresponding expertise.

The primary metric is the quality preference score for each task after the three reviews are summarized; additionally, the failure rate, uncertainty, and naturalness preference for both parties are listed separately. The training system is designated as A, and the scoring rules are as follows. The conditional win rate for both parties' compliance is used as a secondary metric to avoid survivorship bias caused by only screening qualified samples.

| Situation | Relative score of preset treatment and A |
|---|---|
| A is qualified, B fails confirmation | 1; Absolute failure of B is recorded separately |
| A fails, B succeeds| 0; absolute failure of A is recorded separately |
| Both sides confirm defeat | 0.5 for a relative tie, 1 for each side in an absolute defeat; neither side can claim the quality was satisfactory |
| Both parties qualified | For each reviewer, map A/B/tie to 1/0/0.5, then take the average; if A, B, and tie each have one vote, the score is 0.5, and the no-consensus flag is retained. |
| Evaluation of both_unacceptable | First check if the task was not recorded or if the hard constraint failed; if neither is good enough, award 0.5 points for the paired vote, and also award 0.5 points for both. |
| Any reviewer points out a significant factual error | Independent fact-checkers handle cases based on evidence, not by majority vote; a decision cannot be made before a ruling is made |
| If a system fails after empty output, timeout, or agreed-upon retries, | the system task is considered a failure and scored according to the aforementioned unilateral/bilateral failure rules; retention costs |
| Insufficient materials, uncertainty after fact-finding, or lack of review | First, conduct supplementary review or verification; if a judgment still cannot be made, retain the task, providing upper and lower bounds for the task's impact on the overall result using 0 and 1, without silent elimination or using a neutral 0.5 to mask the unknown.

All scheduled tasks remain in the total denominator; for pending tasks, report partial recognition intervals and coverage rates, and only tasks that still meet the threshold at conservative boundaries can pass. If a task package is found to be invalid, it is replaced according to the pre-registered rules that are blind to the model results, and the audit record is retained; tasks are not deleted based on wins or losses.

Four-cell equally weighted macro average, with each cell reported separately. Intervals are calculated based on independent task/source family cluster bootstrap; multiple reviews of the same manuscript, multiple samplings, and A/B reordering are not considered as new independent samples. Analysts need to consider rubric consistency and population differences, and cannot treat all aesthetic disagreements as a single "true value".

A sample threshold can be pre-registered: an overall quality preference score of 0.55 and a 95% lower bound exceeding 0.50; each cell meeting predetermined non-inferiority criteria; and a serious fact error rate meeting specific product requirements. **0.55 is the proposed minimum gain for the product, not a literature-recognized threshold.** After the pilot test and before the final test, the allowable backoff range, the upper limit of serious errors, and the confidence rules for multiple comparisons must be locked for each cell; failure to detect a significant decrease does not equate to non-inferiority, and insufficient evidence is marked as inconclusive. For n=200 cells with binary results close to 0.5, the average approximation 95% half-width is approximately 7 percentage points, and for n=800 cells, it is approximately 3.5 percentage points; ties, clustering, and multiple comparisons will alter accuracy. Therefore, this scale cannot be used to claim a significant improvement of 5 percentage points per cell.

Fidelity also requires uncertainty: Even with 200 independent tasks and zero serious errors, the commonly used rule-of-three approximation upper bound is still around 1.5%, which does not prove the true error rate is below 1%. To commit to a lower error rate, the sample size should be increased and error and confidence requirements predefined. The sample size is ultimately recalculated based on the variance, average percentage, cluster correlation, and desired effect in the pilot.

## 8. What else needs to be tested for both types of products?

The ultimate goal of technical documentation is for readers to correctly complete operations, find the required information, and avoid misunderstanding conditions. Retain code and identifiers, and run user tasks or reading comprehension tests when necessary. More "lively" sentences cannot compensate for instruction errors.

Marketing's ultimate goal depends on the channel: editorial adoption, brand fit, reader understanding, and, when conditions permit, real conversion experiments. CTR, conversion, and naturalness may have different focuses and cannot be substituted for one another. Formal campaigns require separate budgeting and experiment design; they are not triggered in this round. Existing marketing system research indicates that input materials, search, and workflows are all worth including in a control group. [^7]

Another test is conducted when a publishable version is ready: Blindly test editors revise the output to a usable state, recording the editing minutes, number of fact fixes, and final adoption rate. This identifies solutions with high judge scores but still requiring significant manual rework. The initial measurement is for research purposes and should not be used to calculate actual business ROI.

The cost breakdown includes annotation, training, hyperparameter tuning, inference, candidate selection, validation, and rework. The break-even call count can be written as:`额外一次性成本 /（baseline 每稿总成本 − trained 每稿总成本）` When the denominator is not greater than zero, there is no cost recovery based on the number of calls. GPU and API prices will be verified during actual experimental runs; no computational budget will be pre-allocated during the research phase.

## 9. The most worthwhile hypothesis to test at present

- The four scenarios may share some issues, but there is no universally applicable list of forbidden words across languages/domains.
- Given sufficient material, the 8–9B edit model may achieve strong harness quality with lower inference costs; this is more worthy of verification than assuming it necessarily surpasses all cutting-edge models.
- Fact-based accuracy and useful information constraints, coupled with professional editorial preferences, may provide better optimization signals than AI detection scores.
- If prompting has solved most style issues, the value of training may be primarily stability, latency, privacy deployment, or cost, rather than higher average writing quality.
- When the author's voice is diverse, a single preference model may write everyone with the same "natural voice"; configurable voices and positive examples that do not require modification are needed.

The next minimal executable step is to create a rubric pilot with 20 items in each of the four sections and collect real disagreements from professional editors. There's no need to purchase GPUs, crawl large corpora, or train independent discriminators yet.

## Reference source

[^1]: Raheja, Kumar, Koo & Kang. [CoEdIT: Text Editing by Task-Specific Instruction Tuning](https://aclanthology.org/2023.findings-emnlp.350/)Findings of EMNLP, 2023.
[^2]: Du et al. [Understanding Iterative Revision from Human-Written Text](https://aclanthology.org/2022.acl-long.250/)ACL, 2022.
[^3]: The original papers on style studies, their scope of observation, and conflicting results can be found in [Style Literature].](research/09-12-style-literature.md)The term "effective information content" here is a functional definition to be adopted in this project.
[^4]: The original sources of fact-finding, detector limitations, and judge bias can be found in [evaluation literature].](research/09-12-evaluation-literature.md)The two-way fidelity protocol is a feature of this project and should not be considered as a readily available indicator that has already been covered.
[^5]: Wu et al. [WritingBench: A Comprehensive Benchmark for Generative Writing](https://arxiv.org/html/2503.05244v4)2025, v4.
[^6]: Bhat, Browne & Bingemann. [Creativity Benchmark: A benchmark for marketing creativity for LLM models](https://arxiv.org/html/2509.09702v1)2025, preprint.
[^7]: Liu, Tahmasbi, Haque & Jain. [LLMs for Customized Marketing Content Generation and Evaluation at Scale](https://arxiv.org/html/2506.17863v1)2025, preprint.

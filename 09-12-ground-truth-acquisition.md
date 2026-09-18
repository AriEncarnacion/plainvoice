# Where does ground truth come from, and how is it transformed into training data?

2026-09-12. Status: Literature review and collection plan; no Plainvoice Gold papers have been collected and independently reviewed. The quantities below are pilot suggestions, not the optimal size proven by available data or papers. Chinese/English × Technical documents/Marketing four-panel format have equal priority. Scoring and anomaly handling remain the same.[Labeling Protocol](09-12-annotation-protocol.md)and[Main scheme](09-12-research-and-experiment-plan.md).

## 1. The most useful unit: rewrite comparison under the same input.

The user's suggestion of "the same content, one with a strong AI feel, the other natural and easy to read" is a good matching approach. A more accurate unit of recording is:

`任务与受众 + 原稿 + 内容依据与约束 + 候选 A/B + 独立人评`

"Same content" should be grounded in facts, intent, conditions, and certainty, not just the same topic or product. When comparing two articles about the same product, if one provides additional information such as price, customer stories, or features, then the preference is mixed in with the differences in content and cannot be attributed solely to writing style.

Whether the author is a person or a model should be kept separate from the quality. A human-written piece may contain a lot of clichés, while a model draft may require no revisions; both can originate from models. Do not predetermine a winner before judging, nor force each pair to produce a clear "good/bad" result. Retain tie-ins, pieces that are unqualified on both sides, and pieces that are impossible to judge.

Naturalness, readability, and actual usage preferences should be evaluated separately. Technical specifications can be formal and repeat necessary restrictions, while advertisements can be rhythmic or metaphorical. A sentence structure should not be considered a negative example simply because it appears.

A strict "pure style" subset requires the retention of important propositions in both directions. If the original manuscript itself contains errors, and the editor corrects them based on the source pack, this should be marked as a fact-fixing task; such improvements cannot all be considered "de-AI-style" effects. Without external evidence, one can only check the fidelity relative to the original manuscript; one cannot claim that the actual facts are correct.

## 2. Existing papers and publicly available data: What can be obtained?

The following entry point was checked during the initial research round; on the same day, the publicly available data was subsequently downloaded to the desktop as requested by the user.[Actual collection records](09-12-local-data-and-rewrite-pilot.md)The data from the paper can provide candidate and auxiliary tasks, but when reused, the human review of this project still needs to be completed.

| Data and Entry Points | Actual Data | Purpose and Boundaries of this Project |
|---|---|---|
| [AdParaphrase v2.0, Findings ACL 2025](https://aclanthology.org/2025.findings-acl.788/);[Author Data Warehouse](https://github.com/CyberAgentAILab/AdParaphrase-v2.0) | Japanese ads, 16,460 semantically equivalent copy pairs, each with appeal preferences for 10 people; additionally 8,721 dual-candidate records with the same input for preference tuning. | The data construction method closest to this project, but not in Chinese or English, and without AI-style tags. The method is borrowed and cannot be directly used as a four-panel gold grid. Repository labeled CC BY-NC-SA 4.0; commercial training use is not permitted by default. |
| [IteraTeR, ACL 2022](https://aclanthology.org/2022.acl-long.250/);[Author's Repository](https://github.com/vipulraheja/iterater) | Authentic English revisions. The HUMAN subset contains 4,018 sentence pairs, including human-edited intent labels; the FULL subset contains 196,987 sentence pairs, with intent labels predicted by the model. | Language and clarity modifications are prioritized, meaning-changed versions are excluded, and the final draft is reviewed for improvement. Human revisions should not be considered a guarantee. Original version publicly available; Plus/v2 requires Newsela access and contacting the author. Root repository Apache-2.0. Does not automatically state that all original sources are subject to the same license. |
| [arXivEdits, EMNLP 2022](https://arxiv.org/abs/2210.15067);[Author's Repository](https://github.com/chaojiang06/arXivEdits) | 1,039 adjacent versions of 751 papers; plus 2,122 human-annotated edits to 1,000 sentence pairs. | The Improve Language subset provides technical writing candidates; there are still domain differences between papers and product documentation. Updates to experiments or arguments must be made separately. Original licenses are provided per paper/version; a single repository license cannot cover all text.
| [MCTS, LREC-COLING 2024](https://aclanthology.org/2024.lrec-main.969/);[Author's Repository](https://github.com/blcuicall/mcts) | 723 original Chinese news sentences, each with 5 manually simplified references. Additionally, 691,474 machine-generated pseudo-parallel training sentence pairs. | Readability aid evaluation, not marketing/technical document gold. Simplification allows deletion of non-essential information; information must be reviewed and retained. Pseudo-parallel training data cannot be considered human-generated gold. The follow-up downloaded on the same day has obtained the GPLv3 LICENSE text from Git LFS; the specific use of the upstream news text still needs to be confirmed source-by-source. |
| [ASSET, ACL 2020](https://aclanthology.org/2020.acl-main.424/);[Author's Repository](https://github.com/facebookresearch/asset) | 2,359 original English sentences, each with 10 manually simplified references; officially, it's dev/test, without a training split. | Demonstrates "multiple reasonable rewrites per draft," suitable for simplified diagnostics; not AI-style labeling, and deletions should not be considered as fidelity assurance. CC BY-NC 4.0.
| [CoEdIT, EMNLP 2023](https://aclanthology.org/2023.findings-emnlp.350/);[Data card](https://huggingface.co/datasets/grammarly/coedit);[Public Version Description](https://github.com/vipulraheja/coedit) | Editing instructions in English / Original text / Target rewriting. The paper's training set is 82K, with approximately 69K publicly available train data; approximately 13K train data and 1.5K validation data are not publicly available due to licensing restrictions. | Assist in editing SFT. Grammar, formalization, and simplification tasks must be separated and cannot be uniformly treated as natural style examples. Data is labeled Apache-2.0, and its source and task are still recorded; do not confuse data with model weights and licenses.

What's particularly reusable about AdParaphrase is its two-stage annotation process: first, five people judge whether to provide an explanation, then the majority vote is used to filter, and finally, the appeal preferences of ten people are collected. `main` The original file retains unequal candidates, and the entire table cannot be treated as passed pairs.`pt` Preferences are directly collected for two rewrites of the same original manuscript; the winner of the DPO cannot be determined from two irrelevant comparisons.[Fields and Filtering Descriptions in the Author's Repository](https://github.com/CyberAgentAILab/AdParaphrase-v2.0)

Other [CAMERA, ACL 2024](https://aclanthology.org/2024.acl-long.54/) The system provides Japanese landing page/query → advertising data, but the same product can correspond to different appeals; such generated references cannot be taken as equivalent style pairs without verification. Currently, no ready-made complete gold data has been found that directly covers Chinese/English × marketing/technical documents while possessing both authenticity and natural feel tags; this is the conclusion of this search, not an assertion that "no relevant data exists."

## 3. Obtaining the main gold sample: Real model draft → Editing and revision → Independent blind review

This route is closest to actual product input and is recommended as the primary source.

1. **Establish Content Basis.** Technical documentation should use versioned documents with clearly defined usage rights, interface contracts, or original feature descriptions; marketing should use licensed/original product briefs, listing prices, features, target audience, channels, brand tone, and support commitments. Data should be collected natively in both Chinese and English, eliminating the need for translation to fill half the sample.
2. **Obtain original manuscripts with realistic distributions.** Collect manuscripts from actual writing tasks explicitly agreed upon for research purposes, or generate multiple model drafts from the same source pack. Override default suggestions and strong writing suggestions; record the complete model and suggestion versions. Do not specifically require the model to "write like AI," otherwise negative examples will be too easy to obtain.
3. **Rewritten by a suitable editor.** Editors can remove redundancy, rearrange information, change sentence structure, and adjust pacing; they cannot fabricate cases, figures, or promises. Reasons for changes must be retained, but reverting to the original version is also allowed. Technical editors are responsible for technical semantics; marketing editors must be familiar with the target market. Edited drafts are initially candidates, not automatically the answer.
4. **Independent review.** Reviewers conceal the source of the reviewer/model and randomly select the A/B group. Constraints are checked first, followed by evaluation of naturalness and adoption preferences. Editors do not review their own drafts. For pilots, each pair scores independently; disagreements are resolved by a third party, and original scores are permanently retained.
5. **Data is generated for different purposes.** Revised versions with credible improvements and that pass the constraints can be used as SFT objectives; explicit preferences can be used for DPO; tie-breaking results are retained for evaluation and training material that requires no modification. Error samples are left in the failure set and are not removed from the benchmark denominator simply because they are detrimental to performance.

This step requires real human editing and independent judgment. I can prepare source packs, generate candidates, compare and annotate interfaces, and propose editing candidates; results written by me and then self-evaluated can only be considered automatic candidates and cannot be impersonated as independent human gold.

## 4. Three supplementary routes and their deviations

| Route | How to obtain | Why not just calculate gold? |
|---|---|---|
| Good human-written original text → Model rewriting | Using authorized historical or newly written text, multiple models process it according to real editing instructions to form candidates with the same content. | The model may improve the original text. Human-written text should not be assumed to win; forced "AI-enhanced" synthetic degradation should only be used as a small proportion of diagnostic data to avoid only learning to reverse the fingerprint of a particular model.
| Natural Revision History | Obtain from publicly available and appropriately licensed version history, or before/after versions provided by the author; prioritize revisions that only change expression. | New versions may add features, change prices, or correct facts, and are not suitable for pure style comparisons. Even a live-action rewrite may be worse and still requires review. |
| Multiple Models/Multiple Prompt Candidates with the Same Original Draft | Maintain consistency between the original draft and constraints, rewrite different candidate methods, and then perform anonymous comparisons. | This is an efficient source of DPO candidates; the winner doesn't necessarily have to be human. Models that haven't undergone independent review are labeled as "silver"; the final test cannot be self-validated by the same optimization objective.

Pre-ChatGPT original texts can help determine the source history, but "early" does not guarantee quality; older texts may also have been seen by the base model during pre-training. New, unpublished original test materials can fill this gap. Don't just collect classic, good articles and mediocre model drafts, otherwise the date, subject matter, amount of information, and author level will all be mixed into the tags.

## 5. What to do first: Data collection pilot for 80 tasks.

The following is the proposed allocation. 20 independent source tasks per grid; the total remains at 80, and it is not a separate benchmark.

| Data Collection Route | Chinese Technical Support | English Technical Support | Chinese Marketing | English Marketing | Total |
|---|---:|---:|---:|---:|---:|
| Real model original + manually edited candidate | 10 | 10 | 10 | 10 | 40 |
| Manually prepared manuscript + natural revisions / Model rewriting candidates | 6 | 6 | 6 | 6 | 24 |
| Diagnostic tasks including identifying good drafts that require no revisions, providing reasonable comparisons, and identifying factual pitfalls | 4 | 4 | 4 | 4 | 16 |
| Total | 20 | 20 | 20 | 20 | 80 |

Each task can have multiple candidates, but the initial team selects one pair, resulting in 160 independent pair reviews, plus a disagreement resolution; this number does not include content preparation and 40 editing tasks. 80 tasks do not guarantee 80 clearly defined winning and losing training pairs. All labels are retained; the actual pass rate, disagreement rate, and individual task time determine the scaling cost.

Publicly available paper data should first be used as a separate auxiliary review pool, with random checks on content equivalence and task matching. Thousands of reference answers should not be used to replace the four-grid target task. The roles of the training set, judge calibration set, and test set should be explicitly recorded; pilots used for modifying rubrics or few-shots should no longer serve as final tests.

The pilot must answer the following questions: Can the reviewers point out consistent issues? Can the editors consistently improve the strong baseline? Are the improvements merely shortening or correcting facts? Do the four grids show differing preferences? Only if these results support continuing should the artificial gold be expanded, and a larger silver training set generated using a calibrated filtering process. Whether it's a few thousand or tens of thousands depends on the learning curve; the paper cannot provide a fixed answer for this task.

## 6. How to confirm content consistency and tag credibility?

- **First, examine the proposition.** List the facts and intentions that must be retained, and check for newly added unfounded statements, missing conditions, numbers, negations, changes in degree, and certainty. Code, commands, URLs, and identifiers should be checked separately. Automatic diffing/modeling can be helpful, but embedding similarity alone should not be used for approval.
- **Record Usage Constraints.** Retain length, channel, audience, and brand requirements. Shorter doesn't automatically win; more engaging content can't undo a poorly made promise. Don't let revised drafts gain an advantage through added content unless additional facts are requested.
- **Subjective differences are preserved.** Naturalness and the overall picture are evaluated separately; questions require excerpts and reasons, and tie/abstaining is permitted. Consistency before the decision is made is considered first; majority preference is evidence within a given population and context, not the only objective answer.
- **Grouping and Segmentation.** Documents, brand activities, historical versions, translations, and model-derived drafts are grouped into the same source family, segmented, and then candidate sources are derived. Five rewrites of the same original document cannot be treated as five independent test samples.
- **Source and usage rights are clearly indicated.** File version, date, editing/model source, and license are retained; notes and links are saved first for this project. Licenses for data import, training, and redistribution are verified separately.
- **Retain expired data.** Rejected revisions, ties, and difficult-to-judge cases are all useful; the main test uses the same denominator and failure rules as the full task. Do not only report the impressive win rate of the "fidelity pass subset".

## 7. How does the same annotation serve judge, SFT, and DPO?

| Applications | Data Shape | Key Conditions |
|---|---|---|
Judge Calibration and Evaluation | `context, draft, A, B, constraints, 原始各维评分与偏好` | Compare with the input; evaluate the judge based on human assessments, rather than having the judge define all gold. Finally, isolate the test results. |
| SFT | `context + draft → accepted_rewrite` The target draft should be constrained and suitable for the task; multiple reasonable targets are acceptable, and there should be a sample that requires no modification. There's no need to create a clearly inferior draft for every objective.
| DPO | `context + draft, chosen_rewrite, rejected_rewrite` Both drafts target the same input, directly assigning preferences, and the chosen criteria must be constrained by facts and the task. Ties, both drafts failing, and unresolved uncertainties are not directly converted into wins or losses. Rejected drafts may fail, but the failure type must be saved; a separate analysis is performed on the subset of style preferences where both drafts pass the constraints.

A set of "AI original A / edited B" can be directly used to construct the SFT from A to B. For DPO (Design for Production) applications, A can be kept as is as a valid candidate and directly compared with B; a more common approach is to generate B and C from A and then directly label B/C with preferences. Good and bad outputs from different originals should not be arbitrarily combined.

The final delivery should include: citations of the tasks and candidates, resolution of previous assessments and disagreements, applicable training/evaluation splits, scope of application, and evidence for each label. The model generates candidates, silver samples are automatically filtered, and gold samples are manually reviewed and counted separately. This round of delivery includes the data collection scheme and source verification; the actual data has not yet been generated.

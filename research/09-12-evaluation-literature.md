# Plainvoice: How to define ground truth and verify that "removing AI flavor" truly improves writing.

Implementation criteria: This memorandum retains the alternative scales and sizes derived from the literature; the first round will uniformly adopt...[Labeling Protocol v0.1](../09-12-annotation-protocol.md)The severity of the problem is 0–3, and[Main scheme](../09-12-research-and-experiment-plan.md)The 80 pilot, experimental arm numbering, and statistical rules.

Research Date: 2026-09-12. Scope: Chinese and English versions, technical documentation and marketing copies are given equal priority. This memo focuses on measurement and evaluation and is part of the first round of targeted literature review; it is not an exhaustive systematic review up to 2026. All references link to original papers or the authors' published texts; secondary articles are not used as the basis for conclusions.

## Core judgment

The user-suggested order of "first create the evaluator, then train the rewriter, and then compare it with prompting/harnessing" is basically reasonable, but the goal of the evaluator cannot be set as "detecting whether the author is AI." At least three things need to be separated:

| The object to be measured | Tag source | Purpose in this project |
|---|---|---|
| Provenance: Who actually generated it and what process was used? | Verifiable source, timestamp, generation logs, and edit records | Analyze data coverage and obfuscation factors; it cannot be directly used as a label for quality. |
| Perceived AI-ness: The degree to which readers perceive the templated, generalized, and mechanical approach | Blind review by target readers, preferably with specific textual evidence | User perception metrics, which must acknowledge cultural, linguistic, contextual, and individual differences |
| Writing utility: Accuracy, specificity, clarity, and applicability | Evaluation by editors/domain experts based on the brief and source materials; objective checks are conducted when applicable | The product's main objectives, along with content fidelity, serve as the basis for model selection |

Labeling pre-ChatGPT text as "good" and model-generated text as "bad" makes it easy to train classifiers based on era, vocabulary, website, and layout. High-quality human text, poor human clichés, excellent AI rewrites, and poor AI text should all be included in the labeling scope. AI sources are not negative, and human sources are not positive. This is a data design suggestion for this project, not a universally applicable classification method proven in any paper.

For user-generated examples like "not X, but Y," it's important to note whether they provide a true distinction, boundary, or mechanism. For instance, "This operation is not an append write, but an overwrite of an existing file" has significant implications; "This isn't an upgrade, it's a revolution" might only amplify emotions without supporting evidence. The frequency of sentence structure can help with identification, but it cannot solely determine quality. Avoid turning "removing the AI flavor" into another fixed tone.

## 12 key documents and their applicable boundaries

### E01. Humans can also confuse something that "sounds like a human" with its actual origin.

**Maurice Jakesch, Jeffrey T. Hancock, Mor Naaman. 2023. _Human heuristics for AI-generated language are flawed_. PNAS 120(11), e2208839120.** [DOI of the paper](https://doi.org/10.1073/pnas.2208839120) · [Full text of the author's preprint](https://arxiv.org/pdf/2206.07271)

Six experiments involving 4,600 participants examined self-introductions on professional, dating, and accommodation platforms. The primary experiments achieved an accuracy rate of approximately 50%–52% in identifying the source. First-person pronouns and family-related topics make the text sound more human, but may not actually reveal the source. On the other hand, having another group directly rate "repetitive" and "incoherent" texts revealed some genuine issues. The paper also demonstrates that texts selected based on human perception are more easily perceived as human-written than actual human writing.

This project adopts the following approach: Breaking down "template-like/vague/redundant" issues into locatable editing questions; and asking questions with an overall AI feel to prevent guesses about the source from dominating all scoring.

**Limitations:** This research uses English self-presentation and is based on an earlier model. It cannot be concluded that today's professional editors only have a random judgment level when it comes to Chinese technical documents. What is transferable is the measurement alert, not the accuracy rate.

**Reading scope:** The experimental setup, main results, heuristic analysis, optimization text, and discussion in the full text; all statistical models in the appendix have not been reviewed.

### E02. The detector's low perplexity signal may penalize clear, naive non-native English.

**Weixin Liang, Mert Yuksekgonul, Yining Mao, Eric Wu, James Zou. 2023. _GPT detectors are biased against non-native English writers_. Patterns 4(7), 100779.** [Full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC10382961/)

The study evaluated 91 TOEFL articles and 88 US eighth-grade articles using seven detectors. The average false positive rate for the TOEFL articles was 61.3%, which decreased to 11.6% after vocabulary enhancement. This is a result specific to the detector, sample, and time period, and does not represent the current false positive rate of all existing detectors. It suggests that rare words, complex expressions, and detection scores may be correlated.

This project adopts the following approach: Separately list non-native English segments; include clear, simple, and professional English examples. Do not train the model by intentionally adding rare words, grammatical errors, or colloquialisms to make it "human-like."

**Limitations:** The two groups differ in age, genre, and writing environment; this design cannot precisely attribute all differences to native language identity. The Chinese study should be independently validated; TOEFL conclusions cannot be directly applied.

**Reading scope:** Samples of the full text, false positives, vocabulary interventions, and discussions.

### E03. Multilingual detection datasets cannot be directly used as bilingual document quality datasets.

**Yuxia Wang et al. 2024. _M4: Multi-Generator, Multi-Domain, and Multi-Lingual Black-Box Machine-Generated Text Detection_. EACL.** [formal paper](https://aclanthology.org/2024.eacl-long.83/) · [PDF](https://aclanthology.org/2024.eacl-long.83.pdf)

M4 covers multiple generators, domains, and seven languages, including Chinese and English, and found that generalization across unseen domains and generators remains difficult. The Chinese portion consists of Baike/Web QA; the English portion includes Wikipedia, WikiHow, Reddit, arXiv, and PeerRead. Table 1 of the paper contains a total of 147,895 human/machine text entries, with 9,000 in Chinese, including 3,000 human text entries; do not interpret "parallel" as a faithful, sentence-by-sentence rewrite.

This project adopts:** drawing inspiration from cross-generator, cross-domain, and cross-language segmentation; it can be used for external distributed stress testing.

**Limitations:** The English and Chinese domains do not match, making it impossible to differentiate between language and domain influence solely based on overall scores; QA does not represent technical documentation or marketing copy. The required "Better Rewrite" preference tag is not available for this project.

**Reading scope:** Data construction, Table 1, Chinese source, human evaluation, and definition of cross-language experiments.

### E04. Detection scores are very fragile against decoding and surface modifications.

**Liam Dugan, Alyssa Hwang, Filip Trhlík, Andrew Zhu, Josh Magnus Ludan, Hainiu Xu, Daphne Ippolito, Chris Callison-Burch. 2024. _RAID: A Shared Benchmark for Robust Evaluation of Machine-Generated Text Detectors_. ACL.** [formal paper](https://aclanthology.org/2024.acl-long.674/) · [PDF](https://aclanthology.org/2024.acl-long.674.pdf)

The RAID contains over 6 million generations/variants, covering 11 generators, 8 main domains, 11 attack classes, and 4 decoding settings; 12 detectors were tested. Resampling methods, repetition penalties, generators, or surface forms all affect detection. The main set uses pre-2022 human sources; this is a proofreading choice and does not define human text as superior.

This project adopts the following approach: **Retaining complete metadata for decoding, model version, prompt, and source documents; all generation and rewriting of the same source document must be done within the same data partition.**

**Limitations:** The core task is detection; the main focus is not on Chinese marketing copy. Some stress tests can corrupt numerical data, therefore a "decrease in detection scores" does not necessarily indicate that rewriting is beneficial.

**Reading scope:** Data construction, generation settings, detector and threshold evaluation, limitations; attack not reproduced item by item.

### E05. The theoretical boundaries of detection cannot be exaggerated to the point that "any detection is ineffective".

**Vinu Sankar Sadasivan, Aounon Kumar, Sriram Balasubramanian, Wenxiao Wang, Soheil Feizi. _Can AI-Generated Text be Reliably Detected?_ 2023 first release; current reading 2025-01-17 v4.** [full text](https://arxiv.org/html/2303.11156v4)

The paper investigates the impact of recursive paraphrasing on multi-class detectors, and also points out that rewriting may slightly reduce text quality. Its theory links the upper bound of the optimal detector's AUROC to the total variation distance of the human/model text distribution: the closer the distributions are, the more difficult it is to identify the source.

**This project uses:** The detector is only used as a diagnostic indicator; natural and accurate AI rewriting may be difficult to detect, but the reverse is not necessarily true.

**Limitations:** The statement that "model progress will inevitably bring all real-world text distributions infinitely close" is not a fact directly proven by this theorem; actual TV is difficult to estimate accurately from finite texts. The paper does not prove that detectors are useless for all given domains.

**Reading Scope:** v4 abstract, paraphrase quality statement, Theory Section 4, Theorem 1 and hypothesis interpretation; proof not checked line by line.

### E06. Style transfer already has a more suitable multidimensional assessment tradition.

**Remi Mir, Bjarke Felbo, Nick Obradovich, Iyad Rahwan. 2019. _Evaluating Style Transfer for Text_. NAACL.** [formal paper](https://aclanthology.org/N19-1049/) · [PDF](https://aclanthology.org/N19-1049.pdf)

The paper distinguishes between style transfer intensity, content preservation, and naturalness, advocating for observation of the trade-offs among these objectives. In the Yelp sentiment transfer experiment, relative judgments of naturalness showed higher annotation consistency than absolute scores; however, style intensity did not show the same universal benefit. Sentence perplexity in this experiment was not significantly correlated with naturalness ratings.

This project employs the following approach: simultaneously recording the extent of rewriting, fidelity, naturalness, and task quality; using blinded pairwise preference as the primary comparison; and using multi-dimensional scoring to diagnose the causes.

**Limitations:** The boundaries of sentiment shifting are much clearer than those of open-ended "de-AI flavoring"; the word-level masking and WMD proposed in the paper should not be used directly as fact checkers for technical documents.

**Reading Scope:** Evaluation definition, human evaluation, results and tradeoff discussion; old model not reproduced.

### E07. A general LLM judge can be useful, but a meta-evaluation of the current task must be performed first.

**Lianmin Zheng et al. 2023. _Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena_. NeurIPS Datasets and Benchmarks.** [full text](https://arxiv.org/html/2306.05685)

The paper system analyzes limitations related to position, verbosity, self-preference, and reasoning ability. The GPT-4 judge achieves over 80% consistency on its specific human preference data; however, this is not a guarantee of accuracy for any new writing task or any new judge. It distinguishes between pairwise, single-answer scoring, and judging with reference answers.

This project employs the following methods: Hiding model names and sources, randomizing A/B sampling, and repeating a subset of samples with swapped order; comparing the consistency between the judge and domain editing on a calibration set, and reporting on four scenarios respectively. Using different families of judges can reveal discrepancies, but cannot prove that the biases are independent.

**Limitations:** General chat preferences do not equate to the effectiveness of professional copywriting; human evaluations may also favor long, neat, and confident answers.

**Reading Scope:** Assessment format, bias section, human agreement, and data definitions.

### E08. The feasible starting point of the Rubric judge and the risk of self-reinforcement come from the same paper.

**Yang Liu, Dan Iter, Yichong Xu, Shuohang Wang, Ruochen Xu, Chenguang Zhu. 2023. _G-Eval: NLG Evaluation using GPT-4 with Better Human Alignment_. EMNLP.** [formal paper](https://aclanthology.org/2023.emnlp-main.153/) · [PDF](https://aclanthology.org/2023.emnlp-main.153.pdf)

G-Eval uses task/dimension definition, evaluation steps, and structured form completion. The paper reports an average Spearman correlation of 0.514 on SummEval, while explicitly stating that the judge may favor LLM-generated abstracts and warning that directly using this evaluation for tuning may reinforce its own bias.

This project adopts the following approach: First, a rubric + anchor point sample + evidence spans are used as the evaluator baseline; then each dimension is calibrated separately. The evaluation output includes partial evidence and brief reasons, but this does not mean the reasons are necessarily correct; random sampling is still required.

**Limitations:** The preference is that LLM texts are used for preliminary analysis and potential interpretations within the paper, rather than general conclusions that have eliminated confounding factors; relevance in the abstract/dialogue cannot be directly extrapolated.

**Reading scope:** Methodology, SummEval Table 1, LLM output preference analysis, limitations.

### E09. Control the length, but do not replace "shorter is better" with a new reward.

**Yann Dubois, Balázs Galambosi, Percy Liang, Tatsunori B. Hashimoto. _Length-Controlled AlpacaEval: A Simple Way to Debias Automatic Evaluators_. 2024 first release; current reading 2025-03-10 v2.** [full text](https://arxiv.org/html/2404.04475v2)

By adjusting for output length differences through regression, the preference for outputs of the same length was estimated; in their AlpacaEval experiment, the Spearman correlation with Chatbot Arena rankings improved from 0.94 to 0.98. The authors explicitly listed the assumptions and boundaries of application: simple English instructions, a specific judge prompt, and the desire to compare outputs of the same length.

**This project employs:** Sensitivity analysis that simultaneously reports original preferences, length variation, information retention, and length matching.

**Limitations:** One of the goals of this project may be to eliminate unnecessary information, and the length is a mediating result actually generated by the method. Reporting only the score after controlling the length will also eliminate the real benefits; technical documents and taglines cannot be forced to have the same length, and Chinese and English token numbers cannot be directly mixed.

**Reading scope:** Definitions, regression control, main results, other biases, and limitations.

### E10. Rewrite using atomic facts checking, but recall must be added.

**Sewon Min, Kalpesh Krishna, Xinxi Lyu, Mike Lewis, Wen-tau Yih, Pang Koh, Mohit Iyyer, Luke Zettlemoyer, Hannaneh Hajishirzi. 2023. _FActScore: Fine-grained Atomic Evaluation of Factual Precision in Long Form Text Generation_. EMNLP.** [formal paper](https://aclanthology.org/2023.emnlp-main.741/) · [PDF](https://aclanthology.org/2023.emnlp-main.741.pdf)

FActScore breaks down long texts into atomic facts, checks each fact against credible sources, and then calculates factual precision. The paper explicitly states that it does not measure recall: saying less or nothing may reduce the chance of errors but still does not meet the task requirements.

This project employs the following approach: Two-way checks are performed on the rewrite: whether the added/changed assertions in the output are supported by supporting materials, and whether the assertions required to be retained in the original text are still fully present. Additionally, numbers, units, negations, conditions, versions, API identifiers, and commitment strength are checked.

**Limitations:** The input text itself may contain errors; a distinction must be made between "faithful to the original text" and "real-world accuracy." Rigorous mode should provide a source pack or a verified claim ledger. Marketing metaphors and opinions should not be treated as factual for scoring.

**Reading scope:** Definitions, knowledge source assumptions, scope of biography, precision/recall limitations.

### E11. Judges should be able to reject judgments that are "nice to hear but don't accomplish the task."

**Zhiyuan Zeng, Jiatong Yu, Tianyu Gao, Yu Meng, Tanya Goyal, Danqi Chen. 2024. _Evaluating Large Language Models at Evaluating Instruction Following_. ICLR.** [full text](https://arxiv.org/html/2310.07641v2) · [Author Data Warehouse](https://github.com/princeton-nlp/LLMBar)

LLMBar has 419 paired samples: 100 natural and 319 adversarial. In each pair, one sample follows the instructions, while the other deviates but may be more attractive or fluid. The authors used this to examine whether the judge was misled by surface quality and to test improved prompting methods for evaluation.

This project employs the following approach: Constructing challenge pairs such as "more colloquial but missing conditions," "more specific but fabricated data," "removing clichés but correcting meaning errors," and "more emotional but not in line with the brand." Constraint failures and style preferences are recorded separately.

**Limitations:** LLMBar's preferences are as objective as possible; the naturalness and brand fit of this project are subjective; it cannot be assumed that every rewrite pair has a single winner.

**Reading scope:** Task definition, 419 components, adversarial construction and prompting design.

### E12. Even with multiple sampling and selecting the best option, overfitting of the reward can still occur, not just in RL.

**Leo Gao, John Schulman, Jacob Hilton. 2023. _Scaling Laws for Reward Model Overoptimization_. ICML.** [formal paper](https://proceedings.mlr.press/v202/gao23h.html) · [PDF](https://proceedings.mlr.press/v202/gao23h/gao23h.pdf)

The paper trains a proxy reward model in a synthesized setting using a fixed gold reward model instead of a human. When optimizing the proxy, the gold score may initially increase and then decrease; the study also covers both reinforcement learning (RL) and best-of-n methods. Therefore, even with "untrained harnesses," there is a risk of over-optimizing the evaluator.

This project employs the following methods: Separating training/sampling judge from final blind evaluation; reserving a test set that has never been used in prompt iteration, checkpoint selection, or n selection. The aim is to observe whether the quality of human work decreases with optimization intensity.

**Limitations:** Gold is still a model, and the paper does not fully capture the discrepancy between human labels and actual needs; its scaling law coefficients cannot be directly used for budget forecasting in this project.

**Reading scope:** Research setup, RL/best-of-n definition and 4.5 limitations; experiments not reproduced.

## Suggested ground truth structure

The following are project design suggestions based on literature, which have not yet been actually collected or verified.

1. **Source Records.** Save the URL, fetch/archive date, original release date, author/brand, license, permitted use, language, domain, length, and source pack. Pre-ChatGPT pages should use a snapshot or verifiable version from that time, not just an old date on the page; older text may also have been included in the model's pre-training corpus.
2. **Content Constraints.** Each input corresponds to a manually verified claim ledger: essential facts, figures, conditions, terminology, evidence, CTAs, tone, and length constraints. Technical documentation retains its executability; marketing materials retain the basis for selling points and the boundaries of promises.
3. **Quality Tagging.** Independently evaluated by the target audience/editors, without showing them human/AI tags, model name, generation time, or detector score. Saves dimensional results, wins/losses, evidence fragments, and disagreements; does not automatically delete samples with no consensus.
4. **Rewrite Correction.** Within the same source pack, this includes the original file, minimal manual modifications, major rewrites, and outputs from different models/prompts. High-quality original files should be tagged "No Rewrite/Minor Modifications" to prevent forced changes to the model each time.

The most significant misconception to avoid is that the human author receives the complete factual context, while the AI only receives the title or a generic prompt, and then the evaluator rewards the human with specific information. The main experiment should give all methods the same source pack, audience, purpose, and length budget. The task of reconstructing the human author's text from the title alone can be retained, but only as a separate task.

Each of the four scenarios should comprise an equal number of core test units; Chinese should have its own independent original source and review process, not just translations of English. Simplified/Traditional Chinese, regional markets, and non-native English expressions need to be included as metadata or subsequent slices; comprehensive coverage cannot be claimed when the sample size is insufficient.

## The initial version of Rubric: First determine constraints, then consider the reader's experience.

It is recommended to use 1–5 levels per dimension and provide anchor points for the scenario; do not pre-compact all dimensions into an unverified "AI-like score of 0–100". The following is the initial tag definition; the weights and thresholds will be calibrated through small-scale human evaluation.

| Dimensions | Poor Performance | Good Performance | Recording Method |
|---|---|---|---|
| Retention of Facts and Intent | Fabricating Information, Deleting Conditions, Changing Negations, Transforming Possibility into Guarantee | Retaining Necessary Information, Causality, Boundaries, and Uncertainty | Major Failures/Minor Problems/Passage; Evidence Location |
| Information Contribution | Synonyms, vague openings, restatements at the end, useless evaluative words | Each paragraph should provide facts, explanations, evidence for judgment, or necessary transitions | 1–5; redundant spans; omitted claims |
| Specific and Verifiable | False specificity, fabricated figures, statements applicable to all brands | Specific to the scenario, object, mechanism, evidence, and next steps | 1–5; Indicate the materials relied upon |
| Structure and Sentence Naturalness | Symmetrical templates, mechanical three-point structures, overuse of inversion sentences and subheadings | Structure should follow content, sentence length and emphasis should be natural | 1–5; High scores should not be obtained by relying on spelling errors |
| Scenario Adaptation | Technical documentation is overly sentimental; marketing copy focuses on implementation details; it doesn't match the reader's background | Technical content is actionable, marketing content has a clear audience and commitment | 1–5; Use Case Rubric |
| Brand/Author Voice | Replace all sources with the same tone and fabricate personal experiences | Retain necessary individuality and terminology, and conform to the given references | 1–5; excluding if no reference is available |
| Subjective AI Feeling | Readers perceive it as obviously generalized and templated | Readers perceive it as natural, content-rich, and purposeful | Independent 1–5; not interpreted as source probability |
| Overall Usability | Still requires extensive rewriting, or we dare not use it | Can be adopted directly or only minor modifications are needed | A/B/Tie/Neither is usable + Reasons for adoption |

Technical documentation should undergo specific checks, including: preconditions, commands and parameters, return values, exceptions and boundaries, version, permissions, and error recovery information. If the original document contains code, syntax checks or relevant example execution checks should be performed; avoid creating formalistic tests for purely textual transformations.

Marketing-specific checks: audience, question/benefit, differentiating rationale, evidence, brand voice, CTA, and prohibitions. Don't mistake copywriting preferences for CTR/CVR; real conversions require independent experimentation and control over factors such as audience, channel, and offer.

## Minimum evaluator calibration and model benchmark

**Calibration Phase.** It is recommended to start with 30–50 brief/source units per scenario, totaling 120–200 units; this is a budget-friendly design suggestion, not a statistical power guarantee. For each unit, select a small number of output pairs with varying quality, and have at least three suitable reviewers conduct blind reviews. Jason can provide some anchor points and preferences. Invite reviewers with experience in the relevant domain and familiarity with the corresponding language for both technical and marketing roles. Record the reasons for consistency and disagreement, and then revise the rubric.

**Judge Selection.** Compare simple rule features, single-model rubric judge, and another family of judges; use ensemble only if calibration data demonstrates its benefit. Report at least the consistency with humans across all dimensions, pairwise accuracy (in a subset with human consensus), tie-breaking, A/B flip rate, non-native language/language slices, and forced constraint false negative rate. Repeated prompts for the same model do not count as independent evidence.

**Challenge Set.** Includes already good text, valid comparative sentences (allowed), very simple but correct English, formal Chinese technical specifications, short slogans, long documents, and rewrites that sound good but contain significant factual errors. Special checks will be conducted to see if "deleting content only," "changing numbers," "intentionally misspelling words," "adding unsubstantiated anecdotes," or "making all sentences colloquial" will fool the judge.

**Fair Comparison.** Compare no-op, basic rewrite prompt, rubric + examples prompt, critique-rewrite harness, best-of-n, SFT, and preference tuning on the same frozen test set. Each method is tuned only on the development set; the same factual material and task constraints are given during evaluation. Report the same single inference budget and actual quality-cost curve separately; harness extra invocations, latency, and training amortization should not be hidden. The final judge should not be the sampling reward for all methods.

**Main Results.** Prioritize reporting the "Overall Adoption Preference Rewritten" and "Major Fidelity Failure Rate" results, and retain four independent tables and equally weighted averages for each scenario. For samples with errors but better readability, record the original preference while simultaneously disqualifying them according to the pre-defined major failure rules; do not filter out failed samples before only promoting survivor win rates. Auxiliary results should include reports on redundancy reduction, necessary fact recall, unsupported claim rate, editing time, length changes, and subjective AI perception.

**Statistics and Segmentation.** Divide the dataset into train/dev/test segments based on source/brief, ensuring maximum isolation by author, brand, site, and derivative versions; then perform tests with the generator and new date data. Confidence intervals should be resampled by source clustering to avoid treating multiple rewrites of the same source text as independent samples. When using training runs with at least two different random seeds to validate candidate results, seed outputs should not be mixed into independent text samples. Sample size should be planned for effectiveness after pilot testing based on actual variation and the expected minimum benefit; a small batch of "looks good" samples should not be used to declare superiority over prompting.

**Judgment on whether to continue training.** First, prove that humans can reliably identify expected rewriting and that the judge can capture this preference before proceeding with training. If the strong prompt/harness has already achieved its goal, the value of post-training may mainly lie in cost, latency, stability, and deployment methods; if only the automatic judge score improves while the human score does not improve, the optimization of the same reward should not be further increased.

## Evidence not yet established

- These 12 papers cannot prove that there is a unified "AI-flavored" scalar between Chinese and English, or between technical docs and marketing, nor can they prove that using the same reward can improve all four scenarios simultaneously.
- Authorized corpora have not yet been collected, real human evaluations have been conducted, judges have been calibrated, models have been tested, or training has been run; the figures in this article are from the original papers and are not the results of the Plainvoice experiment.
- Professional creative evaluations may differ significantly from general writing evaluations. The main research will separately cover marketing-related work such as the 2025 Creativity Benchmark; marketing judges should not be determined solely based on MT-Bench / G-Eval.
- This round is for targeted background research, with the focus on improving the performance metrics of the first round of experiments to avoid misleading the proxy. The final selection of the base, training method, and cost will be based on another training survey and field tests.

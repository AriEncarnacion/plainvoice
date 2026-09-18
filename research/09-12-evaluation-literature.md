# Plainvoice: How to define ground truth, and verify that "removing AI-ese" really did improve the writing

Operative scope: this memorandum keeps the candidate scales and sample sizes derived from the literature; the first round uniformly adopts the 0–3 problem severity of the [annotation protocol v0.1](../09-12-annotation-protocol.md), together with the 80-item pilot, the experiment-arm numbering, and the statistical rules of the [main plan](../09-12-research-and-experiment-plan.md).

Research date: 2026-09-12. Scope: Chinese and English, technical documentation and marketing copy — the four scenarios have equal priority. This memo focuses on measurement and evaluation and belongs to the first round of targeted literature research; it is not an exhaustive systematic review up to 2026. Every reference links to the original paper or to body text published by the authors; no secondary article is used as the basis for a conclusion.

## Core judgment

The order the user proposed — "build the evaluator first, then train the rewriter, then compare against prompting / harness" — is broadly reasonable, but the evaluator's target must not be set to "detect whether the author is an AI." At least three things have to be kept apart:

| Object to be measured | Source of labels | Use in this project |
|---|---|---|
| Provenance: who actually produced it, and by what process | Verifiable sources, timestamps, generation logs, edit records | Analysing data coverage and confounding factors; it cannot be used directly as a quality label |
| Perceived AI-ness: how templated, generic, and mechanical readers find it | Blind evaluation by target readers, ideally with concrete textual evidence | A user-perception metric; it must acknowledge cultural, linguistic, contextual, and individual differences |
| Writing utility: whether it is accurate, specific, clear, and fit for purpose | Assessed by editors/domain experts against the brief and source material; objective checks where applicable | The product's primary objective; together with content fidelity it is the basis for choosing a model |

Labelling pre-ChatGPT text "good" and model-generated text "bad" makes it very easy to train a classifier for era, vocabulary, website, and layout. High-quality human writing, bad human boilerplate, good AI rewrites, and bad AI text should all enter the annotation scope. AI provenance is not the negative class, and human provenance is not the positive class. This is a data-design recommendation for this project, not a universal taxonomy that some paper has already proven.

For the 「不是 X，而是 Y」 (*"not X, but rather Y"*) construction the user raised, annotate whether it supplies a real distinction, boundary, or mechanism. For example, 「此操作不是追加写入，而是覆盖现有文件」 (*"this operation is not an append write, but an overwrite of the existing file"*) carries important meaning, whereas 「这不是一次升级，而是一场革命」 (*"this is not an upgrade, it is a revolution"*) may merely add emotion when no evidence is given. The number of occurrences of the pattern can help locate candidates; it cannot decide quality on its own. Avoid turning "removing AI-ese" into just another fixed register.

## 12 key papers and their limits of applicability

### E01. Humans, too, confuse "sounds human" with actual provenance

**Maurice Jakesch, Jeffrey T. Hancock, Mor Naaman. 2023. _Human heuristics for AI-generated language are flawed_. PNAS 120(11), e2208839120.** [Paper DOI](https://doi.org/10.1073/pnas.2208839120) · [Full text of the authors' preprint](https://arxiv.org/pdf/2206.07271)

Six experiments with 4,600 participants in total examined self-presentations on professional, dating, and accommodation platforms. Accuracy at judging provenance in the main experiments was about 50%–52%. First person, family topics, and the like make readers feel the text is more human, yet may not actually distinguish provenance. On the other hand, when a separate set of readers was asked to rate "repetitive" and "not fluent" directly, some real problems could be measured. The paper also shows that text selected on the basis of human perception is judged human-written more readily than actual human writing.

**Adopted by this project:** break "sense of templatedness / vagueness / redundancy" into locatable editing problems; ask about overall AI-ness as a separate question, so that guesses about provenance do not dominate every score.

**Limitations:** this is a study of English self-presentation with an earlier model; it cannot be extended to conclude that today's professional editors are also at chance level on Chinese technical documentation. What transfers is the measurement caution, not the accuracy figure.

**Reading scope:** the experimental setup, main results, heuristic analysis, optimized texts, and discussion in the full text; the appendix's statistical models were not re-checked.

### E02. A detector's low-perplexity signal may penalize clear, plain non-native English

**Weixin Liang, Mert Yuksekgonul, Yining Mao, Eric Wu, James Zou. 2023. _GPT detectors are biased against non-native English writers_. Patterns 4(7), 100779.** [Full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC10382961/)

The study used seven detectors to evaluate 91 TOEFL essays and 88 US eighth-grade essays; the average false-positive rate on the TOEFL essays was 61.3%, dropping to 11.6% after the vocabulary was enriched. This is a result for particular detectors, samples, and a particular moment in time, not the current false-positive rate of every detector in use. It shows that rare words, elaborate expression, and detection scores may be bound together.

**Adopted by this project:** keep a separate non-native-English slice; put clear, plain, professional English into the positive examples. Do not train the model to deliberately add rare words, grammatical errors, or spoken filler in order to seem "human."

**Limitations:** the two sets of writers also differ in age, genre, and writing environment; the design cannot attribute all of the difference precisely to native-speaker status. Chinese should be validated independently; the TOEFL conclusions cannot simply be carried over.

**Reading scope:** the samples, false positives, vocabulary intervention, and discussion in the formal full text.

### E03. A multilingual detection dataset cannot serve directly as a bilingual copy-quality set

**Yuxia Wang et al. 2024. _M4: Multi-Generator, Multi-Domain, and Multi-Lingual Black-Box Machine-Generated Text Detection_. EACL.** [formal paper](https://aclanthology.org/2024.eacl-long.83/) · [PDF](https://aclanthology.org/2024.eacl-long.83.pdf)

M4 covers multiple generators, multiple domains, and seven languages including Chinese and English, and finds that generalization to unseen domains and generators remains difficult. Its Chinese portion is Baike/Web QA; the English portion includes Wikipedia, WikiHow, Reddit, arXiv, and PeerRead. Table 1 of the paper gives a total of 147,895 human/machine texts, of which 9,000 are Chinese, including 3,000 human texts; do not read "parallel" as faithful sentence-by-sentence rewrite pairs.

**Adopted by this project:** borrow its cross-generator, cross-domain, and cross-language splits; it can be used as an external-distribution stress test.

**Limitations:** the Chinese and English domains do not match, so language effects and domain effects cannot be separated from the overall scores alone; QA does not stand in for technical documentation or marketing copy. It does not carry the "better rewrite" preference labels this project needs.

**Reading scope:** data construction, Table 1, the Chinese sources, human evaluation, and the definitions of the cross-language experiments.

### E04. Detection scores are very fragile with respect to decoding and surface changes

**Liam Dugan, Alyssa Hwang, Filip Trhlík, Andrew Zhu, Josh Magnus Ludan, Hainiu Xu, Daphne Ippolito, Chris Callison-Burch. 2024. _RAID: A Shared Benchmark for Robust Evaluation of Machine-Generated Text Detectors_. ACL.** [formal paper](https://aclanthology.org/2024.acl-long.674/) · [PDF](https://aclanthology.org/2024.acl-long.674.pdf)

RAID contains over 6 million generations/variants, covering 11 generators, 8 main domains, 11 classes of attack, and 4 decoding settings; 12 detectors were tested. Changing the sampling method, the repetition penalty, the generator, or the surface form all affect detection. The main set uses pre-2022 human sources; that is a provenance choice, and it does not define human writing as excellent.

**Adopted by this project:** retain complete metadata for decoding, model version, prompt, and source document; every generation and rewrite of the same source text must sit in the same data partition.

**Limitations:** the core task is detection, and the main set is not Chinese marketing copy. Some stress tests damage content such as numbers, so a "drop in detection score" cannot by itself show that the rewriter is beneficial.

**Reading scope:** data construction, generation settings, detector and threshold evaluation, limitations; the attacks were not reproduced item by item.

### E05. The theoretical limits of detection must not be inflated into "no detection works at all"

**Vinu Sankar Sadasivan, Aounon Kumar, Sriram Balasubramanian, Wenxiao Wang, Soheil Feizi. _Can AI-Generated Text be Reliably Detected?_ First released 2023; v4 of 2025-01-17 read this round.** [full text](https://arxiv.org/html/2303.11156v4)

The paper studies the effect of recursive paraphrasing on several classes of detector, and also notes that paraphrasing may slightly reduce text quality. Its theory links the AUROC upper bound of the optimal detector to the total variation distance between the human and model text distributions: the closer the distributions, the harder provenance is to identify.

**Adopted by this project:** the detector serves only as a diagnostic indicator; natural, accurate AI rewrites may also be hard to detect, but the converse does not necessarily follow.

**Limitations:** "model progress must bring every real-world text distribution infinitely close" is not a fact this theorem directly proves; in practice TV is hard to estimate precisely from finite text. The paper does not prove that detectors are useless in every given domain.

**Reading scope:** the v4 abstract, the note on paraphrase quality, the theory in Section 4, Theorem 1 and the explanation of its assumptions; the proof was not checked line by line.

### E06. Style transfer already has a better-suited multi-dimensional evaluation tradition

**Remi Mir, Bjarke Felbo, Nick Obradovich, Iyad Rahwan. 2019. _Evaluating Style Transfer for Text_. NAACL.** [formal paper](https://aclanthology.org/N19-1049/) · [PDF](https://aclanthology.org/N19-1049.pdf)

The paper distinguishes style transfer intensity, content preservation, and naturalness, and argues for watching the trade-offs among these objectives. In the Yelp sentiment transfer experiment, relative judgments of naturalness had higher annotation agreement than absolute scores; style intensity, however, showed no comparable general gain. Sentence perplexity in that experiment was not significantly correlated with human evaluation of naturalness.

**Adopted by this project:** record the extent of the rewrite, fidelity, naturalness, and task quality together; use blinded pairwise preference for the main comparison, and per-dimension scores to diagnose the cause.

**Limitations:** sentiment transfer has far clearer boundaries than open-ended "removing AI-ese"; the word-level masking and WMD the paper proposes should not be used directly as a fact checker for technical documentation.

**Reading scope:** the evaluation definitions, human evaluation, results, and the tradeoff discussion; the older models were not reproduced.

### E07. A general-purpose LLM judge can be useful, but meta-evaluation on the task at hand must come first

**Lianmin Zheng et al. 2023. _Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena_. NeurIPS Datasets and Benchmarks.** [full text](https://arxiv.org/html/2306.05685)

The paper systematically analyses position bias, verbosity bias, self-preference, and limited reasoning ability. The GPT-4 judge reaches over 80% agreement on its particular human preference data; that is not an accuracy guarantee for any new writing task or any new judge. It distinguishes pairwise comparison, single-answer scoring, and judging with a reference answer.

**Adopted by this project:** hide model names and provenance, randomize A/B, and repeat a portion of the samples with the order swapped; compare the agreement between the judge and domain editors on a calibration set, reporting the four scenarios separately. Using judges from different families can surface disagreement, but cannot prove the biases are independent.

**Limitations:** general chat preference is not the same as professional copy performing well; human evaluation itself may also favour long, tidy, confident answers.

**Reading scope:** the evaluation formats, the bias sections, human agreement, and the data definitions.

### E08. The workable starting point for a rubric judge and the risk of self-reinforcement come from the same paper

**Yang Liu, Dan Iter, Yichong Xu, Shuohang Wang, Ruochen Xu, Chenguang Zhu. 2023. _G-Eval: NLG Evaluation using GPT-4 with Better Human Alignment_. EMNLP.** [formal paper](https://aclanthology.org/2023.emnlp-main.153/) · [PDF](https://aclanthology.org/2023.emnlp-main.153.pdf)

G-Eval uses task/dimension definitions, evaluation steps, and a structured form to fill in. The paper reports an average Spearman correlation of 0.514 on SummEval, while explicitly raising the possibility that the judge favours LLM-generated summaries, and warning that feeding such evaluation straight into tuning may reinforce its own preferences.

**Adopted by this project:** start with rubric + anchor examples + evidence spans as the evaluator baseline; calibrate each dimension separately. Having the evaluation output local evidence and a short rationale does not mean the rationale is necessarily correct; spot checks are still required.

**Limitations:** the preference for LLM text is, in the paper, a preliminary analysis and a possible explanation, not a general conclusion with confounders ruled out; correlations on summarization/dialogue cannot be extrapolated directly.

**Reading scope:** the method, SummEval Table 1, the analysis of preference for LLM output, and the limitations.

### E09. Control for length, but do not turn "shorter is better" into a new reward

**Yann Dubois, Balázs Galambosi, Percy Liang, Tatsunori B. Hashimoto. _Length-Controlled AlpacaEval: A Simple Way to Debias Automatic Evaluators_. First released 2024; v2 of 2025-03-10 read this round.** [full text](https://arxiv.org/html/2404.04475v2)

Regression is used to adjust away differences in output length and estimate the preference that would hold at equal length; in their AlpacaEval experiment, the Spearman correlation with Chatbot Arena rankings rose from 0.94 to 0.98. The authors state the assumptions and limits of applicability explicitly: simple English instructions, a particular judge prompt, and a wish to compare outputs of the same length.

**Adopted by this project:** report the raw preference, the change in length, information retention, and a length-matched sensitivity analysis together.

**Limitations:** one of this project's goals may be precisely to cut the filler, and length is also a mediating outcome the method genuinely produces. Reporting only the length-controlled score would cancel out the real gain along with it; technical documentation and a tagline cannot be forced to the same length, and Chinese and English token counts cannot simply be pooled.

**Reading scope:** the definitions, the regression control, the main results, other biases, and the limitations.

### E10. Check rewrites with atomic facts, but recall has to be added back

**Sewon Min, Kalpesh Krishna, Xinxi Lyu, Mike Lewis, Wen-tau Yih, Pang Koh, Mohit Iyyer, Luke Zettlemoyer, Hannaneh Hajishirzi. 2023. _FActScore: Fine-grained Atomic Evaluation of Factual Precision in Long Form Text Generation_. EMNLP.** [formal paper](https://aclanthology.org/2023.emnlp-main.741/) · [PDF](https://aclanthology.org/2023.emnlp-main.741.pdf)

FActScore breaks long text into atomic facts, checks one by one whether a trustworthy source supports each, and then computes factual precision. The paper states explicitly that it does not measure recall: saying less, or saying nothing, can cut the chance of error and still fail the task.

**Adopted by this project:** check rewrites in both directions — whether the assertions the output adds or changes are supported by the source material, and whether the assertions the source draft requires to be kept are still present in full. Also check numbers, units, negations, conditions, versions, API identifiers, and the strength of commitments.

**Limitations:** the input text may itself be wrong; "faithful to the source draft" and "correct in the real world" must be kept apart. Strict mode should supply a source pack or a human-confirmed claim ledger. Marketing metaphors and opinions cannot all be scored as if they were facts.

**Reading scope:** the definitions, the knowledge-source assumptions, the biography scope, and the precision/recall limitations.

### E11. The judge must be able to reject "sounds good but did not do the task"

**Zhiyuan Zeng, Jiatong Yu, Tianyu Gao, Yu Meng, Tanya Goyal, Danqi Chen. 2024. _Evaluating Large Language Models at Evaluating Instruction Following_. ICLR.** [full text](https://arxiv.org/html/2310.07641v2) · [Authors' data repository](https://github.com/princeton-nlp/LLMBar)

LLMBar has 419 paired samples: 100 natural and 319 adversarial. In each pair one member follows the instruction and the other departs from it, yet may be more appealing and more fluent. The authors use this to check whether the judge is misled by surface quality, and to test prompting methods that improve evaluation.

**Adopted by this project:** construct challenge pairs such as "more colloquial but drops a condition," "more specific but fabricates data," "removes the boilerplate but gets the meaning wrong," and "more emotive but off-brand." Record constraint failures separately from style preference.

**Limitations:** LLMBar's preferences are as objective as they can be made, whereas this project's naturalness and brand fit are subjective; it cannot be assumed that every rewrite pair has a single winner.

**Reading scope:** the task definition, the composition of the 419 items, the adversarial construction, and the prompting design.

### E12. Sampling many and picking the best also overfits the reward — this is not confined to RL

**Leo Gao, John Schulman, Jacob Hilton. 2023. _Scaling Laws for Reward Model Overoptimization_. ICML.** [formal paper](https://proceedings.mlr.press/v202/gao23h.html) · [PDF](https://proceedings.mlr.press/v202/gao23h/gao23h.pdf)

In a synthetic setting, the paper substitutes a fixed gold reward model for humans and trains a proxy reward model. As the proxy is optimized, the gold score may rise and then fall; the study covers both RL and best-of-n. A "training-free harness" therefore also carries the risk of over-optimizing the evaluator.

**Adopted by this project:** keep the training/sampling judge separate from the final blind evaluation; hold out a test set never used for prompt iteration, checkpoint selection, or choosing n. Observe whether human-rated quality falls as optimization pressure rises.

**Limitations:** gold is still a model, and the paper does not fully capture the gap between human labels and real needs; its scaling-law coefficients cannot be applied directly to this project's budget forecasts.

**Reading scope:** the study setup, the RL/best-of-n definitions, and the 4.5 limitations; the experiments were not reproduced.

## Suggested ground truth structure

The following are project design recommendations based on the literature; no real collection or verification has been done yet.

1. **Source records.** Save the URL, the fetch/archive date, the original publication date, the author/brand, the licence, the permitted scope of use, the language, the domain, the length, and the source pack. Pre-ChatGPT pages should use a snapshot from that time or a verifiable version, not merely an old date printed on the page; old text may also already have entered a model's pre-training corpus.
2. **Content constraints.** Each input has one human-verified claim ledger: facts that must not be dropped, numbers, conditions, terminology, evidence, CTA, tone, and length constraints. Technical documentation keeps its executability; marketing material keeps the grounds for its selling points and the boundaries of its promises.
3. **Quality labels.** Evaluated independently by target readers/editors, who are not shown the human/AI label, the model name, the generation time, or detector scores. Keep the per-dimension results, the win/loss/tie, evidence fragments, and disagreements; samples without consensus must not be deleted automatically.
4. **Rewrite pairs.** Under the same source pack, include the source draft, a minimal human edit, a larger rewrite, and outputs from different models and different prompts. A high-quality source draft needs a "no rewrite needed / minor edit" label, to stop the model from forcing a change every time.

The single most important confound to avoid is this: the human source text gets the complete factual background while the AI gets only a title or a one-line generic prompt, and the evaluator then rewards the human's specificity. The main experiment should give every method the same source pack, audience, purpose, and length budget. A task of reconstructing the human source text from the title alone can be kept, but only as a different task.

The four scenarios each account for the same number of core test units; Chinese needs its own native sources and reviewers, not just translated English. Simplified/traditional characters, regional markets, and non-native English expression should be carried as metadata or as later slices; comprehensive coverage must not be claimed while the sample is too small.

## Initial rubric: judge the constraints first, then the reader's experience

The recommendation is 1–5 levels per dimension with anchors supplied for that scenario; do not collapse every dimension in advance into an unvalidated "AI-ese score of 0–100." Below are the initial label definitions; the weights and thresholds await calibration by small-scale human evaluation.

| Dimension | Poor performance | Good performance | How it is recorded |
|---|---|---|---|
| Fact and intent preservation | Fabricating information, deleting conditions, flipping negations, stating a possibility as a guarantee | Preserving necessary information, causality, boundaries, and uncertainty | Major failure / minor issue / pass; evidence location |
| Information contribution | Synonymous repetition, empty openings, closing restatement, evaluative words that do nothing | Every paragraph supplies a fact, an explanation, grounds for a judgement, or a necessary transition | 1–5; redundant span; missing claim |
| Specific and verifiable | False specificity, numbers invented out of thin air, lines that would fit any brand | Specific to the scenario, the object, the mechanism, the evidence, and the next step | 1–5; state the material relied on |
| Structure and sentence naturalness | Symmetrical templates, mechanical rule-of-three, overuse of reversal sentences and subheadings | Structure follows content; sentence length and emphasis feel natural | 1–5; a high score must not be earned through typos |
| Scenario fit | Technical documentation waxing lyrical; marketing copy piling up implementation detail; mismatched to the reader's background | Technical content is actionable; marketing content has a clear audience and a clear promise | 1–5; per-scenario rubric |
| Brand/author voice | Rewriting every source into one tone; fabricating personal experience | Keeping the necessary individuality and terminology, consistent with the given reference | 1–5; may abstain when there is no reference |
| Subjective AI-ness | Readers find it plainly generic and templated | Readers find it natural, substantive, and clearly purposeful | Independent 1–5; not to be read as a probability of provenance |
| Overall usability | Still needs extensive rewriting, or you would not dare use it | Can be used as is, or needs only a small edit | A/B/tie/neither usable + reason for the choice |

Checks specific to technical documentation: preconditions, commands and parameters, return values, exceptions and boundaries, versions, permissions, and error-recovery information. If the source contains code, a syntax check or execution of the relevant examples can be run; do not invent formalistic tests for purely textual transformations.

Checks specific to marketing: audience, problem/benefit, reason for differentiation, evidence, brand voice, CTA, and forbidden promises. Do not treat human evaluation preference on copy as CTR/CVR; real conversion requires a separate experiment with audience, channel, offer, and similar factors controlled.

## Minimum evaluator calibration and model benchmark

**Calibration phase.** The suggested starting point is 30–50 brief/source units per scenario, 120–200 in total; this is a budget-friendly design recommendation, not a guarantee of statistical power. For each unit, pick a small number of output pairs that differ in quality and have at least three suitable reviewers evaluate them blind; it is enough for Jason to supply a portion of the anchors and preferences. For technical and for marketing separately, invite reviewers who have experience in that domain and are familiar with the language in question. Record the agreement and the reasons for disagreement, then revise the rubric.

**Judge selection.** Compare simple rule-based features, a single-model rubric judge, and a judge from another family; adopt an ensemble only where the calibration data shows it helps. Report at least per-dimension agreement with humans, pairwise accuracy (on the subset where humans agree), how ties are handled, the A/B flip rate, the non-native and per-language slices, and the miss rate on hard constraints. Repeating a prompt against the same model does not count as independent evidence.

**Challenge set.** Include text that was already good, permitted and genuinely effective contrast sentences, very plain but correct English, formal Chinese technical specifications, short slogan copy, long documents, and rewrites that read well but carry a major factual error. Check specifically whether "delete content only," "change the numbers," "introduce deliberate typos," "add an unsourced anecdote," and "make every sentence colloquial" can fool the judge.

**Fair comparison.** On the same frozen test set, compare no-op, a basic rewrite prompt, a rubric + examples prompt, a critique–rewrite harness, best-of-n, SFT, and preference tuning. Each method is tuned only on the dev set; at evaluation time every method gets the same factual material and task constraints. Report separately at an equal single-inference budget and as an actual quality–cost curve; the harness's extra calls, its latency, and amortized training cost must not be hidden. The final judge must not double as the sampling reward for all the methods.

**Main results.** Report two results first — "overall adoption preference for the rewrite" and "major fidelity failure rate" — and keep the four scenarios in separate tables alongside an equally weighted average. For a sample that reads better but contains an error, record the raw preference and at the same time mark it as failing under the pre-defined major-failure rule; failed samples must not be filtered out first so that only the survivors' win rate is advertised. Supporting results report redundancy reduction, recall of necessary facts, unsupported claim rate, editing hours, length change, and subjective AI-ness.

**Statistics and splits.** Split train/dev/test by source/brief, quarantining authors, brands, sites, and derived versions as whole units as far as possible; then add a held-out-generator test and a new-date test. Confidence intervals should be resampled with clustering by source, to avoid treating multiple rewrites of one source text as independent samples. Where training runs with at least two different random seeds are used to validate a candidate result, the seeds' outputs must not be pooled as independent text samples. Sample size should be power-planned after the pilot from the observed variance and the minimum benefit worth detecting; a small batch that "looks good" cannot be used to declare superiority over prompting.

**Deciding whether to go on to training.** First show that humans can reliably tell the desired rewrite apart and that the judge can capture that preference; only then train. If a strong prompt/harness already reaches the goal, the value of post-training may lie mainly in cost, latency, stability, and how it is deployed; if only the automatic judge score improves while human evaluation does not, optimization against that same reward should not be pushed further.

## Evidence not yet established

- These 12 papers cannot prove that a single unified "AI-ese" scalar exists across Chinese and English, or across technical docs and marketing, nor that one and the same reward can improve all four scenarios at once.
- No licensed corpus has been collected yet, no real human evaluation has been run, no judge has been calibrated, no model has been tested, and no training has been run; the figures in this memo come from the original papers and are not Plainvoice experimental results.
- Professional creative evaluation may differ substantially from general writing evaluation. The main research separately covers marketing-related work such as the 2025 _Creativity Benchmark_; the marketing judge should not be decided on MT-Bench / G-Eval alone.
- This round is targeted background research, and its point is to keep the first round of experiments from getting better at optimizing the wrong proxy metric; the final base model, training method, and cost choices need to be made together with the separate training literature review and with real measurements.

# AI writing style: evidence, counter-evidence, and the object of evaluation

Research date: 2026-09-12. Scope: linguistic explanations of "AI-ese," post-training-related evidence, genre differences, Chinese-language evidence, and the implications for product evaluation. What follows is selective background research, not an exhaustive systematic review. Only the original papers, official publisher versions, and author versions of papers are treated as evidence; media coverage, social media discussion, and commercial "de-AI-ese" copy found in the search results were not used as a factual basis.

## First, be clear about what the product is actually supposed to change

"AI-ese" is best defined, to begin with, as **a particular reader's perception, within a particular writing task, of expressions that are contextually inappropriate, formulaic, vague, or stripped of the author's voice**. This is this project's testable working definition, not an existing consensus scale. It is related to authorship, detectability, writing quality, factual accuracy, genre fit, and commercial effectiveness, but these quantities are not interchangeable.

Three senses of "information density" that are routinely conflated need to be pulled apart:

- **Syntactic/lexical density**: how densely noun phrases, nominalizations, modifying structures, and content words are packed; this kind of density may make a text harder to read.
- **Effective information density**: how many relevant, specific, source-supported propositions each paragraph delivers, and whether they move the reader toward completing the task. This requires the project's own annotation and verification.
- **Information-theoretic surprisal/entropy**: predictability relative to some model's distribution; it is not the value of the content to the reader, nor is it directly equivalent to factual novelty.

High density of the first kind and low density of the second can perfectly well occur together. Taking "shorter, more colloquial, more rare words" directly as the reward for removing AI-ese would simply induce another fixed writing style.

The following features should first be treated as annotation hypotheses, not as blanket prohibition rules:

| Candidate dimension | Actionable check | Counter-examples that must be preserved |
|---|---|---|
| Vagueness and repetition | Whether deleting a sentence loses any fact, reasoning step, or action; whether there is an opening or closing that only restates the topic | Explanation needed for teaching, necessary safety preconditions, a summary of the key actions |
| Unnecessary rhetorical antithesis | In `不是 X，而是 Y` (*"not X, but rather Y"*), whether anyone actually asserts X, and whether Y draws a real distinction | Clarifying a common misconception, defining a boundary, correcting an actual error |
| Unsupported specificity | Whether figures, experiences, customer cases, causal claims, and guarantees can be grounded in the input | Writing more specifically using facts from the input; labelling assumptions explicitly |
| Register mismatch | Who it is written for, what it is meant to do, what the reader already knows; whether it reads like good real work in that genre | Technical specifications need consistent terminology; long-form marketing may legitimately use rhetoric |
| Formulaic patterns and over-ornamentation | Recurring openings of the same kind, parallelism, exaggerated adjectives; whether the structure serves the content | Lists that are genuinely required, a set of three items that really are parallel, real product differences |
| Author voice and stance drift | Whether the rewrite changes the degree of conviction, the judgments, the emotion, the personal wording, or the narrative perspective | The user explicitly asked for the stance to be rewritten, or for a switch to a particular brand voice |
| Cross-document homogenization | After the same model rewrites work by different authors and for different tasks, whether structure and viewpoint converge excessively | Naming and formatting in an API reference ought to be uniform |

This round found no high-quality direct empirical evidence strong enough to support the claim that "all models significantly overuse the Chinese `不是，而是` (*"not X, but rather Y"*), and the cause is known." The user's observation deserves a place in the hypothesis set, but it must not be passed off as already quantitatively confirmed, and it cannot be used to infer anything about a model's training data or reward mechanism.

## Twelve directly relevant primary studies

### S1 — Style bias and the direct comparison with instruction tuning

**Alex Reinhart, Ben Markey, Michael Laudenbach, Kachatad Pantusen, Ronald Yurko, Gordon Weinberg, David West Brown. _Do LLMs write like humans? Variation in grammatical and rhetorical styles._ PNAS, 2025; first preprint 2024.**

[Published paper](https://doi.org/10.1073/pnas.2422455122) · [Full-text version read](https://arxiv.org/html/2410.16107v2)

Methods, Results, and Discussion read. Two multi-genre parallel corpora of English, each starting from 12,000 human-written texts; the model was given roughly the first 500 words and asked to continue in the same style; base/instruct versions of GPT-4o/mini and Llama 3 8B/70B were compared. 66 Biber features show that instruct models lean further toward nominalization, participial clauses, and other dense written structures; larger model size did not automatically narrow the style gap. **Limitations**: this is mainly a continuation task; the base/instruct difference cannot isolate SFT, preference optimization, data, or other post-training steps. The paper also states explicitly that precise attribution is not possible. Its "informationally dense" is grammatical packaging, not more valuable facts. Implications for the project: test genre fit, keep a base model as a control, and do not rely on scaling the model alone.

### S2 — The origin of “delve” has not been clearly explained

**Tom S. Juzek, Zina B. Ward. _Why Does ChatGPT “Delve” So Much? Exploring the Sources of Lexical Overrepresentation in Large Language Models._ COLING, 2025.**

[Paper PDF](https://aclanthology.org/2025.coling-main.426.pdf)

§§4–7, the abstract, and Appendix B/D read. The study identifies 21 words that are overrepresented in scientific abstracts and compares candidate training corpora, Llama base/chat, and a human preference experiment. The evidence bearing on post-training is indirect and mixed: the base/chat comparison bundles SFT together with RLHF; the experiment with 201 Indian participants did not conclusively confirm that preferred words cause a reward bias. **Limitations**: neither "RLHF causes delve" nor "the English of annotators from a particular country causes AI-ese" may be written down as a conclusion. The project should record word frequencies within a genre and avoid building permanent blacklists that span languages and use cases.

### S3 — Homogenization can come from the model's contribution, not from all of the user's language variation

**Vishakh Padmakumar, He He. _Does Writing with Language Models Reduce Content Diversity?_ ICLR, 2024; first preprint 2023.**

[Official ICLR entry](https://proceedings.iclr.cc/paper_files/paper/2024/hash/02dec8877fb7c6aa9a79f81661baca7c-Abstract-Conference.html) · [Full text read](https://arxiv.org/html/2309.05196v2)

§§1–3, the results summary, and Appendix A read. 38 native English speakers with writing or editing experience wrote 300 argumentative essays in total, comparing an unassisted condition, GPT-3, and InstructGPT; which suggestions were accepted and how much model text was actually retained were recorded. Essays in the InstructGPT condition were more similar to one another and lower in content and lexical diversity, while GPT-3 showed no comparably significant result; the authors localize the main change to the model-contributed portion. **Limitations**: an old model, short essays, and a requirement to request suggestions at least five times per essay. No long-term conclusion about all natural usage settings can be drawn from this; it does, however, support measuring single-piece quality and whole-batch content diversity separately.

### S4 — Cross-genre and decoding both change style metrics

**Sergio E. Zanotto, Segun Aroyehun. _Linguistic and Embedding-Based Profiling of Texts Generated by Humans and Large Language Models._ EMNLP, 2025.**

[Official entry](https://aclanthology.org/2025.emnlp-main.1163/) · [Paper PDF](https://aclanthology.org/2025.emnlp-main.1163.pdf)

The abstract, §3 Data, the feature descriptions, the conclusions, and §8 Limitations read. Using RAID's eight English domains, 11 models, and four classes of decoding configuration, the study analyses sentence length, dependency relations, lexical and semantic features, and style embeddings. Both humans and models vary by domain, but humans vary more on the features measured; newer models are closer to one another in style. **Limitations**: model vintage is not a randomized intervention, so the result cannot be attributed to synthetic training data; the models used are not 2026 frontier models; dependency features are not the same thing as user experience. The project's benchmark needs to fix or record the decoding settings and to test across domains.

### S5 — A more recent rewriting study: style compression and content preservation can occur together

**Zhivar Sourati, Farzan Karimi-Malekabadi, Meltem Ozcan, Colin McDaniel, Alireza Ziabari, Jackson Trager, Ala N Tak, Meng Chen, Fred Morstatter, Morteza Dehghani. _The shrinking landscape of linguistic diversity in the age of large language models._ Nature Human Behaviour, 2026-08-24.**

[Official DOI](https://doi.org/10.1038/s41562-026-02550-0) · [Official abstract](https://pubmed.ncbi.nlm.nih.gov/42637911/) · [Author version read](https://arxiv.org/html/2502.11266v2)

The official abstract was verified as covering three studies and seven datasets; in the author version, Study 1a/1b, Study 2, and the limitations of the detection method were read. Combining observational time series with having models polish existing text, it finds a compression in the variance of writing complexity. **Limitations**: real-world AI authorship is estimated by a detector; Granger prediction does not prove interventional causality; high embedding similarity is not enough to prove that every fact and every stance was preserved. Do not treat its "semantic preservation" and S8's "semantic drift" as simply mutually exclusive: the tasks, the metrics, and the granularity of interest all differ.

### S6 — Counter-evidence: the appearance of AI-preferred words does not mean lexical diversity has declined

**Sarah Fitterer, Dominik Gangl, Jannes Ulbrich. _Testing English News Articles for Lexical Homogenization Due to Widespread Use of Large Language Models._ ACL Student Research Workshop, 2025.**

[Official entry](https://aclanthology.org/2025.acl-srw.95/) · [Paper PDF](https://aclanthology.org/2025.acl-srw.95.pdf)

The abstract, the discussion of results, and §4 Conclusion read. Comparing English online news from 2018 and 2024: metrics for AI-style words rose, but the changes in MATTR and Maas were negligible and MTLD rose, giving no support for a "decline in lexical diversity." **Limitations**: there is no per-article log of actual AI use; news topics, editorial processes, and time all changed together. This is not the same thing as the "complexity variance" S5 measures. The project cannot sum homogenization up in a single lexical diversity score, still less assume that more diversity is always better.

### S7 — Higher quality in the individual piece and collective convergence are not in contradiction

**Anil R. Doshi, Oliver P. Hauser. _Generative AI enhances individual creativity but reduces the collective diversity of novel content._ Science Advances, 2024.**

[Published paper](https://doi.org/10.1126/sciadv.adn5290) · [Full-text PDF at the author's institution](https://discovery.ucl.ac.uk/10195027/1/Generative%20AI%20enhances%20individual%20creativity%20but%20reduces%20the%20collective%20diversity%20of%20novel%20content.pdf)

The Results returned by the publisher (including story similarity) and the Discussion read. In an online experiment writers either worked unassisted or received one AI story idea, or up to five; in blind evaluation, novelty, usefulness, and readability improved, and writers with lower initial creativity benefited more, but the stories were more similar to one another. **Limitations**: ordinary participants, miniature stories, restricted interaction with the ideas; this is not a professional marketing rewrite experiment. It refutes the notion that "content that looks like AI must be of lower quality," and it also shows that preference on a single piece cannot stand in for diversity of brand and author voice across a whole batch.

### S8 — Rewriting may change the stance; this study's causal claims need to be narrowed

**Marwa Abdulhai, Isadora White, Yanming Wan, Ibrahim Qureshi, Joel Leibo, Max Kleiman-Weiner, Natasha Jaques. _How LLMs Distort Our Written Language._ arXiv 2603.18161, 2026-03-18, preprint.**

[Full text](https://arxiv.org/html/2603.18161v1)

§3, §4.2–4.3, the abstract, and the discussion read. It covers a writing experiment with 100 people, plus 86 ArgRewrite-v2 essays collected in 2021, comparing human and model revisions across three vendors' models and five classes of editing instruction. It finds that even edits restricted to grammar may change the argument. **Limitations**: heavy use was defined by behaviour after random assignment, so that subgroup difference cannot be treated as a randomized dose effect; embedding displacement also mixes style with content; the real-review portion partly relies on an AI detector. The project can reuse the paired-revision design, but must verify claim by claim separately, and cannot sign off on embeddings alone.

### S9 — "Completeness" in technical documentation must be aligned with the page and the reader's context

**Karen de Souza, Alexandre Nikolaev, Maarit Koponen. _Generative AI for Technical Writing: Comparing Human and LLM Assessments of Generated Content._ NoDaLiDa/Baltic-HLT, 2025.**

[Paper PDF](https://aclanthology.org/2025.nodalida-1.67.pdf)

§§3, 4.3, and 5–7 read. 12 prompts against the Nokia Network as Code documentation, three models, and two temperatures produced 72 RAG answers; a professional technical writer's DQF-MQM assessment, an LLM judge, and BLEU/ROUGE were compared. In one concrete case, the human held that a prerequisite stated on another page did not need restating and marked the answer correct; the LLM deducted heavily because that condition was absent. **Limitations**: a single human evaluator, a proprietary RAG implementation, and older models. This study does not measure "AI-ese" directly, but it shows that an evaluator for technical documentation needs error categories, the reader's task, and context; surface lexical similarity and a generic notion of "comprehensiveness" will distort the picture.

### S10 — The counter-example closest to a marketing product: real effect and style preference must be tested separately

**Jean-Pierre Dubé, Ariel Xu. _Large Language Models and Creative Content Design: a case study of email marketing at Wine Access._ Quantitative Marketing and Economics, 2026-01-13.**

[Publisher full text](https://link.springer.com/article/10.1007/s11129-025-09303-9)

§3.1, §4, §5, and §6 read. Three rounds of real-world email RCT: the first two rounds used a Mistral7B customized on 3,148 historical emails, while the third switched to prompting Claude; human-written, AI, and human-edited AI were compared. The business judgment took revenue and writing cost into account. **Limitations**: a single wine brand, short term; training and prompting are spread across rounds and the model changed too, so this is not an equal-conditions ablation of methods; a non-significant difference in effect does not prove equivalence; the net-profit projection depends on assumptions about labour cost. Prompting cannot be declared the winner on this basis, but it does show that a strong prompting baseline must be compared against, and that "feels less like AI-ese" and a lift in conversion should be validated separately.

### S11 — Chinese: More complex does not equal more natural or higher quality

**Longhui Zou, Ke Li, Joshua Lamerton, Mehdi Mirzapour. _GenAIese — A Comprehensive Comparison of GPT-4o and DeepSeek-V3 for English-to-Chinese Academic Translation._ PSLT, 2025.**

[Official entry](https://aclanthology.org/2025.pslt-1.1/) · [Paper PDF](https://aclanthology.org/2025.pslt-1.1.pdf)

The abstract, §2, and §6 read. 11 English-language papers on language, culture, and literature, 3,498 sentences translated into Chinese; DeepSeek-V3 scored higher on automatic QE, while GPT-4o was higher in lexical richness and syntactic complexity. **Limitations**: there is no human translation as a reference, and no naturalness evaluation by native Chinese speakers; Chinese AI-ese cannot be defined on this basis, nor can naturalness be ranked. It does supply clues to Chinese-relevant features such as left-branching and the distance of noun modification, and it is a reminder not to transplant English nominalization and participial-clause scales directly.

### S12 — Source labels on Chinese social media carry a risk of circular judgment

**Yulong Ma, Xinsheng Zhang, Jinge Ren, Runzhou Wang, Minghu Wang, Yang Chen. _Linguistic features of AI mis/disinformation and the detection limits of LLMs._ Nature Communications; online 2025-12-11, volume 17/article 456 for 2026.**

[Publisher full text](https://www.nature.com/articles/s41467-025-67145-1)

The abstract, the RQ1 discussion, and the data construction and annotation methods read. The linguistic differences between long Chinese Toutiao articles and short MCFEND texts depend on content quality; the direction of the Chinese dependency-distance effect seen here cannot be mapped directly onto the English findings. **Key limitation**: the human/AI source of the Toutiao texts was judged by hand on the rule "if any passage is suspected of being AI, the whole article counts as AI," and the quality labels come mainly from two LLMs plus expert arbitration. Training an AI-ese judge on labels like these would circularly write the identifier's existing impressions into the ground truth; the evidence from the controlled-generation portion for short texts is clearer, but the task there is mis/disinformation and does not extrapolate to professional marketing or technical documentation.

## Specific revisions to the original plan

1. **Keep the pre-ChatGPT data, but treat it as source evidence and style reference; it cannot automatically be labelled "high quality" or "low AI-ese."** Old marketing copy has its own clichés too; old technical documentation may no longer apply. Every item must be independently annotated with quality, genre, language, audience, period, source, and usage licence.
2. **Build at least four crossed cells: human-good, human-bad, AI-good, AI-bad.** The AI and human source labels are for diagnosis, not as a reward for style quality. Add human-edited AI text, human text polished by AI, and "no rewrite needed" samples of excellent input, so that the edit rate itself is not mistaken for success.
3. **Build paired writing and rewriting from the same factual material.** A "similar prompt" on its own routinely omits the product facts, the experience, and the target audience the original author had in hand; when the model is vague as a result, that is an input problem. Keep the source packet, the writing brief, the source draft, the editing constraints, and the revised draft, and mark who introduced each missing fact.
4. **Calibrate the evaluation with humans first, then train a judge.** Human evaluators do not have to reach full consensus on a single "AI-ese, 1–5" score; domain editors can mark problems paragraph by paragraph, give paired preferences with reasons, and report their disagreements. An automatic judge may be used for iteration only after it has been validated on an independently held-out human evaluation set.
5. **Make task completion and fidelity the gate, and only then optimize voice.** For technical documentation, check the terminology, parameters, constraints, and whether the steps can actually be carried out; for marketing, check whether promises and product facts have been inflated and whether the CTA matches the audience. Neither should lean on invented detail to add a "human touch."
6. **Measure at the article level and the corpus level separately.** A single piece may read better while a whole batch of articles turns into one voice. Hold out test sets by author and by brand, measure the variation across different samplings of the same input, and also measure the degree to which different inputs get rewritten into the same structure.
7. **Comparisons of training methods must hold conditions constant.** The original model, prompting with general rules, exemplar prompting within the same genre, a step-by-step harness with semantic checks, and SFT/preference optimization should all use the same inputs and the same held-out human evaluation. Extra sampling, judge calls, and human time all have to be counted as cost. Find the clusters of errors where prompting still reliably fails before deciding what training is supposed to learn.

### A first, genre-specific version of the human evaluation task

| Task | Content that should be preserved a priori | Main style problems | Suitable human evaluators and external outcomes |
|---|---|---|---|
| API / how-to documentation | Parameters, return values, errors, conditions, code, cross-page context | Unnecessary introductions, restated prerequisites, vague benefits, terminology drift | A technical writer plus real users; success rate and time to find information or complete an operation |
| Long-form product marketing | Verified features, audience, positioning, pricing, the limits of what is promised | Abstract praise, piled-up synonyms, unfounded specificity, the brand voice disappearing | An editor who knows the industry and the brand; clicks, conversion, and trust measured separately later |
| Short ads / headlines | Genuine differentiation, specific selling points, length and channel constraints | Dense adjectives, a one-size-fits-all slogan, a CTA with no object | A copywriter who knows the channel; settled in the end by a randomized business experiment |
| Personal essay / professional opinion | The author's original stance, degree of conviction, evidence, examples | Automatic neutralization, false balance, unsourced escalation, the voice disappearing | The author themselves plus a blind-reviewing editor; fidelity and quality of expression measured separately |

The table above is an experimental design this project is proposing, not a unified rubric that the twelve papers have already validated.

## Conclusions mapped to evidence

| Conclusions that can be stated | Main basis | Claims that would overreach |
|---|---|---|
| Some models show systematic genre and grammatical bias | S1, S4 | That all models, languages, and genres behave alike |
| Post-training very likely plays a part in style narrowing | S1, S2, S3 | That a particular RLHF algorithm or annotation region has been confirmed as the root cause |
| A larger model is not a sufficient condition for better style | S1 | That a small model is all any task needs |
| Single-piece quality and whole-batch diversity can be separated | S3, S5, S6, S7 | That AI text is necessarily lexically impoverished or necessarily badly written |
| Rewrite fidelity needs to be verified on its own | S8, plus the metric limitations of S5 | That high embedding similarity proves there is no semantic drift |
| Technical documentation must be evaluated in context | S9 | That more comprehensive and longer is always better, or that shorter is always better |
| Marketing style and business effect must be measured separately | S10 | That removing AI-ese necessarily improves conversion; that some particular training approach is bound to win |
| Chinese needs its own calibration set and its own features | S11, S12 | Scoring Chinese directly with English AI high-frequency word and syntax tables |

Evidence work still outstanding: no unified "AI-ese" benchmark has yet been found that covers both Chinese and English, both technical docs and marketing, and has been validated by human annotation across multiple domains; this round also ran no training or reproduction experiments, so no figure can be given for the actual gain of post-training relative to the strongest prompting. The existing research amply supports launching a project to do measurement and controlled comparison; it does not yet support betting up front on a particular algorithm, model size, or single reward.

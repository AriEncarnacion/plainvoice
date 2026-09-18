# AI writing style: evidence, counter-evidence, and the object of evaluation

Research Date: 2026-09-12. Scope: Linguistic interpretations of "AI flavor," post-training related evidence, genre differences, Chinese evidence, and implications for product evaluation. The following is a selection of background research, not an exhaustive systematic review. Only original papers, official publishers, and author versions are considered evidence; media, social media discussions, and commercial "de-AI flavor" copywriting in search results are not considered factual evidence.

## First, clarify exactly what needs to be changed in the product.

"AI flavor" is suggested to be initially defined as **a specific reader's perception of expressions that are out of context, formulaic, vague, or lack the author's voice in a specific writing task.** This is a verifiable working definition for this project, not an existing consensus scale. It is related to author identity, verifiability, writing quality, factual accuracy, genre suitability, and commercial effectiveness, but these quantities are not interchangeable.

It is important to distinguish between the three commonly used terms related to "information density":

- **Syntactic/lexical density**: the density of noun phrases, nominalization, modifying structures, and content words; this density can make an article more difficult to read.
- **Effective information density:** How many relevant, specific, and supported propositions does each paragraph provide, and how well do they motivate the reader to complete the task? This requires the project's own annotation and verification.
- **Information theory surprise/entropy**: the predictability of a distribution relative to a certain model; it is not the value of content to the reader, nor is it directly equivalent to the novelty of facts.

The first type of high density and the second type of low density can coexist. Using "shorter, more colloquial, and more rare words" directly as a reward for removing AI flavor will also induce another fixed writing style.

The following features should be used as annotation assumptions rather than as global disabling rules:

| Candidate Dimensions | Actionable Checks | Negative Examples That Must Be Retained |
|---|---|---|
| Vagueness and Repetition | Does deleting a sentence result in the loss of facts, reasoning, or actions? Is it merely a restatement of the beginning or end of the title? | Explanation required for teaching, necessary safety prerequisites, and summary of key actions |
| Unnecessary Rhetorical Contradictions | In the statement "Not X, but Y," is X claimed, and does Y truly differentiate the two? | Clarifying Common Misconceptions, Defining Boundaries, and Correcting Actual Errors |
| Unsupported Specificity | Can figures, experiences, customer cases, causal relationships, and warranties be supported by the input? | Write more specifically using the input facts; clearly label the assumptions.
| Inappropriate style | Who is it written for, what is it about, and what does the reader know? Does it resemble excellent works of the genre? | Technical specifications require consistent terminology, while marketing articles can appropriately use rhetoric.
| Formulas and Overemphasis | Repetitive use of similar openings, parallel structures, and exaggerated adjectives; Does the structure serve the content? | Required lists, truly parallel three-item structures, genuine product differences |
| Author's Voice and Stance Shift | Does rewriting alter the degree of conviction, judgment, emotion, personal wording, and narrative perspective? | Users explicitly request a rewrite of the stance or a change to a specific brand's voice |
| Cross-document homogenization | After rewriting the same model for different authors/tasks, do the structure and viewpoints become excessively similar? | API reference naming and formatting should be consistent.

This round of research did not find sufficient high-quality direct empirical evidence to support the claim that "all models significantly outperformed the Chinese '不是，而是' and the reason is known." User observations are worth including in the hypothesis set, but cannot be presumed to have been quantitatively verified, nor can they be used to infer the model's training data or reward mechanism.

## Twelve directly related original studies

### S1 — A direct comparison between style deviation and instruction tuning

**Alex Reinhart, Ben Markey, Michael Laudenbach, Kachatad Pantusen, Ronald Yurko, Gordon Weinberg, David West Brown. _Do LLMs write like humans? Variation in grammatical and rhetorical styles._ PNAS, 2025; first preprint 2024. **

[formal paper](https://doi.org/10.1073/pnas.2422455122) · [I have read the full version.](https://arxiv.org/html/2410.16107v2)

I have read the Methods, Results, and Discussion sections. Two parallel corpora of English texts across multiple genres were used, each starting with 12,000 human-written texts. The first 500 words were given a requirement to continue writing in the same style. The base/instruction models of GPT-4o/mini and Llama 3 8B/70B were compared. 66 Biber features showed that the instruction model was more skewed towards nominalization, participial clauses, and other dense written structures; larger corpora did not automatically reduce the style difference. **Limitations**: Primarily related to the writing task; the difference between base/instruction cannot isolate SFT, preference optimization, data, or other post-training steps. The paper also explicitly states that precise attribution is not possible. Its "informationally dense" is grammatical wrapping, not a greater amount of valuable information. Implications for the project: Testing genre fit, retaining the base model for comparison, and not relying solely on scaling up the model.

### The origin of S2 — “delve” is not clearly explained.

**Tom S. Juzek, Zina B. Ward. _Why Does ChatGPT “Delve” So Much? Exploring the Sources of Lexical Overrepresentation in Large Language Models._ COLING, 2025. **

[Paper PDF](https://aclanthology.org/2025.coling-main.426.pdf)

Read §§4–7, Abstract and Appendix B/D. The study identified over-occurring words in 21 scientific abstracts and compared candidate training corpora, Llama base/chat, and human preference experiments. Evidence related to post-training is indirect and mixed: the base/chat comparison incorporated both SFT and RLHF; the experiment with 201 Indian participants did not definitively confirm that preferred words caused reward bias. **Restrictions**: Conclusions should not state "RLHF leads to delve" or "English used by annotators from a certain country contributes to AI flavor." The project should record word frequency within genres to avoid creating permanent blacklists across languages and uses.

### S3 — Homogenization can come from model contributions, rather than from all language variations of the user.

**Vishakh Padmakumar, He He. _Does Writing with Language Models Reduce Content Diversity?_ ICLR, 2024; first preprint 2023. **

[ICLR Official Entry](https://proceedings.iclr.cc/paper_files/paper/2024/hash/02dec8877fb7c6aa9a79f81661baca7c-Abstract-Conference.html) · [I have read the full text.](https://arxiv.org/html/2309.05196v2)

I have read §§1–3, the results summary, and Appendix A. 38 native English speakers with writing/editing experience contributed 300 essays, comparing unassisted, GPT-3, and InstructGPT models; the model texts that received suggestions and those that were actually retained were recorded. The InstructGPT group showed greater similarity and lower content and lexical diversity among the essays, while GPT-3 did not show similarly significant results; the authors identified the main changes as affecting the model's contributions. **Limitations**: Old model, short essays, and a requirement of at least five suggestions per essay. Long-term results for all natural use cases cannot be derived; however, it supports separate testing of individual essay quality and overall content diversity.

### S4 — Cross-genre and decoding both change style metrics

**Sergio E. Zanotto, Segun Aroyehun. _Linguistic and Embedding-Based Profiling of Texts Generated by Humans and Large Language Models._ EMNLP, 2025. **

[Formal entry](https://aclanthology.org/2025.emnlp-main.1163/) · [Paper PDF](https://aclanthology.org/2025.emnlp-main.1163.pdf)

I have read the abstract, §3 Data, feature descriptions, conclusions, and §8 Limitations. Using RAID across eight English domains, 11 models, and four decoding configurations, I analyzed sentence length, dependency relations, lexical and semantic features, and style embeddings. Both humans and models exhibit domain-specific variations, but humans show greater variation in the measured features; newer models show more similar styles. **Limitations**: Model age is not randomly determined and results cannot be attributed to synthetic training data; the models used are not cutting-edge models from 2026; dependency features do not equate to user experience. Project benchmarks need to fix or record the decoding and perform cross-domain testing.

### S5 — More Recent Rewriting Research: Style Compression and Content Preservation Can Happen Simultaneously

**Zhivar Sourati, Farzan Karimi-Malekabadi, Meltem Ozcan, Colin McDaniel, Alireza Ziabari, Jackson Trager, Ala N Tak, Meng Chen, Fred Morstatter, Morteza Dehghani. _The shrinking landscape of linguistic diversity in the age of large language models._ Nature Human Behavior, 2026-08-24. **

[Official DOI](https://doi.org/10.1038/s41562-026-02550-0) · [Formal Abstract](https://pubmed.ncbi.nlm.nih.gov/42637911/) · [I have read the author's version.](https://arxiv.org/html/2502.11266v2)

The formal abstract verification involved three studies and seven datasets; author versions of Study 1a/1b and Study 2 were reviewed, along with limitations of the detection methods. Observing time series data and having the model refine existing text revealed variance compression in writing complexity. **Limitations:** Real-world AI identities are estimated by the detector; Granger predictions do not prove intervention causality; high embedding similarity is insufficient to prove that every fact and stance is preserved. Do not view its "semantic preservation" and S8's "semantic drift" as simply mutually exclusive: the tasks, metrics, and granularities of focus differ.

### S6 — Counter-evidence: The appearance of AI-preferred words does not indicate a decline in lexical diversity.

**Sarah Fitterer, Dominik Gangl, Jannes Ulbrich. _Testing English News Articles for Lexical Homogenization Due to Widespread Use of Large Language Models._ ACL Student Research Workshop, 2025. **

[Formal entry](https://aclanthology.org/2025.acl-srw.95/) · [Paper PDF](https://aclanthology.org/2025.acl-srw.95.pdf)

I have read the abstract, results discussion, and §4 Conclusion. Comparing 2018 and 2024 English online news: AI style word index increased, but MATTR and Maas changes were negligible; MTLD increased, and there was no support for a "decline in lexical diversity." **Limitations**: There are no logs of every real AI usage article; news topics, editing processes, and time all varied. It differs from the "complexity variance" measured by S5. The project cannot use a single lexical diversity score to summarize homogenization, nor can it be assumed that higher diversity is always better.

### S7 — Improved quality in individual articles does not contradict collective convergence.

**Anil R. Doshi, Oliver P. Hauser. _Generative AI enhances individual creativity but reduces the collective diversity of novel content._ Science Advances, 2024. **

[formal paper](https://doi.org/10.1126/sciadv.adn5290) · [Full text PDF of author's affiliation](https://discovery.ucl.ac.uk/10195027/1/Generative%20AI%20enhances%20individual%20creativity%20but%20reduces%20the%20collective%20diversity%20of%20novel%20content.pdf)

I have read the publisher's results (including story similarity) and discussion. The online experiment allowed writers to participate without assistance, or receive one to five AI story ideas; improvements in novelty, usability, and readability were observed in the blind reviews, with authors having lower initial creativity benefiting more, but the stories were more similar to each other. **Limitations**: Ordinary participants, micro-stories, limited idea interaction; not a professional marketing rewriting experiment. It refutes the notion that "AI-like content is necessarily of lower quality" and demonstrates that individual preferences cannot replace the diversity of voices from an entire group of brands/authors.

### S8 — Rewriting may change the position; the causal statements in this study should be narrowed.

**Marwa Abdulhai, Isadora White, Yanming Wan, Ibrahim Qureshi, Joel Leibo, Max Kleiman-Weiner, Natasha Jaques. _How LLMs Distort Our Written Language._ arXiv 2603.18161, 2026-03-18, preprint. **

[full text](https://arxiv.org/html/2603.18161v1)

I have read §3, §4.2–4.3, and the abstract and discussion. This includes a writing experiment with 100 participants and 86 ArgRewrite-v2 articles collected in 2021, comparing human and model revisions using three models and five types of editing instructions. It was found that even restricting grammatical editing can alter arguments. **Limitations:** Extensive use of randomly assigned behavior segmentation means that differences in this subgroup cannot be considered a randomization dose-response effect; embedding shifts also mix style and content; the real peer review portion relies on an AI detector. The project can reuse the paired revision approach, but must conduct separate topic-by-topic verification; acceptance cannot be based solely on embedding.

### S9 — A "complete" technical document must align the page with the reader's context.

**Karen de Souza, Alexandre Nikolaev, Maarit Koponen. _Generative AI for Technical Writing: Comparing Human and LLM Assessments of Generated Content._ NoDaLiDa/Baltic-HLT, 2025. **

[Paper PDF](https://aclanthology.org/2025.nodalida-1.67.pdf)

Read §§3, 4.3, and 5–7. The Nokia Network as Code document generated 72 RAG responses across 12 prompts, three models, and two temperature settings; compared to a professional technical writer's DQF-MQM, LLM judge, and BLEU/ROUGE. In one specific case, a human judge deemed the prerequisites on the side page unnecessary and awarded a correct answer; the LLM judge significantly lost points due to the missing condition. **Limitations:** One human evaluator, proprietary RAG implementation, older model. This study did not directly measure "AI flavor," but it demonstrates that technical document evaluators require error categories, reader tasks, and context; literal similarity/generalization "comprehensiveness" can be distorted.

### S10 — A counterexample closely related to marketing products: Real results and writing style preferences need to be tested separately.

**Jean-Pierre Dubé, Ariel Xu. _Large Language Models and Creative Content Design: a case study of email marketing at Wine Access._ Quantitative Marketing and Economics, 2026-01-13. **

[Full text of the publisher](https://link.springer.com/article/10.1007/s11129-025-09303-9)

I have read §3.1, §4, §5, and §6. Three rounds of real-world email RCTs: the first two rounds used Mistral7B, customized based on 3,148 historical emails; the third round used Prompting Claude. The comparisons included human, AI, and human-edited AI. Business decisions considered revenue and writing costs. **Limitations**: Single alcohol brand; short-term; training and prompting spanned multiple rounds with different models, not using equal-conditional ablation; insignificant differences in performance do not prove equivalence; net profit projection depends on the assumption of labor costs. This does not definitively declare prompting the winner, but it sufficiently demonstrates the necessity of a strong prompting baseline, and that the perceived "lack of AI" performance should be validated separately from conversion improvement.

### S11 — Chinese: More complex does not equal more natural or higher quality

**Longhui Zou, Ke Li, Joshua Lamerton, Mehdi Mirzapour. _GenAIese — A Comprehensive Comparison of GPT-4o and DeepSeek-V3 for English-to-Chinese Academic Translation._ PSLT, 2025. **

[Formal entry](https://aclanthology.org/2025.pslt-1.1/) · [Paper PDF](https://aclanthology.org/2025.pslt-1.1.pdf)

Abstracts, §2, and §6 have been read. 11 English language/culture/literature papers, 3,498 sentences translated into Chinese; DeepSeek-V3 achieved a high automatic QE score, while GPT-4o showed high lexical richness and syntactic complexity. **Limitations**: No human translations were provided for comparison, and naturalness assessments by native Chinese speakers are lacking; therefore, the AI-generated Chinese style or naturalness ranking cannot be defined based on this. It provides clues to Chinese-related features such as left nesting and noun modification distance, and cautions against directly transplanting English nominalization/participle clause scales.

### S12 — Source tags on Chinese social media platforms pose a risk of circular judgment.

**Yulong Ma, Xinsheng Zhang, Jinge Ren, Runzhou Wang, Minghu Wang, Yang Chen. _Linguistic features of AI mis/disinformation and the detection limits of LLMs._ Nature Communications; online 2025-12-11, volume 17/article 456 for 2026. **

[Full text of the publisher](https://www.nature.com/articles/s41467-025-67145-1)

Abstracts read, RQ1 discussion, data construction/annotation methods. The linguistic differences between long Chinese Toutiao articles and short MCFEND articles depend on content quality; the dependency distance direction observed in this paper cannot be directly applied to the English findings. **Key Limitations**: The Toutiao human/AI source is judged manually based on the rule "if there are suspected AI segments, then the entire article is AI-generated." Quality labels mainly come from two LLMs plus expert arbitration. Using this labeling to train AI will cause the judge to repeatedly write the reader's existing impressions into the ground truth; the controllable generation of evidence in short texts is clearer, but the task involves misinformation/false information and cannot be extrapolated to professional marketing and technical documents.

## Specific revisions to the original plan

1. **Retain pre-ChatGPT data, but use it as source evidence and style reference; do not automatically label it as "high-quality" or "low-AI-feeling."** Old marketing copy may contain clichés; old technical documents may no longer be applicable. Each entry must be independently labeled with quality, genre, language, audience, year, source, and usage license.
2. **Establish at least four cross-category units: Human Good, Human Poor, AI Good, AI Poor.** AI and human source labels are used for diagnostic purposes, not as style quality rewards. Include human-modified AI, AI-polished humanities, and "no-rewrite" samples of excellent input to avoid equating modification rate with success.
3. **Using the same factual material for further writing/rewriting.** Relying solely on a "similar prompt" often overlooks the product facts, experiences, and target audience the original author possessed, resulting in a vague model—a problem with the input. The source packet, writing brief, original manuscript, editorial constraints, and revised manuscript should be retained, clearly indicating who introduced the missing facts.
4. **First, human evaluation is used to calibrate the judge, then the judge is trained.** Human evaluation does not necessarily require complete consensus on an "AI-flavored 1-5 score"; domain editors can label issues segment by segment, provide paired preferences and reasons, and report disagreements. Automated judging can only be used iteratively after validation on an independently reserved set of human evaluations.
5. **Set task completion and loyalty as thresholds, then optimize the message.** Technical documentation should be checked for feasibility in terms of terminology, parameters, constraints, and steps; marketing should examine whether promises and product facts are exaggerated, and whether the CTA matches the audience. Neither should rely on fabricated details to add a "human touch."
6. **Test at the article level and corpus level separately.** Individual articles can be read better, but entire batches of articles become monotonous. Tests are allocated by author/brand, measuring the changes in different samples of the same input, and also measuring the degree to which different inputs are modified into the same structure.
7. **Training methods require careful control of conditions.** The original model, general rule prompting, genre-specific exemplar prompting, step-by-step harnessing with semantic checks, and SFT/preference optimization should all use the same input and held-out human evaluation. Additional sampling, judge calls, and human time must be factored into the cost. First, identify the error group that consistently fails during prompting before deciding what to train.

### The first version of the genre-based human assessment task

| Task | Prior content to be preserved | Main style issues | Suitable human evaluators and external outcomes |
|---|---|---|---|
| API/Operation Documentation | Parameters, Return Values, Errors, Conditions, Codes, Cross-Page Context | Unnecessary Introductions, Repetitive Presuppositions, Vague Benefits, Terminology Drift | Technical Writers and Real Users; Success Rate and Time to Find Information or Complete Operations |
| Product Marketing Article | Confirmed Features, Target Audience, Positioning, Pricing, and Promise Boundaries | Abstract Praise, Synonym Piling, Unfounded Concretization, and Disappearing Brand Voice | Edited by an industry and brand expert; Further testing on clicks, conversions, and trust will follow. |
| Short Ads/Headlines | Real Differentiation, Specific Selling Points, Length and Channel Limitations | High-Density Adjectives, Universal Slogans, Targetless CTAs | A Copywriter Familiar with Channels; Ultimately, Through Randomized Business Experimentation |
| Personal opinions/professional viewpoints | Author's original stance, level of conviction, arguments, examples | Automatic neutralization, false balance, unsubstantiated exaggeration, disappearance of voice | Author's own comments plus blind review and editing; measuring fidelity and quality of expression separately |

The table above shows the experimental design proposed in this project, not the unified rubric that has been verified in the twelve papers.

## Conclusions correspond to evidence

| Possible conclusions | Main basis | Statements that should not cross boundaries |
|---|---|---|
| Some models exhibit systematic genre and grammatical bias | S1, S4 | All models, languages, and genres are the same |
| Post-training is likely involved in style narrowing | S1, S2, S3 | It has been confirmed that a specific RLHF algorithm or labeled region is the root cause |
| Larger models are not a sufficient condition for style improvement | S1 | Any task only requires small models |
| Individual article quality and batch diversity can be separated | S3, S5, S6, S7 | AI text is always either poorly written or has a limited vocabulary |
| Rewrite fidelity needs separate verification | Limitations of S8 and S5 metrics | High embedding similarity proves the absence of semantic drift |
Technical documentation must be evaluated in context. | S9 | The more comprehensive and longer, the better; or shorter articles are always better.
| Marketing style and business performance must be measured separately | S10 | Removing AI-centric approaches will inevitably improve conversion rates; certain training methods are guaranteed to succeed |
| Chinese needs its own calibration set and features | S11, S12 | Use English AI high-frequency words/syntactic tables to directly score Chinese |

Incomplete evidence work: A unified "AI-like" benchmark covering Chinese and English, technical documents and marketing, and validated by human annotations across multiple domains has not yet been found; there are also no training or reproduction experiments in this round, so the actual gain of the post-training relative strongest prompt cannot be given. Existing research fully supports the project to conduct measurement and controlled comparisons, and does not yet support betting on a certain algorithm, model size, or single reward.

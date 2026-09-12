# Literature review: reducing AI-sounding writing

The relevant literature spans several problems: describing model-specific language, understanding writing homogenization, editing while preserving meaning, assessing writing quality, and rewriting to evade provenance detectors. They share techniques but measure different outcomes. This review organizes the closest existing work around what it establishes for a bilingual technical-documentation and marketing rewriter.

This is a targeted review as of 2026-09-12, not an exhaustive systematic review. Paper findings are distinguished from implications for Plainvoice. Detailed study settings, reading coverage, counterevidence, and references are in the four linked research memos.

## What makes model writing recognizable?

**Reinhart et al., 2025 — [Do LLMs write like humans? Variation in grammatical and rhetorical styles](https://arxiv.org/html/2410.16107v2), PNAS.** Compares parallel English human/model continuations across genres using lexical, grammatical, and rhetorical features. Instruction-tuned variants show stronger stylistic departures than base variants; scaling size does not automatically remove them. This is evidence for systematic genre mismatch beyond a handful of conspicuous words. The comparison cannot isolate SFT from preference optimization or other post-training changes.

**Juzek & Ward, 2025 — [Why Does ChatGPT “Delve” So Much?](https://aclanthology.org/2025.coling-main.426/), COLING.** Studies lexical overrepresentation in scientific abstracts and investigates possible causes. The evidence does not establish a single mechanism explaining the words. For this project, word frequency is a diagnostic feature whose meaning depends on genre; it is not a validated global blacklist or reward.

**Padmakumar & He, 2024 — [Does Writing with Language Models Reduce Content Diversity?](https://arxiv.org/html/2309.05196v2), ICLR.** A writing study finds that InstructGPT-assisted essays are more homogeneous, with much of the effect associated with retained model contributions. Its English essay task and older models limit transfer. It motivates evaluating a collection of rewritten texts, alongside the quality of each individual text.

**Fitterer et al., 2025 — [Testing English News Articles for Lexical Homogenization Due to Widespread Use of Large Language Models](https://aclanthology.org/2025.acl-srw.95/), ACL SRW.** Finds increased AI-associated vocabulary without evidence of reduced lexical diversity in its historical news comparison. This is useful counterevidence to a broad claim that all AI influence reduces every form of diversity. Time, genre, lexical diversity, syntactic variation, and semantic similarity must be distinguished.

The strongest defensible synthesis is that some models have systematic linguistic preferences and limited adaptation to genre. There is no established equivalence between those preferences, poor writing, and actual AI authorship. The Chinese observation about gratuitous “不是……而是……” remains a product hypothesis in this review; direct evidence specific to that construction was not located.

## What existing work actually trains or improves a rewriter?

Directly named humanization work also exists: DIPPER trains a controllable paraphraser; HUMPA uses detector-derived preference tuning and proxy decoding; CoPA uses training-free contrastive paraphrasing. The community Unslopper model uses repeated AI rewrites of historical human literature to create reverse-distillation pairs. See the [direct prior-art addendum](09-12-humanization-prior-art.md) for original sources, methods, quality results, and evidence levels. These are important comparators; detector evasion is not evidence of comprehensive editorial improvement.

**Raheja et al., 2023 — [CoEdIT: Text Editing by Task-Specific Instruction Tuning](https://aclanthology.org/2023.findings-emnlp.350/), Findings of EMNLP.** Trains on editing instructions paired with revised text. This is a close task formulation for an instruction-following rewriter. Its strongest evidence concerns relatively short edits and historical comparison models; it does not establish a current bilingual long-document naturalness result.

**Du et al., 2022 — [Understanding Iterative Revision from Human-Written Text](https://aclanthology.org/2022.acl-long.250/), ACL; Kim et al., 2022 — [Improving Iterative Text Revision by Learning Where to Edit from Other Revision Tasks](https://aclanthology.org/2022.emnlp-main.678/), EMNLP.** IteraTeR and DElIteraTeR treat revision as edits with intentions and locations. They offer more useful supervision structure than labeling a whole document “AI-like.” The source domains and historical models differ from this project; adopting edit intentions does not prove their original architectures are the best current implementation.

**Madaan et al., 2023 — [Self-Refine: Iterative Refinement with Self-Feedback](https://arxiv.org/abs/2303.17651).** Uses the same model to generate, critique, and revise without changing weights. It establishes an inference-time improvement approach that belongs in a serious comparison. Its multi-task findings do not imply that every additional revision improves factuality or style; calls and error accumulation must be measured.

**Wu et al., 2025 — [WritingBench: A Comprehensive Benchmark for Generative Writing](https://arxiv.org/html/2503.05244v4).** Combines diverse Chinese/English writing tasks, query-specific criteria, a critic, and critic-filtered SFT data. It is especially relevant to the proposed evaluator-to-training pipeline. Its improved writing-model scores do not directly measure reduced AI-ness, and the shared evaluation/data-curation framework makes independent human validation important.

These papers support editing-specific SFT and strong inference-time baselines. Generic LoRA/QLoRA and DPO papers explain how to implement efficient adaptation or preference learning; they do not themselves establish success at removing AI-sounding style. The [training memo](09-12-training-literature.md) separates these implementation methods from task evidence.

## How should improved writing be evaluated?

**Mir et al., 2019 — [Evaluating Style Transfer for Text](https://aclanthology.org/N19-1049/), NAACL.** Separates style-change strength, content preservation, and naturalness. It supplies a useful evaluation foundation: moving further toward a target style can trade off against preserving content. The original sentiment-transfer setting is much more narrowly defined than “AI flavor.”

**Liang et al., 2023 — [GPT detectors are biased against non-native English writers](https://pmc.ncbi.nlm.nih.gov/articles/PMC10382961/), Patterns.** Shows substantial false positives on its non-native English samples using historical detectors. This is a warning against treating low detector scores as quality or naturalness labels. Its numerical error rates should not be presented as estimates for current detectors or Chinese writing.

**Min et al., 2023 — [FActScore: Fine-grained Atomic Evaluation of Factual Precision in Long Form Text Generation](https://aclanthology.org/2023.emnlp-main.741/), EMNLP.** Provides atomic-fact precision assessment. A rewriting benchmark must also measure whether required original information survives: precision alone can reward saying less. Preserving an input claim and verifying that claim against the world are separate tasks.

**Abdulhai et al., 2026 — [How LLMs Distort Our Written Language](https://arxiv.org/html/2603.18161v1), preprint.** Examines human writing and model revisions, finding that even constrained editing can change arguments. It motivates explicit stance and claim checks. Embedding shifts do not isolate every semantic change, and behavior-defined heavy-user groups should not be interpreted as randomized dose effects.

The practical inference is to evaluate naturalness, utility, and preservation separately, using calibrated human judgment. This is a proposed synthesis, not a universal validated metric. The [evaluation memo](09-12-evaluation-literature.md) also covers MT-Bench, G-Eval, length bias, RAID, M4, LLMBar, and reward overoptimization.

## What changes in technical documentation and marketing?

**de Souza et al., 2025 — [Generative AI for Technical Writing: Comparing Human and LLM Assessments of Generated Content](https://aclanthology.org/2025.nodalida-1.67/), NoDaLiDa/Baltic-HLT.** Compares human and model judgments of generated technical content. Context-dependent completeness can produce disagreement: repeating prerequisites may be unnecessary on a page where readers already have them. Its small evaluation and single technical writer limit generalization, but it directly challenges a generic reward for maximal detail.

**Bhat et al., 2025 — [Creativity Benchmark: A benchmark for marketing creativity for LLM models](https://arxiv.org/html/2509.09702v1), preprint.** Uses practicing creatives to compare brand-constrained ideas. Model-judge rankings do not reliably reproduce those human preferences. It concerns brief creative concepts, not all marketing copy or conversion outcomes; nevertheless, it shows why a general chat judge needs domain validation.

**Dubé & Xu, 2026 — [Large Language Models and Creative Content Design: a case study of email marketing at Wine Access](https://link.springer.com/article/10.1007/s11129-025-09303-9), Quantitative Marketing and Economics.** Studies real email marketing experiments, including a customized small model in early rounds and prompted Claude in a later round. The methods were used in different rounds with different models, so this is not a controlled fine-tuning-versus-prompting ablation. It provides a concrete reason to measure writing costs and business outcomes separately from stylistic preference.

Chinese-specific evidence remains thinner for the exact target task. Translation complexity and Chinese misinformation-detection studies are adjacent sources, but their labels and tasks cannot substitute for native Chinese technical and marketing judgments. Their limitations are detailed in the [style memo](09-12-style-literature.md).

## What remains open?

The selected literature does not establish an off-the-shelf gold standard for “AI flavor” across Chinese/English and technical/marketing writing. It also does not establish a winning model size or demonstrate that a particular preference objective beats a well-tuned, equally informed inference-time workflow across those four settings.

A defensible contribution would be a validated domain-aware editing benchmark and evidence that a particular training method improves human-rated writing while preserving facts and author intent at a useful cost. Merely lowering provenance-detector scores would establish a different result.

For a short reading sequence: start with Reinhart for the phenomenon, CoEdIT for the task, WritingBench for the evaluator/training loop, Creativity Benchmark for its limits, and Wine Access for an actual business setting. Read the [paraphrasing/humanization addendum](09-12-humanization-prior-art.md) before making any novelty claim about existing rewriting methods.

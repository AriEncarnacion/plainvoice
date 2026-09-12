# Direct humanization and paraphrasing prior art

This addendum covers a gap in the first literature pass: work that explicitly trains or steers models to make machine-generated writing appear more human. These are close methodological comparators, although their main objective is often detector evasion. Evaluation as of 2026-09-12; no method was reproduced here.

## DIPPER

**Kalpesh Krishna, Yixiao Song, Marzena Karpinska, John Wieting, Mohit Iyyer. _Paraphrasing evades detectors of AI-generated text, but retrieval is an effective defense._ NeurIPS 2023.** [Author full text](https://arxiv.org/html/2303.13408v2) · [Official proceedings](https://proceedings.neurips.cc/paper_files/paper/2023/hash/575c450013d0e99e4b0ecf82bd1afaa4-Abstract-Conference.html)

An 11B T5 paraphraser trained using aligned alternative English literary translations in PAR3. It can use surrounding context and control lexical changes and content reordering. The paper tests detection robustness and also checks semantic preservation, including a small human study.

**Relevance:** a concrete, existing controllable paragraph rewriter and a useful historical baseline. **Limit:** its evidence does not establish improved information value, brand voice, or Chinese technical-document quality. Detector evasion and semantic similarity do not jointly imply that an editor prefers the revision. Read method, quality evaluation, detection experiments, and limitations; no independent replication.

## HUMPA

**Tianchun Wang et al. _Humanizing the Machine: Proxy Attacks to Mislead LLM Detectors._ ICLR 2025; preprint first published 2024-10-25.** [Full text, v2](https://arxiv.org/html/2410.19230v2) · [Official proceedings](https://proceedings.iclr.cc/paper_files/paper/2025/hash/ab1ee157f7804a13f980414b644a9460-Abstract-Conference.html)

Uses detector-derived preferences to train a small model through DPO and LoRA, then uses that model to adjust a larger model during decoding. It is generation-time control, not an already-validated arbitrary-document editing system. OpenWebText, WritingPrompts, and PubMedQA feature in its experiments.

The main results measure detector robustness. Appendix H also reports a small randomized-order human fluency comparison, favorable to HUMPA. That is relevant evidence, but it does not establish preservation of detailed product promises, technical conditions, author stance, or comprehensive editorial quality across languages.

**Relevance:** direct precedent for small-model preference training to affect perceived machine style. **Limit:** inheriting detector-derived preferences would inherit a different objective from the proposed human editorial rubric. The abstract's broad RL wording should not be described as PPO: the implementation uses DPO. Read training, experiments, utility measures, and Appendix H.

## CoPA

**_Your Language Model Can Secretly Write Like Humans: Contrastive Paraphrase Attacks on LLM-Generated Text Detectors._ EMNLP 2025; preprint first published 2025-05-21.** [Official entry with authors](https://aclanthology.org/2025.emnlp-main.433/) · [Full paper](https://aclanthology.org/2025.emnlp-main.433.pdf)

A training-free paraphrasing method using contrastive decoding under human-like and machine-like instructions. The experiments include XSum, SQuAD, LongQA, detection metrics, and fluency/consistency assessments. It belongs in the method comparison when token-level model access is available; ordinary hosted text APIs may not expose the required decoding controls.

Appendix H, Table 11 is particularly informative. On XSum, human natural-fluency scores are **4.74 for CoPA, 4.25 for DIPPER, and 4.94 for the original machine text**. The table also reports lower CoPA fluency than original machine text on the other two datasets. This supports a narrower claim than “humanization improves writing”: it can preserve quality better than an earlier paraphraser while still reducing fluency relative to the input. These are reported point estimates, not a new significance analysis.

**Relevance:** a direct no-training comparator and concrete evidence that detector metrics and editorial properties can diverge. **Limit:** English benchmark fluency is not a complete measure of naturalness or domain utility. Read method, datasets, and Appendix H.

## Unslopper: a close community implementation, with weaker evidence

**N8Programs. _Unslopper-30B-A3B: Humanizing AI-Generated Text via Reverse Distillation._** [Author model card](https://huggingface.co/N8Programs/Unslopper-30B-A3B-bf16). Community release, not a peer-reviewed paper. The card's citation says 2025; the exact original release date was not independently established.

This closely resembles the proposed data idea: take 1,000 Gutenberg-derived literary passages, rewrite each ten times with GPT-4o-mini, and train a Qwen-based LoRA to recover the original from the final rewritten version.

The author reports that Pangram-derived “humanness” improves, while an Opus 4.5 automated weakest-dimension quality score drops from **8.60 to 7.96** on 100 generated stories. A same-base-model rewriting control is also reported. These are author-reported, model/detector-based evaluations, not independent human evidence.

**Relevance:** reverse-corruption training is existing prior art, not a novel idea by itself. **Limit:** literary-domain training, possible semantic drift, synthetic repeated-rewrite artifacts, and no demonstrated bilingual technical/marketing improvement. Read training pipeline, evaluation definition, result table, and limitations. Do not treat “30B-A3B” as a dense 3B model.

## Consequences for the research claim

There is already direct work on humanizers, detector-guided preference training, controllable paraphrasing, and training-free contrastive methods. A novelty claim needs to acknowledge it.

The research opportunity proposed here is narrower: demonstrate improvements that bilingual domain editors actually value, with facts and author intent preserved, on independent technical and marketing tasks. The current sources do not establish that result. Some direct prior art should be evaluated as comparators, but its evaluation metric should not automatically become the project's training target.

DIPPER and CoPA can be treated as rewriting-method comparators where technically feasible. HUMPA requires a generation-control adaptation and is not a drop-in rewrite arm. A reverse-corruption LoRA baseline inspired by Unslopper would test whether a relatively simple existing data recipe already captures the benefit; it would need independent editorial evaluation and a held-out source family.

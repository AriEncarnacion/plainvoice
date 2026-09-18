# Research coverage and verification records

This round is a targeted background study, not a PRISMA-style systematic review. Search results are up to September 12, 2026; the first round only involves the study itself, with subsequent desktop data downloads and generation of six short fragment candidates to user authorization. Independent peer review, model training, and real-world benchmarking have not yet been performed. The goal is to cover four equal priority units: Chinese/English bilingual and technology/marketing; the six sources in this round are exploratory sampling, not a four-dimensional balanced benchmark.

## Scope of evidence

The four literature memos collectively list 40 research papers/datasets, along with 5 official model cards and supporting publications. The focus includes linguistic style and homogenization, AI source detection and bias, editing and style transfer, human/LLM evaluation, efficient parameter training, preference optimization, and industry writing experiments.

On the same day, a follow-up was added, providing a literature-first introduction and supplementing the weakly covered direct humanization prior art from the first round: three papers from DIPPER, HUMPA, and CoPA, as well as a separate evidence-level community Unslopper model card. The human rating scale for CoPA and the quality scale for Unslopper have been reviewed, clarifying the different conclusions relative to the original manuscript and the relatively weak baseline; however, no claim has been made to reproduce the effect based on this.

The original sources are primarily ACL Anthology, arXiv author versions, PNAS, Nature, Science Advances, ICML/ICLR, and the publisher's own articles. Model configurations are from the model cards and official release instructions from the publisher's organization. Commercial promotions, social media posts, and secondary interpretations found in the search are not considered evidence for the conclusions drawn.

Each memo records the reading scope and limitations; for some datasets, only the official abstract and metadata were verified, and no complete reproduction was falsely claimed. All literature scores belong to the model, task, and population specified in the paper, and not to Plainvoice. Some 2026 studies are still in preprint, or the reading scope differs between the official version and the author's version, which has been noted.

## Search direction

- AI writing style / AI-ese / grammatical and rhetorical variation / lexical overrepresentation / homogenization.
- Human and LLM judge bias / non-native detection bias / RAID / M4 / style transfer evaluation / factual preservation.
- Text editing instruction tuning / CoEdIT / IteraTeR / Chinese revision and simplification.
- WritingBench/marketing creativity/copywriting/technical writing evaluation/real marketing experiments.
- LoRA / QLoRA / DPO / online preference coverage / reward overoptimization / current official model cards.

## Important corrections

1. Syntactic density and insufficient effective information can coexist and are not contradictory.
2. Historically sourced manually does not automatically equate to high quality; AI-based source identification cannot be used as a quality label.
3. The base/instruction control failed to isolate SFT, RLHF, or other specific post-training factors, and therefore cannot be used for univariate causal attribution.
4. The Chinese phrase “不是，而是” was not found to have sufficient direct empirical evidence in this round, and is therefore retained as a product hypothesis to be verified.
5. The custom mini-model of Wine Access and the prompted Claude were in different experimental rounds and cannot be regarded as controlled ablation of training and prompting.
6. FActScore precision does not cover necessary recall information; embedding similarity is also insufficient to prove position-free drift.
7. The model card provides existence, structure, and licensing information, but cannot prove that the recommended size is optimal for the task; Qwen's LM parameter is not the total storage of a complete multimodal checkpoint.
8. The memory table distinguishes between the theoretical lower bound of weights and actual equipment planning; the price example is a sensitivity analysis assuming no purchase quotation or expenditure already incurred.
9. The scales, learning curves, and ARM numbers for each memorandum are research options; the unified implementation version is in the main scheme and annotation protocol, and the entry point is already marked.

## Independent method review

A separate review of the main solution was conducted, and three rules were identified and supplemented:

- For cases where both parties fail, cannot make a judgment, have no evaluation, have empty output, or have no majority in the review and are disputed in fact, retain all task denominators; use upper and lower bounds for pending tags, and do not delete them.
- The non-inferiority limit and the upper limit of major errors for each cell must be determined before the final test; the absence of significant degradation cannot be interpreted as proof of non-inferiority.
- Consistency statistics use only the independent original scores prior to the ruling and must not include rulings that only evaluate disagreements.

The annotation estimate of 800 items × 3 people × 3–5 minutes = 120–200 hours was reviewed; it was confirmed that n=200/division is insufficient to support a very narrow effect or low error rate commitment. Cost and sample size still require pilot calibration.

## Results not yet established

Actual follow-up data collection: Six sets of publicly available data, totaling 105 files/610,783,737 bytes; structure, parallel line count, ZIP CRC, and manifest SHA-256 verification passed. MCTS license updated from "not read in full" to "GPLv3 LICENSE obtained," but usage rights are still not extended to upstream news. Six official original documents and six sets of independent context subagent rewrites are saved on the desktop; output mappings and a few technical identifiers have been verified, and all comment tags are empty. Failed CLI calls and actual subagent generation are archived separately. HTML local references and six source frames passed checks; no claims were made regarding passing human review or full browser interaction tests.

Ground truth follow-up: Author entry points for AdParaphrase v2.0, IteraTeR, arXivEdits, MCTS, ASSET, and CoEdIT were verified, and independent data collection schemes were added. Distinctions were made between ad interpretations/preferences and AI-generated tags, human editing and automatic tagging, and the scale of paper usage versus the actual public release. Full data licensing for MCTS was not verified in this round; CoEdIT's 82K corpus represents the paper size, with approximately 69K publicly available for training. The entire corpus was not downloaded, and the proposed 80 data collection schemes were not counted as collected gold.

The data collection plan was independently verified: the arithmetic of 80 items, 20 in each of the four grids, and 160 pair reviews by two people was valid; it was clarified that the addition of DPO chosen must be subject to constraints, and ties, both drafts being unqualified, and uncertainties not being directly converted into ordinary DPO win/loss labels.

There is no credible evidence to declare a model or training method superior across four scenarios, nor is there a calibrated, uniform "AI-like" score. No permission has been obtained for bulk training of historical marketing copy, no company data has been collected, and no training weights have been downloaded or paid computation initiated. The current repository serves as a viable starting point for continued research.

Markdown internal links, file lists, and Git commit differences are checked before pushing. Only original research documents and templates from this project are added to the personal repository and are not included in the parent management workspace.

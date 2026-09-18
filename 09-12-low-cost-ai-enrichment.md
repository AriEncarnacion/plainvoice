# Plainvoice: Bilingual AI Candidate Completion and Model Comparison

2026-09-12 Methodology and Delivery Record. This experiment supplements existing English and Chinese sources with AI-generated comparison drafts, retaining the sources, semantic extraction, writing process, and failure records for subsequent review and method comparison. **All generated drafts are candidates awaiting evaluation and do not yet constitute validated gold data or model training results.**

The study log is divided into early pilot diagnostics, Gemini 2.5 Flash-Lite baseline runs, and full article comparisons with Gemini 3.1 Flash-Lite. Additional model comparisons cover six full articles; multiple model outputs from the same source are retained separately and not counted as new independent sources. Early pilot diagnostic versions are displayed in groups with the main batch; restored or supplementary runs also retain their respective models, pilot versions, result statuses, and ledgers.

Actual quantities are counted separately for complete articles, documents or sentence/segment units, model comparisons, and early diagnoses; target numbers, available candidate numbers, number of entries, source coverage after deduplication, and number of manually accepted entries use different metrics:

| Current caliber | Quantity |
|---|---:|
| Target Sources in Chinese and English | 930 |
| Independent sources for the new AI are now available | 839 |
| Gemini 2.5 Full Article Candidate | 29 |
| Gemini 2.5 Sentence/Technical Fragment Candidates | 808 |
| Gemini 3.1 Full-Text Model Comparison | 6 |
| Early pilot diagnostic draft | 5 |
| Added viewer record | 848 |
| Target sources not yet covered | 91 |
| Gold inspected independently by human inspectors | 0 |

New records added: 352 Chinese entries and 496 English entries. The Viewer now has **1,247,891 entries in 28 groups**. These are bounded sample completions; AI was not generated for all 1.25 million original entries. See details. [Machine-readable delivery summary](qa/09-12-enrichment-summary.json).

Of the 91 uncovered targets, 15 have records of failures, rejections, or exceptions; another 76 have not yet been invoked after the browser session was reset. The dedicated credentials are only stored in memory and cannot be recovered after a reset; these 76 targets did not incur invocation costs, and the list to be generated is retained locally. This round delivers based on the existing 848 candidates, and the generation process has been stopped for all of them.

Both English and Chinese are included in this round, while Japanese candidates are not. "Complete article" refers only to the downloaded full text or cleaned full text retained from the selected sources. Document revision units may be abstracts, chapters, or collected revised text; sentences, human-referenced rewrites, and function document fragments will remain in their respective types and cannot be accumulated into the "full-text article count." The limited source scope does not guarantee a balanced or representative number of articles across languages and types.

The target for completion is determined based on the original role and the selected text. The existence of human before-and-after versions or multiple reference answers does not necessarily mean there is an AI comparison; the source side for this rewrite must be explicitly selected. Agent traces containing only AI output, machine pseudo-targets, isolated records without alignment, and obviously mismatched code and documentation will not be included in the source queue for missing AI comparisons in this round. Articles with existing comparisons will retain the "comparison" tag when participating in additional model comparisons.

Source tags use existing evidence of origin and retain the uncertainty of author identity. Community content, some editorial data, and a few existing articles cannot be individually proven to have been written entirely by humans independently.`human`,`reference` Input/target tags do not automatically validate quality. Original role, selected side, license, data split, content hash, and these limitations are retained.

Each source is, in principle, called twice in a context-isolated manner. The first reading reads the selected full text or complete source unit, extracting the subject, predicate, object (SVO), and necessary constraints: subject and object, negation scope, condition, numerical value, technical behavior, uncertainty, and viewpoint attribution. The source paragraph number is only used for audit extraction; each unit must correspond to a proposition, exclusion reason, or unresolved status. The complete article will not be broken down into unrelated paragraph-by-paragraph rewriting tasks.

After extraction, the script shuffles the propositions according to the recorded seeds, removes source locators and original text structural clues, and forms a content package. The second call only receives this package and the writing requirements, allowing the user to choose a title, structure, and wording, write an independent body text in the same language, and submit coverage evidence and unresolved items for each proposition. The writing call does not accept the original body text or the chat history of the extraction call; both calls can use the same model, and context isolation does not equate to independent quality verification.

The machine checks and verifies the JSON structure, source units and proposition IDs, the presence of evidence in the text, and the completeness of the output. Pilot and independent agent spot checks have identified semantic omissions, negations or polarity changes, and shifts in opinion attribution; these issues may still occur even when coverage self-reports as passed. Information missed during the extraction phase may also disappear in the subsequent text and coverage table. Therefore, complete coverage does not prove full-text authenticity, and independent agent spot checks cannot replace human verification.

Defect markers only apply to specific manuscripts that have been verified and are bound to the model, source hash, and output text hash. Other model outputs or subsequent versions from the same source need to be checked separately. The defect conclusion cannot be automatically inherited, nor can it be considered as passed simply because it was not selected.

Some complete articles may still lack available AI comparisons. Failure records include: the requested structure schema complexity or format is unacceptable to the model/router; generation reaches the output limit, resulting in truncation or failure to complete properly; transmission anomalies prevent reliable confirmation of server completion or billing; and the model rejects or filters responses. Responses that fail structure or integrity checks are not considered acceptable final drafts, and requests with unclear results are reserved. `unknown` Status, without automatically retries to cover up missing items. Specific sources and reasons for the lack of coverage are retained in the delivery summary.

Costs are aggregated across all running ledgers, including early pilots, baselines, model comparisons, and related failed requests. Settled costs, conservative reserves for unresolved calls, and total cost exposure are listed separately.

The user authorization is capped at $20. Total recorded costs for all runs in this round amount to **$1.08076450**; an additional **$0.16447055** is a budget reserved for uncertain outcomes and cannot be considered a confirmed expense. The total conservative exposure is **$1.24523505**, less than the purchased $10 credit limit.

| Model | Input / Million tokens | Output / Million tokens |
|---|---:|---:|
| [Gemini 2.5 Flash-Lite](https://openrouter.ai/google/gemini-2.5-flash-lite) | $0.10 | $0.40 |
| [Gemini 3.1 Flash-Lite](https://openrouter.ai/google/gemini-3.1-flash-lite) | $0.25 | $1.50 |

The above are the text prices verified in this round; six articles (3.1) cost $0.159308 each. All costs, unsettled reserves, and request statuses for each operation are included in the delivery summary.

Before each payment request, the client persists a conservative reserve of input and maximum output; settlement is only made after reliable usage is obtained.`unknown` The request continues to hold the reserved quota and stops new scheduling; it does not automatically release or reissue the quota. The recovery process only reuses saved responses that can be verified as accepted and settled, and checks the original queue, prompts, and budget configuration; it cannot create a new ledger to bypass unknown calls. Budget caps are executed on a per-ledger basis; before continuing with untried sources, all previously spent and unknown reserves are aggregated separately before allocating quotas to new runs. Budget caps for each round are recorded separately from actual expenditures; model prices are based on runtime verification of identifiers, routes, and ledgers.

Reproduce the use of deterministic queues and versioning hints:`plainvoice_prepare_enrichment.py` Read-only source database and generate source list;`run_ai_enrichment.py` Execute the Gemini 2.5 baseline;`run_ai_enrichment_multi.py` Perform a limited-scope model comparison. Run metadata storage queues and include hint hashes, model identifiers, random seeds, source text hashes, extraction results, out-of-order packages, final drafts, overlay evidence, anomalies, and expense ledgers. Evidence is transferred only locally into process memory and is not written to public documents or research artifacts.

After all generation processes stop,`finalize_ai_enrichment.py` Retain the original generated files, attach QA statements with clearly defined scopes to the corresponding manuscripts, and summarize the results and costs of each round. Then, [the process will be handled by...]. `plainvoice_ingest_enrichment.py` Importing to the local review library: Skips entries with the same ID and content; reports an error and rolls back entries with the same ID but different content; retains existing records, content hashes, and reviews. Articles, data units, model comparisons, and early diagnoses are displayed separately; importing indicates the item is ready for review, but does not guarantee quality approval.

Before entering SFT or DPO, the entire "original text → content card → new text" chain must be independently verified by humans to assess information retention, expression quality, and practical use, and to confirm data usage rights and source group boundaries. DPO preference labels need to be judged on a case-by-case basis and cannot presuppose that a particular model, AI manuscript, or source manuscript will win. The current output can be used for review, diagnosis, and design of subsequent experiments, but it cannot be used to claim that the training is effective or that a reliable model ranking has been obtained.

Publicly available materials include methodologies, aggregated statistics, and licensed examples. Third-party full texts, unauthorized complete comparative versions, and original traces are kept for local review; this statement does not contain private accounts, credentials, or native identity information.

## Review portal

Open [Full viewer on this machine](http://127.0.0.1:8876)This will automatically take you to a new article group. You can toggle it directly via the "New AI Rewrites Added This Round" option at the top left.[Full article](http://127.0.0.1:8876/?collection=ai-enrichment-articles),[Six Gemini 3.1 comparisons](http://127.0.0.1:8876/?collection=ai-enrichment-comparison),[Sentences and technical segments](http://127.0.0.1:8876/?collection=ai-enrichment-units)A represents the selected original text, and B represents the corresponding AI draft. The original text, generated draft, extracted content cards, writing packages, coverage tables, and cost information are all viewable. The desktop files are located at... `ai-enrichment/` The general ledger is `delivery-summary.json` Each round `pairs.jsonl` Input for a viewer that already has a QA document attached;`pairs.generated.jsonl` or `pilot-pairs.jsonl` Retain the original generation record.

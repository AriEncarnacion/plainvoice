# Plainvoice: bilingual AI candidate enrichment and model comparison

2026-09-12 method and delivery record. This experiment adds AI comparison drafts to existing English and Chinese sources, keeping the source, the semantic extraction, the writing process, and the failure records for later review and method comparison. **Every generated draft is a candidate awaiting human evaluation; none of them yet constitutes verified gold data or a model training result.**

The research record divides into early pilot diagnostics, the Gemini 2.5 Flash-Lite baseline run, and the full-article comparison on Gemini 3.1 Flash-Lite. The additional model comparison covers six full articles; several model outputs from the same source are kept separately and are not counted as new independent sources. Diagnostic drafts from early prompt versions are shown as a collection separate from the main batch, and recovery or supplementary runs likewise keep their own model, prompt version, result status, and ledger.

Actual counts are tallied separately for full articles, document or sentence/segment units, model comparisons, and early diagnostics; the target count, the usable candidate count, the ingested count, the deduplicated source-coverage count, and the human-acceptance count use different definitions:

| Definition used this round | Count |
|---|---:|
| Chinese and English target sources | 930 |
| Independent sources that already have a new AI version | 839 |
| Gemini 2.5 full-article candidates | 29 |
| Gemini 2.5 sentence-segment / technical-fragment candidates | 808 |
| Gemini 3.1 full-text model comparisons | 6 |
| Early pilot diagnostic drafts | 5 |
| New viewer records added | 848 |
| Target sources not yet covered | 91 |
| gold accepted by independent human review | 0 |

Languages of the new records: 352 Chinese and 496 English. The viewer now holds **1,247,891 records in 28 collections**. These are bounded sample enrichments; AI was not generated for all 1.25 million existing records. See the [machine-readable delivery summary](qa/09-12-enrichment-summary.json) for details.

Of the 91 uncovered targets, 15 have a failure, refusal, or exception record; the other 76 had no call issued after the browser session was reset. The dedicated credential is held in memory only and cannot be recovered after a reset; these 76 incurred no call cost, and the to-be-generated list is kept locally. This round delivers the 848 candidates that exist, and all generation processes have been stopped.

English and Chinese are both in scope this round; Japanese candidates are not. "Full article" means only the downloaded body text or cleaned full text that is retained in full from the selected sources. A document revision unit may be an abstract, a section, or collected revision text; sentences, human reference rewrites, and function-documentation fragments each keep their own type and cannot be added up into a "full-article count". The limited source scope also does not guarantee that the counts are balanced or representative across languages and types.

What gets enriched is determined by the original role and the selected text. Existing human before/after versions or several reference answers do not mean that an AI comparison already exists; the source side for this rewrite has to be chosen explicitly from among them. agent traces containing only AI output, machine pseudo-targets, orphaned records with no alignment relation, and obviously mismatched code and documentation do not enter this round's queue of sources lacking an AI comparison. When an article that already has a comparison takes part in the additional model comparison, it keeps the "comparison" marker.

Source labels follow the existing provenance evidence and preserve the uncertainty about author identity. Community content, some editing data, and a few pre-existing articles cannot be proven item by item to have been written entirely and independently by humans; a `human` or `reference` label, or an input/target label, likewise does not automatically prove quality. The original role, the chosen side, the license, the data split, the content hash, and these limitations are all retained together.

In principle each source goes through two model calls whose contexts are quarantined from each other. The first call reads the selected full text or the complete source unit and extracts subject, predicate, object (SVO) plus the necessary qualifiers: the entity and the object, the scope of negation, conditions, numbers, technical behavior, uncertainty, and attribution of viewpoint. Source paragraph numbers are used only for extraction auditing, and every unit has to map to a proposition, an exclusion reason, or an unresolved status; a full article is not broken up into unrelated paragraph-by-paragraph rewriting tasks.

After extraction, the script shuffles the proposition order using the record's seed, removes source locators and structural cues from the original, and forms a content packet. The second call receives only that packet and the writing requirements; it chooses the title, structure, and wording itself, writes an independent body text in the same language, and submits per-proposition coverage evidence and unresolved items. The writing call does not receive the original body text or the chat history of the extraction call; the two calls may use the same model, and context quarantine is not the same as independent quality verification.

The machine checks verify the JSON structure, the source unit and proposition IDs, whether the evidence is present in the body text, whether the output is complete, and so on. Pilot and independent agent spot checks have already found semantic omissions, negation or polarity changes, and drift in attribution of viewpoint; problems of this kind can still occur when coverage self-reports as passing. Information dropped at the extraction stage may also disappear from the resulting body text and the coverage table alike. Complete coverage therefore cannot prove full-text fidelity, and independent agent spot checks cannot replace human acceptance.

A defect marker applies only to the specific draft that was checked, and is bound to the model, the source hash, and the output text hash. Other model outputs or later versions from the same source have to be checked separately; they cannot inherit that defect conclusion automatically, nor can they be treated as passing merely because they were not sampled.

Some full articles may still lack a usable AI comparison. The failure records include: the requested structured schema's complexity or format was not accepted by the model/router; generation hit the output limit and was truncated or did not terminate normally; a transport error made it impossible to confirm reliably whether the server completed the request or billed for it; and the model refusing or filtering the response. A response that fails the structure or completeness check does not count as a qualified finished draft; a request whose outcome is unclear keeps the `unknown` status, and gaps are not papered over by automatic retries. The specific uncovered sources and their reasons are retained with the delivery summary.

Costs are aggregated across the ledgers of all runs, covering the early pilot, the baseline, the model comparison, and the associated failed requests, listing separately the settled cost, the conservative reserve for unresolved calls, and the total cost exposure:

The user authorized up to $20. The recorded cost of all runs this round totals **$1.08076450**; a further **$0.16447055** is budget reserved for requests whose outcome is unclear, and must not be treated as confirmed spending. The total conservative exposure is **$1.24523505**, below the $10 credit already purchased.

| Model | Input / million tokens | Output / million tokens |
|---|---:|---:|
| [Gemini 2.5 Flash-Lite](https://openrouter.ai/google/gemini-2.5-flash-lite) | $0.10 | $0.40 |
| [Gemini 3.1 Flash-Lite](https://openrouter.ai/google/gemini-3.1-flash-lite) | $0.25 | $1.50 |

These are the text prices verified this round; the six 3.1 comparisons cost $0.159308 on their own. The cost, unsettled reserve, and request status of every run are all included in the delivery summary.

Before each paid request, the client first persists a conservative reserve for the input and the maximum output; it settles only once reliable token usage is available. An `unknown` request keeps holding its reserved quota and stops new scheduling; the quota is not released or reissued automatically. The recovery flow reuses only saved responses that can be verified as accepted and settled, and it checks the original queue, prompt, and budget configuration; a second ledger cannot be set up to bypass unknown calls. The budget cap is enforced per individual ledger; before continuing with sources that were never attempted, all prior spending and unknown reserves are aggregated again before quota is allocated to a new run. Each round's budget cap and its actual spending are recorded separately, and model prices follow the identifier, route, and ledger verified at run time.

Reproduction uses a deterministic queue and versioned prompts: `plainvoice_prepare_enrichment.py` reads the source database read-only and generates the source list; `run_ai_enrichment.py` runs the Gemini 2.5 baseline; `run_ai_enrichment_multi.py` runs the limited-scope model comparison. The run metadata stores the queue and prompt hashes, the model identifier, the random seed, the source text hash, the extraction result, the shuffled packet, the finished draft, the coverage evidence, exceptions, and the cost ledger. Credentials reach process memory only by local hand-off and are not written into public documents or research artifacts.

After all generation processes had stopped, `finalize_ai_enrichment.py` kept the raw generation files, attached scope-limited QA to the corresponding drafts, and summarized each round's results and costs. `plainvoice_ingest_enrichment.py` then imports them into the local review database: same ID and same content is skipped, same ID with changed content raises an error and rolls back, and existing records, content hashes, and reviews are preserved. Articles, data units, model comparisons, and early diagnostics are displayed as separate collections; ingestion means reviewable, it does not mean the quality has been accepted.

Before anything enters SFT or DPO, an independent human has to check the full chain "original text → content card → new body text", assess information retention, expression quality, and practical usefulness, and confirm the data usage rights and the source collection boundaries. A DPO preference label requires a judgment about the specific draft; it cannot presuppose that a given model, the AI draft, or the source draft wins. The current artifacts can be used for review, diagnostics, and designing later experiments, but they do not yet support a claim that training is effective or that a reliable model ranking has been obtained.

The public material provides the method, the aggregate statistics, and permitted examples. Third-party full texts, unlicensed complete comparison drafts, and the raw trace stay within the local review scope; this document contains no private account, credential, or local machine identity information.

## Review entry point

Open the [full local viewer](http://127.0.0.1:8876), which opens on the new-articles collection by default. "New AI rewrites this round" at the top left switches directly between [full articles](http://127.0.0.1:8876/?collection=ai-enrichment-articles), [the six Gemini 3.1 comparisons](http://127.0.0.1:8876/?collection=ai-enrichment-comparison), and [sentence segments and technical fragments](http://127.0.0.1:8876/?collection=ai-enrichment-units). A is the selected original text and B is the corresponding AI draft. The original text, the generated draft, the extracted content card, the writing packet, the coverage table, and the cost information can all be viewed. The desktop files live in `ai-enrichment/`, the master ledger is `delivery-summary.json`, and each round's `pairs.jsonl` is the viewer input with QA already attached; `pairs.generated.jsonl` or `pilot-pairs.jsonl` retains the raw generation record.

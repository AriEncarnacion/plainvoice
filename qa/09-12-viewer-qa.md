# Unified viewer verification

- Six datasets were stream-parsed to 1,246,954 records with unique IDs; all fields, source/target text, 27,205 reference answers, and source-file existence passed their checks. The hashes of 95 manifest-listed source files were verified.
- A further 89 rewrite/technical records had no duplicate IDs, and all 579 claims and 562 trace messages in the articles were preserved; all 200 input files were classified, with no unclassified files remaining.
- After normalization there are 1,247,043 records across 24 collections. The SQLite `quick_check` passed, and the indexes total roughly 2.51 GB. The local API was verified for per-collection counts, the first-record detail of each collection, the final page of the full MCTS set, Chinese and English queries, and reviewed/unreviewed filtering; all passed.
- Front-end HTML, static resource references, and JavaScript syntax checks passed; sources and text are rendered via `textContent`, source HTML, code, and trace commands are not executed, and external images referenced within them are not loaded.
- No browser click, visual, or mobile testing was performed; the syntax and API checks must not be described as full interactive acceptance. Optional WebMCP functionality is skipped on browsers that do not support it; no supported WebMCP verification environment was available, so no runtime verification is claimed to have passed.
- The original research repository's 6 commits and 34 distinct historical blobs were examined, and no credentials, company or client confidential material, or full-text copies of third-party articles were found. A personal account email address in the documentation has been removed from the reachable branch history that will be made public; the old history bundle is retained locally and has not been committed.
- The existing untracked `experiments/` was not committed. Of its contents, 12 candidate copies match the existing paragraph experiments from this round; 36 fictitious test fixtures are not counted as research data.

These are data coverage and program checks, not assessments of writing quality, fidelity, or training effectiveness. The specific local source-file coverage report is saved in `data-viewer/source-coverage.json`.

For subsequent enrichment and incremental ingestion, see [Low-cost AI enrichment verification](09-12-enrichment-qa.md); the 1,247,043 records above are a pre-increment snapshot.

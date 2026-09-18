# Repo-wide body-text cleaning

The corpus covers **1,247,891 records / 28 collections**, of which **214,048 records and 397,342 text fields** changed format. Of the 860 rewrite experiments, 600 are candidates awaiting human evaluation and 260 are quarantined; the remaining records keep their original task meaning. For verification, see the [QA record](qa/09-12-text-cleaning-qa.md); for counts before and after cleaning, see the [length comparison](research/clean-text-2026-09-12/length-comparison.md).

The raw data is left untouched, and a unified `clean-text-v1` derived database is generated from it. Source text, AI rewrites, and all reference answers go through the same rule set; source, author, date, license, task description, model, and QA are kept outside the body text. No model was called and no sentences were regenerated.

## Viewing and downloading

The [local viewer](http://127.0.0.1:8876/?view=clean) shows the cleaned A/B body text by default. In the detail view, "Text version" switches between the raw collected and generated drafts, and "Cleaning record" shows what was removed, why, and which issues still need re-checking. The left side filters rewrite candidates, quarantined records, and other original tasks. Any single item's currently displayed body text can be downloaded.

The complete files live on the desktop at `plainvoice/data/local/clean-text-v1/`:

| File | Purpose |
|---|---|
| `review.sqlite` | All cleaned text, original pairing roles, sources, models, and audit records |
| `text-only/*.jsonl.gz` | Exports all records split across the 28 collections, with fields `id,a,b,references` |
| `rewrite-candidates.jsonl.gz` | Source/AI rewrite candidates that triggered no quarantine rule, still awaiting human review |
| `quarantined-rewrites.jsonl.gz` | Source/AI records needing attention due to failure, semantic, or formatting problems |
| `metadata.jsonl.gz` | Role, language, license, raw/cleaned hash, candidate status, and reason, keyed by ID |
| `format-flags.jsonl.gz` | Repo-wide records carrying format warnings or quarantine reasons; joined to the body text by ID/clean hash, including warnings for text that is empty after cleaning |
| `summary.json`, `qa/` | Full counts, rule fingerprint, exact removals, and defect scope |

Model input takes only the body-text columns. `id` is used to join metadata and is not concatenated into the training text. `null` means unpaired, while an empty string may be a valid insertion/deletion edit; the two are not interchangeable. Multi-reference answers preserve their original order and roles.

## Scope of cleaning

- Removes unambiguous YAML metadata, duplicated document titles, byline dates, breadcrumb navigation, citation/reprint notices, and empty page footers.
- Strips ordinary Markdown/HTML layout, decorative rules, and image tags; keeps the readable text of links and URLs that carry technical meaning.
- Normalizes HTML entities, Unicode, whitespace, and body-text punctuation spacing; for PDF sources, conservatively joins hard line breaks within a paragraph.
- For webpage metadata the AI has already rewritten into ordinary sentences, removal uses the source SHA and a unique exact fragment; an audit record is left for each one. Sentences that mix in substantive content and cannot be resolved by deletion alone are retained and quarantined.
- The OWID download snapshot contains orphaned footnote anchors with no endnote body attached: these webpage numbers are removed, the research attribution and year are kept, and the source is flagged as missing its endnotes. No citations were fabricated.

Code, API endpoints, mathematical expressions, scientific sub- and superscripts, units, negations, Javadoc, list order, and table structure all count as content. To keep cleaning repeatable and preserve technical meaning, code fences, inline code, and formula/table delimiters are deliberately retained. Valid JSON traces are stored as-is and not converted into prose. arXiv's `[MATH]` and `[CITATION]` are retained and flagged as a source limitation.

A few ambiguities remain at the collection layer: hard line breaks inside some PDF paragraphs, scientific-notation spacing such as `CO 2` / `B 12`, and placeholders for missing formulas or citations. These are not fixed by guesswork; the corresponding source limitations are retained, and specific examples are in the local QA.

Paragraphs are not deleted on the basis of single words like "copyright" or "cookies", body text is not arbitrarily deduplicated, facts are not corrected, and run-on sentences or spelling problems are not guessed into new phrasings.

## Quarantine and training boundaries

Only explicit rewrite experiments enter the candidate/quarantine export; other published data keeps its original task semantics and cannot be treated uniformly as human–AI pairs. Authorship of source texts follows the source evidence, and format cleaning does not promote it to "high-quality human gold".

Known failed stubs, Chinese tasks that produced English, confirmed omissions, over-compression, identical text, pre-existing independent semantic defects, and other diagnostics needing re-checking are quarantined separately. Automatic flags such as numeric discrepancies may have legitimate explanations; quarantine means something needs attention, not that every item is a factual error. No SFT correct answers or DPO chosen/rejected labels were generated automatically.

Original IDs are retained, and a separate content hash is computed after cleaning. Old reviews still correspond to the old hash and are not silently carried over to the cleaned text.

## Reproducing

The cleaning script requires Python 3.11+ and SQLite FTS5, with standard-library dependencies only. The sidecar holding exact source text fragments exists only in the local data package and is not published to GitHub.

```sh
python3 scripts/clean_data_corpus.py \
  --database "$HOME/Desktop/plainvoice/data/local/data-viewer/review.sqlite" \
  --output "$HOME/Desktop/plainvoice/data/local/clean-text-v2" \
  --removals "$HOME/Desktop/plainvoice/data/local/clean-text-v1/qa/scoped-removals.json" \
  --defects "$HOME/Desktop/plainvoice/data/local/clean-text-v1/qa/scoped-defects.json" \
  --warnings "$HOME/Desktop/plainvoice/data/local/clean-text-v1/qa/review-warnings.json"
```

Once the body text is built, the source warnings can be exported separately in a form that is easy for a training adapter to read:

```sh
python3 scripts/export_cleaning_flags.py \
  --database "$HOME/Desktop/plainvoice/data/local/clean-text-v2/review.sqlite" \
  --output "$HOME/Desktop/plainvoice/data/local/clean-text-v2/format-flags.jsonl.gz"
```

The output directory must not already exist; the script validates raw file hashes, cleaning idempotency, total row counts, and SQLite integrity before publishing the derived directory. A newer version can be selected through the viewer's `--clean-database` argument.

Subsequently, `plainvoice_prepare_enrichment.py` prepares new queues from the cleaned database by default and records the cleaning version and raw hash; an explicit `--db` can reproduce a specified input version. Existing queues and generated results are not modified. Clearly corrupted formula/citation placeholders, wiki editing residue, and non-body-text traces are skipped when sampling for subsequent automatic rewrites; other source limitations travel with the queue.

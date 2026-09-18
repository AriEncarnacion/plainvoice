# Low-cost AI enrichment verification

- The IDs, complete payloads, and content hashes of the 848 new records were matched item by item against the ingestion result.
- The ID/hash sequence of the pre-existing 1,247,043 records is entirely unchanged; the full database holds 1,247,891 records across 28 collections.
- The API record counts for the new collections, the first complete A/B text in each collection, Chinese and English search, and the SQLite `quick_check` all passed.
- 47 offline program tests, 9 finalizer fault-injection checks, and 9 incremental import scenarios passed; no paid model was called for verification.
- The defects found in 11 drafts by the independent agent's spot check are bound only to the specific model and text hash that were checked, and are not inherited by other drafts from the same source.
- No browser interaction or visual testing was done this round; this round of checks does not constitute acceptance of human writing quality.

Attribution mismatches, changes in causality or polarity, omission of technical conventions, and repetition have been found in the long-form texts. Gemini 3.1 fixed some specific problems in two Chinese samples while also introducing or retaining other omissions, so no overall model win rate can be drawn from this. Spot checks on short units also found context omissions and altered evidence attribution, even where automatic coverage reported no error.

All candidates still require item-by-item review; they are not ground truth. For statistics and per-round cost, see the [delivery summary](09-12-enrichment-summary.json).

The new collections are placed at the top of the sidebar and support direct `collection` / `language` / `q` deep links; JavaScript syntax and static resource checks passed.

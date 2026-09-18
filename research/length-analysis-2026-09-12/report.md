# AI rewrite length: descriptive statistics for local candidates

Statistics over the 848 saved Chinese and English candidates. The main analysis covers the Gemini 2.5 batch: 836 items after excluding one confirmed failed output; 6 Gemini 3.1 comparisons and 5 early pilot items are listed separately. Targets that were never generated are excluded.

Chinese is counted in Han characters, excluding punctuation, spaces, digits, and Latin letters. English is counted in words made of letters; apostrophe contractions count as one word and hyphenated words are split; digits do not count as words. Counts are taken from the A/B body text as-is, without stripping headings, quotations, code, or URL letter strings. Chinese and English are not combined into a single total length.

Percentage change = (AI length / source length − 1) × 100%. The "median change" is computed per item first and then taken as a median, which is not the same quantity as the change in total character count.

| Batch / type | N | Source → AI mean length | Longer | Unchanged | Shorter | Median change |
|---|---:|---:|---:|---:|---:|---:|
| Chinese short sentences · 2.5 | 346 | 45.7 → 49.7 | 240 (69.4%) | 23 | 83 | +6.9% |
| English sentence segments / technical snippets · 2.5 | 462 | 129.3 → 127.1 | 228 (49.4%) | 43 | 191 | +0.0% |
| English full articles · 2.5 | 26 | 2317.3 → 1251.3 | 1 (3.8%) | 0 | 25 | -43.6% |
| Chinese full articles · 2.5 (only 2) | 2 | 1196.5 → 1302.5 | 1 (50.0%) | 0 | 1 | +17.5% |
| English full articles · 3.1 (only 4) | 4 | 4559.8 → 493.2 | 0 (0.0%) | 0 | 4 | -76.4% |
| Chinese full articles · 3.1 (only 2) | 2 | 1196.5 → 750.0 | 0 (0.0%) | 0 | 2 | -33.4% |

English sources broken out (main analysis; technical snippets are not mixed in with long-form articles):

| Source | N | Share longer | Median change |
|---|---:|---:|---:|
| arxivedits-alignment | 60 | 38.3% | +0.0% |
| asset-references | 59 | 39.0% | +0.0% |
| code2doc | 15 | 66.7% | +17.4% |
| coedit | 60 | 48.3% | +0.0% |
| coggen-owid | 15 | 0.0% | -59.8% |
| freshwiki | 9 | 11.1% | -18.8% |
| iterater-human-doc | 268 | 53.4% | +0.7% |
| rewrite-article-v2 | 2 | 0.0% | -20.7% |

Conclusion: in this batch, Chinese short sentences more often grew slightly longer; English sentence segments showed no general inflation; English full articles were usually shortened substantially. There are only 15 code2doc technical snippets, of which 10 grew longer with a median of +17.4%, which shows that the specific source and task type matter.

Limitations: the Chinese short sentences all come from MCTS, so the Chinese/English difference cannot be attributed to language itself. This experiment covers only a specific model and the SVO extraction → shuffling → rewriting pipeline, and does not generalize to all AI. Human authorship follows the source annotation and was not certified item by item. Shortening may come from semantic omission, body-text/metadata contamination, or over-generalization, and must not be read as a quality improvement.

Data quality finding: the output for one long OWID article is only "The article" (2 words), with ID `plainvoice-enrichment-svo-v3:68d31c2616d399a6570c761d`. Although it was saved as a candidate, it did not in substance complete a rewrite; it has been excluded from the main statistics, but the raw data was left unchanged. Including it, English full articles are N=27 with 26 shorter and a median of −44.3%; excluding it, N=26 with 25 shorter and a median of −43.6%, leaving the main direction unchanged.

Per-item counts are in `pair-lengths.csv`; collection summaries and input file hashes are in `summary.json`. No model was called, and no changes were made to source texts, generated drafts, or individual reviews.

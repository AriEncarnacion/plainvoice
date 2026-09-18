# After format cleaning: length change between source and AI draft

This run reads the 848 already-generated candidates. The earlier Gemini 2.5 main statistics excluded the failed short draft, giving N=836; this run additionally excludes one Chinese task mistakenly written in English, giving a main analysis of N=835. The raw and cleaned versions in each row below use exactly the same record IDs, so that changes caused by swapping samples are not mistaken for an effect of cleaning.

Counting follows the previous definition: Chinese counts Han characters only; English counts letter-words, with word-internal apostrophes not split and hyphenated words split, and digits not counted. AI / source − 1 is computed per item first, then the median is taken. Code, formulas, and headings that carry content meaning may be retained, so these are not model token counts either.

| Same sample batch | N | Source mean: before → after cleaning | AI mean: before → after cleaning | Median AI change vs source: before → after |
|---|---:|---:|---:|---:|
| Chinese short sentences · 2.5 | 345 | 45.7 → 45.7 | 49.9 → 49.9 | +7.0% → +7.0% |
| English sentence segments / technical snippets · 2.5 | 462 | 129.3 → 129.3 | 127.1 → 127.1 | +0.0% → +0.0% |
| English full articles · 2.5 | 26 | 2317.3 → 2008.9 | 1251.3 → 1172.2 | -43.6% → -43.7% |
| Chinese full articles · 2.5 | 2 | 1196.5 → 1189.5 | 1302.5 → 1294.5 | +17.5% → +17.9% |
| English full articles · 3.1 comparison | 4 | 4559.8 → 4551.0 | 493.2 → 490.8 | -76.4% → -76.3% |
| Chinese full articles · 3.1 comparison | 2 | 1196.5 → 1189.5 | 750.0 → 750.0 | -33.4% → -32.8% |

How formatting and webpage miscellany affect the counts:

- Same batch of 347 Chinese items: sources total −14 Han characters (−0.08%), AI drafts total −16 Han characters (−0.08%); 2 and 1 items respectively changed count.
- Same batch of 488 English items: sources total −8,021 words (−6.69%), AI drafts total −2,055 words (−2.25%); 27 and 15 items respectively changed count.

After cleaning, English full articles still shorten more often: 25/26 are shorter than the source and 1/26 is longer. The median relative length change moves from −43.6% to −43.7%. This shows that formatting miscellany does affect the counts, but a change in length by itself says nothing about fidelity or writing quality.

Quality boundary: only the effect of format cleaning is compared here; apart from the two excluded items — the failed short draft and the wrong-language one — the remaining quarantined semantic-risk samples stay in the same-ID descriptive statistics. That does not let them enter the training candidates or become ground truth. The Chinese short sentences are concentrated in MCTS as a source, so the Chinese/English difference cannot be attributed to language itself. There are very few Chinese full-article samples.

Six Gemini 3.1 comparisons and five early diagnostic drafts are kept separately in their own JSON collections and are not merged into the Gemini 2.5 main statistics. All figures are computed by script; the report contains no source or generated body text. The previous statistics files are unchanged.

Data: `length-comparison.json` holds per-item before/after counts, collection-level results, raw and cleaned content hashes, and the reasons for the two exclusions. Script: `scripts/analyze_cleaned_lengths.py`.

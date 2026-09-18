# Body-text cleaning QA — 2026-09-12

Covers 1,247,891 records, 28 collections, and 2,466,749 text fields; raw data, model outputs, and existing reviews were not modified, and no model was called.

## Completeness

- 397,342 fields across 214,048 records changed format; the cleaned database's row count, IDs, pairing roles, and 33,562 reference answers correspond one-to-one with the source database.
- All 31 body-text/metadata gzip files were read in full, parsed, and CRC-checked; per-collection ordered IDs and full-text hashes match SQLite exactly. 600 candidates and 260 quarantined records make up 860 rewrite experiments in total; neither side of a candidate is empty.
- A 32nd file, `format-flags.jsonl.gz`, was verified independently: 148,318 records carrying source warnings or quarantine reasons, containing no body text. It can be used to exclude corrupted sources when reading the archived data.
- 62,595 null targets are retained as unpaired. 2,400 fields that originally held only whitespace were normalized to empty strings; a further 6 non-empty fields became empty after HTML, bylines, or reference definitions were stripped, all belonging to 5 archived records, which keep their full audit trail and warnings and are not mixed into the rewrite candidates.
- The source database's SHA256 is identical before the build, after the build, and in independent QA: `a8b2572fbc88853b424ed4b1f8840f605bb32ec6bd251b7b794725b144d47188`.
- Rule fingerprint: `ec3783638cc9f0473fd5087f0cc29c863f09f25a0ebc4a6a87a40f4480c7d11c`. At build time, re-cleaning every changed field produces an unchanged result.

## Content protection and interface

28 offline format-protection tests, 12 real local HTTP tests, and 14 sampled regression tests passed. A corpus-wide rule rescan found and fixed LaTeX without delimiters being misread as Markdown; formulas with unclear structure, diffs, wiki editing residue, and ASCII art are preserved and flagged.

An independent format check covered 328 records and 748 fields, including all 47 article/paragraph AI outputs and 20 code2doc samples. 41 code blocks, the code content of 1 HTML `pre` example, 30 formula/citation placeholders, and 35 specified numeric/technical fact checks passed.

Both the source and the AI draft of the Spanish flu article start directly at the body text, with frontmatter, bylines, duplicated titles, horizontal rules, copyright/citation footers, and webpage information restated by the AI removed. The source lacks the endnote body text, so its source warning is retained and it is quarantined; it is not claimed as fidelity-grade gold.

The local API selects the cleaned database by default and supports the raw version, search, quality filtering, and cleaning audits; version-hash isolation has been tested, so reviews of the raw text do not automatically become reviews of the cleaned draft. Static resources, DOM IDs, JS syntax, and local page responses passed their checks. A real browser verified the cleaned/raw toggle, candidate filtering, audit expansion, and two-column layout on the Spanish flu article; the raw version still shows the original YAML, and switching back to the cleaned version shows the body text directly.

## Still requires human judgment

Five AI sentences blend author/date into the substantive content; these are preserved and quarantined. Some PDF hard line breaks, scientific-notation spacing, missing figures/endnotes, and run-on sentences already present in the source cannot be fully recovered by safe typographic rules. Code fences, formulas, and table structures are preserved in order to protect their meaning.

The quality quarantine holds automatically diagnosed items awaiting checking; it is not the case that all 260 have been proven wrong. The verification above does not substitute for authorship verification, preference annotation, full semantic equivalence, or human quality review. The complete item-by-item audit and the source text excerpts exist only in the local data package.

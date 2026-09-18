# Full Text Rewrite v2: SVO Content Extraction → Shuffle → Independent Composition

The user asked for the first round's six sources to be redone: first extract pure content from the full text, then have the AI organize the language on its own, with the evaluation unit changed to the whole article. The source texts, content packets, generated results, and side-by-side page are saved on the desktop at `plainvoice/data/local/human-rewrite-pairs/article-v2/`. This document records the method; results that have not undergone human evaluation are not called gold.

## What changed this round

The first round gave the model only a short opening fragment and asked directly for a rewrite. The second round reads the complete body text of all six pieces and writes the whole article only after an independent content representation. There is no target length taken from the source, and no preset number of paragraphs.

1. **Extract the content of the full text.** Each proposition has a subject, predicate, and object, and retains qualifiers, attribution, modality, polarity, and depends_on. The coordinator separately stores source_locator and the full-text coverage record. Simple triples cannot express qualifiers such as "retry when the parameters are the same and the original key is still retained," and these conditions must not be erased when sentences are split.
2. **Remove organizational hints from the source.** Strip source locations, title metadata, original numbering, and source order out of the writer packet. Shuffle all propositions using the fixed seed 20260912, HMAC opaque numbering, and deterministic sorting. Real causality, event order, and the meaning of API operations are not randomized.
3. **Compose in a new session.** Each piece is written by a Codex subagent with `fork_turns: none`, given only that piece's content packet and the writing instructions. The model chooses its own title, entry point, organization, paragraphs, and sentences; looking back at the sources, at adjacent files, or searching for the original text is forbidden. Every qualifier and every piece of unique content should be expressed, and the article carries no claim ID.
4. **Keep the raw output and review it.** Output the body text and a separate coverage JSON. The coordinator does not polish the body text. A mechanical check confirms whether the coverage record is complete; the review page separately asks about facts, omissions, organizational similarity, and overall preference.

The six full texts yielded **579 propositions**. "Full text" here means the cleaned, complete body text; images linked externally from the HTML were not newly transcribed, and non-body material such as PDF footers, copyright notices, site navigation, and comments has a separate exclusion record.

| Source | Language | Number of Propositions | Scope |
|---|---|---:|---|
| Howard Marks, How Quickly They Forget, 2011 | EN | 192 | Body text and postscript, including tables |
| Howard Marks, There They Go Again . . . Again, 2017 | EN | 196 | Full body text, historical judgments retained |
| Ruan Yifeng, RESTful API Design Guide, 2014 | ZH | 81 | Full text and code examples |
| Ruan Yifeng, How to Reduce Software Complexity?, 2018 | ZH | 40 | Full text |
| Stripe, Designing robust and predictable APIs with idempotency, 2017 | EN | 46 | Full text and two practical code examples |
| Stripe, Idempotent requests, current snapshot | EN | 24 | Full API documentation text and the meaning of the demonstrations |

## Points that need critical scrutiny

**Shuffling the input order does not guarantee an independent output structure.** The new Stripe 2017 draft still forms the teaching sequence "network failure → idempotency → key → backoff". The model may reconstruct an approximate outline from semantic relations. Sentence-level change and discourse-level change therefore have to be evaluated separately; completing the shuffle is not by itself evidence that the rewrite succeeded.

**Extraction is a lossy risk point.** The model may already have lost tone, exceptions, or the author's stance before it starts writing. This round retains source locations, so errors can be told apart as source → content or content → rewrite. Propositions are still natural language, and book titles, the author's own statements, and the names of historical memos sometimes count as content; this is neither thorough source anonymization nor a purely semantic representation proven to erase every syntactic trace.

**A completeness record is not a fidelity conclusion.** Matching source-unit counts and all claim IDs appearing in the coverage only show that the records line up. Coverage is self-reported by the generator, and 100% information retention cannot be declared on that basis. Character counts, n-gram overlap, and the order-reversal ratio are only diagnostics, not scores for quality, AI-ese, or semantic equivalence.

A second model re-checked Stripe 2017 and Ruan Yifeng's REST — the two full source texts, the new drafts, and 127 extracted propositions in total. It did not confirm any major omission or reversal, but it recorded two specific issues: REST's "list (array)" became "list or array" during extraction, introducing slight formatting ambiguity; the final sentence of the new Stripe draft about a complete rollback may state a sufficient condition as a necessary one, logged as a low-confidence observation. Both have been put on the local review page, and the body text keeps the raw generated output. This model re-check cannot be extrapolated to the other four pieces, and it does not replace human evaluation.

**The sources themselves have problems too.** Within the Howard 2017 piece the same memo is dated 2007 in one place and 2008 in another, which has to be recorded as an unresolved item. Ruan Yifeng's 2018 description of Windows/Unix file behavior is kept as the historical source has it; the technical details have not been independently verified. The authorship and original date of the current Stripe document are unknown. The older-dated articles are likewise only the snapshot downloaded this time, and were not checked word-for-word against historical archives.

**The generation environment has limits.** A new session prevents inheritance from this conversation and restricts contact with the sources through the read instructions; no separate OS-level file sandbox was built. Following repository conventions, some writers read the root README first, which does not contain these source texts. The system writing instructions still influence the result. The tooling did not return a precise backend checkpoint, token count, or cost amount, so those fields stay empty; the fixed seed is used only for arranging the content packet, and is not a generation sampling seed.

**The task distribution still differs from that of future deployment.** The current direction is human article → content card → AI new draft. It can supply candidate pairs and a checking method, but what a future model receives is usually an AI draft. The human source text does not necessarily win; only after human preference judgments and semantic review can it be decided how any of this enters SFT or preference data.

## Files and reproduction

- [Content extraction prompt](prompts/article-content-extraction.md)
- [Compose from a content packet prompt](prompts/article-from-content.md)
- [Validate and shuffle content packets](scripts/prepare_article_packets.py)
- [Generate the full-text review page](scripts/build_article_review.py)

```sh
python3 scripts/prepare_article_packets.py \
  --input-dir /path/to/article-v2/content-extraction \
  --writer-dir /path/to/article-v2/writer-packets \
  --audit-dir /path/to/article-v2/packet-audit \
  --seed 20260912

python3 scripts/build_article_review.py /path/to/article-v2/article-results.json
```

The preparation script does not call a generation model. Each writer receives only its own packet and the composition instructions; output should be saved as `<packet_id>.md` and `<packet_id>.coverage.json`. The raw sources, run inputs, coverage self-reports, and generation records are kept on the desktop and not committed to the repository. The older paragraph experiment remains at `human-rewrite-pairs/review-paragraph-v1.html`.

Script checks include schema, duplicate IDs, missing references, semantic dependency cycles, uncovered source units, and reproducibility under the fixed seed. Page build checks cover full-text embedding, HTML escaping, failure on missing input, and JavaScript syntax. Browser interaction has not been through actual acceptance testing; this is not a test of human writing quality.

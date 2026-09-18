# Full Text Rewrite v2: SVO Content Extraction → Randomization → Independent Text

The user requested a redo of the first round of six source articles: first, extract pure content from the full text, then let AI organize the language automatically, and change the evaluation unit to the entire article. The original text, content package, generated results, and comparison page are saved on the desktop. `plainvoice/data/local/human-rewrite-pairs/article-v2/` This document records the method; results that have not been evaluated by others are not referred to as "gold".

## This change

The first round only provided a short opening segment of the model, requiring direct rewriting. The second round involved reading six complete texts, representing their content independently, and then writing the entire article. There was no target length for the original text, nor was there a preset number of paragraphs.

1. **Extract full text content.** Each proposition has a subject, predicate, and object, and retains qualifiers, attributes, modality, polarity, and depends_on. The coordinator stores the source_locator and full-text overwrite record separately. Simple triples are insufficient to express constraints such as "retry when parameters are the same and the original key is still retained," and these conditions cannot be removed during sentence splitting.
2. **Eliminate original text organization hints.** Remove original text location, title metadata, original numbering, and source order from the writer packet. Shuffle all propositions using a fixed seed 20260912, HMAC opaque numbering, and deterministic sorting. True causality, event sequence, and API operation meaning are not randomized.
3. **New Conversation Writing.** Each piece consists of one... `fork_turns: none` The Codex subagent writing tool provides only a single content package and writing instructions. The model independently selects the title, entry point, organization, paragraphs, and sentences; it prohibits looking back at sources, adjacent files, or searching the original text. All specific and unique content should be expressed, and the article does not include a claim ID.
4. **Preserve the original output and review it.** Output the main text and a separate coverage JSON. The coordinator does not polish the main text. Mechanically check for completeness of coverage records; the review page asks for additional facts, omissions, organizational similarity, and overall preferences.

**579 propositions were extracted from the six full-text articles.** "Full-text" refers to the cleaned, complete text; HTML external images were not transcribed, and non-text elements such as PDF footers, copyright notices, website navigation, and comments were excluded separately.

| Source | Language | Number of Propositions | Scope |
|---|---|---:|---|
Howard Marks, How Quickly They Forget, 2011 | EN | 192 | Text and postscript, including tables |
Howard Marks, There They Go Again... Again, 2017 | EN | 196 | Full text, retaining historical judgment |
| Ruan Yifeng, RESTful API Design Guide, 2014 | ZH | 81 | Full text and code examples |
| Ruan Yifeng, How to Reduce Software Complexity?, 2018 | ZH | 40 | Full Text |
| Stripe, Designing robust and predictable APIs with idempotency, 2017 | EN | 46 | Full text and two practical code examples |
| Stripe, Idempotent requests, current snapshot | EN | 24 | Full API documentation text and demonstration meaning |

## Areas that need to be viewed critically

**Scrambling the input order does not guarantee an independent output structure.** The Stripe 2017 draft still follows the teaching sequence of "network failure → idempotency → key → backoff." The model may reconstruct an approximate outline from semantic relationships. Therefore, sentence structure changes and discourse changes must be evaluated separately; scrambling itself is not evidence of successful rewriting.

**Extraction carries a risk of loss.** The model may have lost tone, exceptions, or authorial stance before writing. This round retains source location, allowing errors to be distinguished as source → content or content → rewrite. Propositions remain in natural language; book titles, author biographies, and historical memo names sometimes belong to the content; this is neither complete source anonymization nor a purely semantic representation that has been proven to erase all syntactic traces.

**Completeness records are not a guarantee of fidelity.** Consistent source unit counts and the appearance of all claim IDs in the coverage only indicate record alignment. Coverage is self-reported by the generator and cannot be used to declare 100% information retention. Character count, n-gram overlap, and order reversal ratios are diagnostic, not scores for quality, AI-likeness, or semantic equivalence.

Another model was reviewed, examining the complete original and new drafts of Stripe 2017 and Ruan Yifeng's REST, totaling 127 extracted propositions. No major omissions or reversals were confirmed, but two specific issues were noted: REST's "list (array)" was changed to "list or array" during extraction, introducing slight formatting ambiguity; the last sentence of Stripe's new draft regarding complete rollback may have mistakenly stated a sufficient condition as a necessary condition, as a low-confidence observation. Both issues are on the local review page, and the original generated results are retained in the main text. This model review cannot be extrapolated to the other four papers, nor can it replace human review.

**The source itself is also problematic.** Howard's 2017 memo contains a discrepancy between 2007 and 2008, which needs to be recorded as an unresolved issue. Ruan Yifeng's 2018 Windows/Unix file behavior is preserved based on historical sources, but the technical details have not been independently verified. The author's source and initial time of the current Stripe document are unknown. Older articles are merely snapshots of this download and have not been verified word-for-word against historical archives.

**The production environment has boundaries.** New sessions prevent inheritance of the current conversation and restrict source access through read commands; no separate OS-level file sandbox is created. Some writers read the root README first according to repository conventions, which does not contain these original texts. System write commands still affect the results. The tool does not return precise backend checkpoints, tokens, or amounts; these fields remain empty. Fixed seeds are only used for content package arrangement, not for generating sample seeds.

The task distribution and future deployment are different. The current approach is human article → content card → AI draft. This provides candidate pairs and checking methods, but the model will typically receive AI drafts in the future. Human original texts do not necessarily win; human preference and semantic review are needed to determine which data enters the SFT or preference dataset.

## Documents and Reproduction

- [Content extraction prompt](prompts/article-content-extraction.md)
- [Packaged into a document prompt based on content](prompts/article-from-content.md)
- [Verify and shuffle the content package](scripts/prepare_article_packets.py)
- [Generate full-text review page](scripts/build_article_review.py)

```sh
python3 scripts/prepare_article_packets.py \
  --input-dir /path/to/article-v2/content-extraction \
  --writer-dir /path/to/article-v2/writer-packets \
  --audit-dir /path/to/article-v2/packet-audit \
  --seed 20260912

python3 scripts/build_article_review.py /path/to/article-v2/article-results.json
```

The preparation script does not call the generative model. Each writer only receives its own packet and writing instructions; the output should be saved as... `<packet_id>.md` and `<packet_id>.coverage.json` The original source, run input, overwrite self-report, and build history are saved on the desktop and not committed to the repository. Older paragraph experiments are retained. `human-rewrite-pairs/review-paragraph-v1.html`.

Script checks include schema, duplicate IDs, missing references, semantic dependency cycles, uncovered source units, and reproducibility of fixed seeds. Page build checks include full text embedding, HTML escaping, missing input failures, and JavaScript syntax. Browser interaction has not undergone actual acceptance testing; this is not a test of human writing quality.

# Draft Plainvoice annotation protocol

This document is the unified protocol v0.1 for the first pilot and has not yet been calibrated against human evaluation. Where it differs from the alternative scales, sample sizes, or experiment arm numbering in the research memo, this document and the [main plan](09-12-research-and-experiment-plan.md) take precedence. A new version is frozen before the real experiment begins; using test results to change the rules retroactively is forbidden.

## What reviewers see

Language, region/audience, domain, channel, task, source draft, available factual material, information that must not be lost, the mutable and immutable parts, an author voice reference (where one exists), and candidates A/B. Source, model name, generation time, detector score, and any system recommendation about a draft are hidden.

Chinese and English use separate reviewers familiar with the target market; technical documentation and marketing each require the relevant domain experience. The four cells carry the same number of main tasks. Native-English phrasing is not assumed to be better than clear non-native phrasing; formal Chinese phrasing is not automatically treated as templated.

## Round 1: independently checking constraints

Record `pass / fail / uncertain` for each draft. Only information the original brief marks as mandatory constitutes a hard constraint; all facts must still avoid unfounded change. Record omissions, fabrications, changes to numbers/units/identifiers, changes to negation/condition/certainty, and whether the task was completed.

Major failures include changes that would lead a reader to take the wrong action, misjudge product capability, or accept an unsupported promise. Minor poor word choice is recorded separately as a style issue. Where the factual material is contradictory or lacks context, choose uncertain and state what is missing; do not guess.

## Round 2: locating problems

Each dimension uses a 0–3 **issue severity**: 0, nothing to point out; 1, local and minor; 2, recurring or affecting use; 3, seriously obstructing the purpose. The dimensions are: useful information, structure and pacing, contextual fit, voice preservation, necessity of the edit, and subjective sense of templatedness. Where there is genuinely not enough information to judge a dimension, use null/abstain rather than substituting 0 for unknown.

For every non-zero score, give the text span, a brief reason, and the effect on the reader; "too much AI-ese" on its own is not acceptable. Where the source draft is already good, leaving it unchanged is an acceptable answer. Speculation about AI provenance does not factor into scoring.

## Round 3: independent paired preference

Answer separately: which draft is better suited to actual use, and which draft feels less templated? Each question allows A, B, tie, both_unacceptable, and insufficient_context. A preference on naturalness may run opposite to the overall adoption preference; both are kept, and they are not forced into agreement.

Before the first review, the rubric is explained using practice examples that do not enter the final test. In the pilot, disagreement between two first-pass reviewers goes to a third for adjudication, but the original votes are retained; in the final test each pair gets three independent reviewers, and the adjudication result likewise does not replace the original votes. A/B order is randomized; stability is checked on a separate QA subset through reordering and delayed re-review, and duplicate drafts do not increase the independent sample count.

## Four demonstrations: not ground truth

All of the following are original demos from this repository. The figures and products are hypothetical and illustrate only the annotation approach. There is no real human evaluation here, so none of it may count toward a benchmark. The Chinese scenarios keep their Chinese specimen text, with an English gloss in parentheses.

| Scenario | Given facts and source draft | Rewrite open to discussion | What to check |
|---|---|---|---|
| Chinese technical | Given: request timeout 30 seconds, idempotency key retained for 24 hours. Source draft: "这不只是简单的超时设置，而是对可靠性的全面保障。请求超时为 30 秒，幂等键保留 24 小时。" (*"This is not merely a simple timeout setting, but a comprehensive guarantee of reliability. The request timeout is 30 seconds, and the idempotency key is retained for 24 hours."*) | "请求在 30 秒后超时。幂等键保留 24 小时。" (*"Requests time out after 30 seconds. The idempotency key is retained for 24 hours."*) | What was removed is an unsupported guarantee; "因此绝不会重复执行" ("and so it will never execute twice") must not be added. If the fact pack requires idempotent behaviour to be explained, a substantiated explanation must still be supplied. |
| English technical | Given: retry only HTTP 429, at most three retries, waits of 1/2/4 seconds; no retry on 401. Draft: "Our robust retry mechanism seamlessly handles errors. Only 429 responses are retried, up to three times after 1, 2, and 4 seconds. Never retry 401 responses." | "Retry only 429 responses, at most three times, waiting 1, 2, and 4 seconds before successive retries. Do not retry 401 responses." | Preserve the count, the order, the codes, and the negation. Do not drop 401 for the sake of pacing; keep the explicit imperative. |
| Chinese marketing | Given: Team edition with 3 seats, ¥199/month, 14-day trial. Source draft: "不只是协作工具，更是团队效率的全新起点。团队版每月 199 元，含 3 个席位，可试用 14 天。" (*"Not just a collaboration tool, but a whole new starting point for team efficiency. The Team edition is ¥199 per month, includes 3 seats, and offers a 14-day trial."*) | "团队版含 3 个席位，199 元/月。试用 14 天。" (*"The Team edition includes 3 seats at ¥199/month. 14-day trial."*) | Do not add "无需信用卡" ("no credit card required"), "随时退款" ("refund any time"), or a percentage efficiency gain. The shorter draft is not necessarily better; it needs a brand/channel judgment. |
| English marketing | Given: import CSV campaign data; compare weekly campaign results. Draft: "Unlock seamless insights with a game-changing dashboard. Import CSV campaign data and compare results week by week." | "Import your campaign CSVs. Compare results week by week." | Clear, but it may be missing the brand voice; it cannot be claimed as verified better than the source draft, still less used to infer a conversion rate. |

## Counterexamples that must be tested

A legitimate contrast should be preserved: "Use a project token, not a personal token, for this endpoint." (only where the evidence pack supports it). Necessary repetition should be preserved: repeating a warning about an irreversible action during a multi-step procedure. A short tagline may carry rhythm and metaphor; a technical specification may be formal and predictable; non-native English may be plain and accurate.

Also include: drafts that are polished but change a number wrongly, short drafts that drop a condition, fabricated customer stories, deliberately introduced typos, drafts that delete all the information, good drafts returned unchanged, and candidate text with scoring instructions smuggled into it. Reviewers must be able to recognize these cases rather than only tracking banned words.

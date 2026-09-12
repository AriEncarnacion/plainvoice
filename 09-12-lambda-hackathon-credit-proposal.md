# Plainvoice — Lambda Hackathon Compute Proposal

**Request: $450 in additional Lambda Cloud credits, bringing the allocation to $500 including the initial $50.**

Participant: Jason Hu

Lambda account: `[private account email omitted]`

I’m building a small model that rewrites AI-generated drafts into clearer, more natural writing while preserving facts and the author’s intent. The hackathon experiment will test whether targeted post-training improves on strong prompting and multi-step editing workflows, and whether a small model can provide comparable quality at lower inference cost.

I expect approximately **$300–420 of Lambda usage** for the planned exploration, including a reserve for failed experiments. The $500 request provides a spending ceiling and flexibility if available GPU configurations differ. This is a compute estimate, not a claim that training results have already been measured.

## The project

AI drafts often contain vague claims, repetitive framing, unnecessary rhetorical contrasts, and a generic voice. An effective rewriter should remove those weaknesses without inventing details or dropping useful information.

The prototype will cover four equally weighted categories: English technical documentation, Chinese technical documentation, English marketing copy, and Chinese marketing copy. For the hackathon, I will focus on paragraphs and short sections. Full-length document quality and professional editorial validation are follow-up work.

The main outputs will be a working rewrite demo, a reusable evaluation set, adapter checkpoints, and a comparison of writing quality, factual preservation, latency, and compute cost. I can share the demo and experiment report with the organizers.

## Experiment design

I will start with dense text models such as **Qwen3-4B and Qwen3-8B**, using non-thinking output for the rewrite task. Their official model cards document these checkpoints and the non-thinking mode.[1][2] They are practical hackathon candidates, not a claim about the best available models.

The experiment will compare:

1. The unchanged draft and a simple rewrite prompt.
2. A stronger prompt with editing rules and examples.
3. A critique–rewrite–verify workflow.
4. Supervised fine-tuning with LoRA adapters.
5. A small DPO preference-tuning stage, if the initial evaluation supports it.

The planning envelope is **up to 24 SFT experiments and 8 DPO experiments**, covering data variants, model size, a small hyperparameter grid, and repeat runs of promising configurations. These are maximum experiment slots; I will stop unproductive branches early. LoRA is the default on H100; QLoRA is a fallback if memory constraints justify it, since quantization is not automatically the fastest choice.

Data will combine authorized writing examples, synthetic draft/revision pairs, and a small set of human-reviewed anchors. Human and model provenance will be recorded separately from quality. Train and evaluation splits will keep related documents, translations, and generated variants together.

I will reserve a small balanced holdout, initially **160 tasks, 40 per category**. A separate calibration set will help align the rubric with human judgments. The hackathon evaluation is exploratory; this sample does not establish small statistically significant gains in every category.

## Keeping each training round within 30 minutes

The target is **at most 30 minutes for a bounded post-training round after the environment, model weights, and tokenized data are ready**. Each round includes optimization, adapter saving, and a small smoke evaluation. Dataset creation, initial setup, and the full holdout evaluation are budgeted separately.

I will use the following controls:

- Start with a warmed-up **4B model**, then test the **8B model** on one or two H100s. Measure whether two-GPU training is actually faster before using it routinely.
- Use short examples, initially at most **1,024 total tokens per SFT sequence**, with packing that respects example boundaries. Do not silently truncate required facts.
- Run a representative throughput calibration for each model and objective. Allocate roughly **20 minutes to optimization**, with the remaining time for loading adapters, saving, smoke checks, and slack.
- Start SFT experiments around **0.4–0.8 million processed tokens**, including prompts and targets. Finishing that optimization in 20 minutes requires approximately **333–667 aggregate training tokens/second**. These are required-throughput calculations, not benchmark claims.
- Set the actual round token budget to no more than **80% of measured throughput × 1,200 seconds**, capped by the planned data budget. Shrink the data subset or step count when the target would otherwise be exceeded.
- Start DPO with a few hundred preference pairs. Measure DPO throughput separately, including both chosen and rejected sequences; do not reuse SFT timing estimates. Cache reference-model log probabilities before repeated experiments where appropriate, and charge that computation to the data-preparation budget.[3]
- Save adapters rather than merging and exporting a full model every round. Run the full evaluation outside the short training loop.

This makes the 30-minute requirement a realistic **iteration budget**, not a promise to complete unlimited data or a full-parameter training job in half an hour. A timer or failure does not count as a completed experiment: completed tokens, steps, checkpoint status, and failures will be logged. If even the reduced configuration fails the timing requirement, I will use the smaller model and narrow the experiment rather than claim the target was met.

## Lambda compute budget

Rates below are Lambda’s published on-demand instance prices checked on **September 12, 2026**, before applicable taxes.[4] Multi-GPU figures are converted to whole-instance cost; the advertised rate is per GPU.

| Configuration | Published price per GPU-hour | Whole-instance hourly cost | 30-minute allocation |
|---|---:|---:|---:|
| 1× H100 SXM, 80 GB | $4.29 | $4.29 | $2.15 |
| 2× H100 SXM, 80 GB each | $4.19 | $8.38 | $4.19 |
| 1× H100 PCIe, 80 GB | $3.29 | $3.29 | $1.65 |

The primary training budget assumes a **2× H100 SXM instance**, with a separate **1× H100 SXM instance** used intermittently for data preparation, teacher/critic inference, evaluation, and demo work. The latter can also host independent experiments when useful. Peak requested capacity would be three H100 GPUs; availability and account quota remain to be confirmed.

| Work | Allocation | Estimated cost |
|---|---|---:|
| Setup, model/data loading, throughput calibration | 6 hours × 1 H100 SXM | $25.74 |
| SFT exploration | 24 rounds × 0.5 hours × 2-H100 instance | $100.56 |
| Preference-tuning exploration | 8 rounds × 0.5 hours × 2-H100 instance | $33.52 |
| Synthetic data, candidate generation, preference preparation, reference caching | 12 hours × 1 H100 SXM | $51.48 |
| Prompt baselines, judge calibration, full evaluations | 12 hours × 1 H100 SXM | $51.48 |
| Debugging, integration, final demo and reproduction | 8 hours × 1 H100 SXM | $34.32 |
| **Planned instance usage** | **70 GPU-hours across the two instance types** | **$297.10** |
| Extra reruns and throughput uncertainty | Planning reserve | $90.00 |
| Persistent storage and billing incidentals | Allowance, not a quoted storage/tax rate | $30.00 |
| **Working budget including reserves** | | **$417.10** |
| **Requested total credit allocation** | Existing $50 + requested $450 | **$500.00** |

The training allocation is 16 instance-hours on two GPUs; the support allocation is 38 instance-hours on one GPU. Overlapping work across the two lanes makes this a roughly two-day compute sprint, although human data review and exact hackathon timing may require a narrower run list. These hours are spending allocations, not measured time-to-completion estimates for each task.

Lambda bills running on-demand instances in one-minute increments, including idle time, until termination.[5] The budget therefore includes setup and debugging time. I will terminate unused instances after saving required artifacts and track total instance hours, rather than count only training steps. Stopping a training process alone does not stop instance billing.

If only H100 PCIe instances are available, the single-GPU hourly cost is lower, but I will recalibrate throughput rather than assume the same completion time. Additional credits do not guarantee GPU availability; confirmation of H100 access would also be helpful. Filesystem charges and any credit exclusions, taxes, or expiration terms will be confirmed in the account rather than inferred from this proposal.

## Other costs and scope

Most generation and automated evaluation can run on Lambda using open-weight models. An **optional $30–80 external API allowance** could cover selected frontier-model comparisons; that is a separate spending cap, not a provider quote, and is not part of the Lambda credit request. With that option, the working monetary budget is approximately **$330–500 across providers**, before any exceptional charges beyond the allowances.

This estimate assumes I perform the hackathon’s data review and development. Paid professional annotation, a large statistically powered human study, production hosting, and ongoing retraining are not included. They belong to a later research or product budget.

If a $500 allocation is not possible, a **$250 total-credit version** would narrow the model/hyperparameter grid to roughly 12 SFT and 4 DPO round slots, with fewer teacher and evaluation hours. The initial $50 is useful for setup and a small proof of concept; the additional credits fund a broader comparison and repeat experiments.

## Evaluation and deliverables

Success means a useful improvement in blind editorial preference while preserving facts, technical conditions, and author intent. An AI detector score will not be the primary reward or the definition of good writing.

I will compare all methods on the same source material and report the four language/domain categories separately. Failures, ties, unsupported claims, omitted constraints, and unnecessary edits to good drafts will remain visible. A small independent human review will check whether automated judging agrees with actual editorial preference.

The final hackathon package will include:

- A before/after rewrite demo for all four categories.
- Training recipes, adapter checkpoints, and logged wall-clock times per round.
- A comparison of prompting, editing workflows, SFT, and any completed DPO runs.
- A cost ledger and an explanation of where training helped, failed, or was unnecessary.

The broader literature review and experiment design are already organized in the private [Plainvoice repository](https://github.com/onjas-6/plainvoice). This attachment is self-contained; repository access is not required to assess the credit request.

## Sources

1. Qwen team. [Qwen3-4B official model card](https://huggingface.co/Qwen/Qwen3-4B).
2. Qwen team. [Qwen3-8B official model card](https://huggingface.co/Qwen/Qwen3-8B).
3. Hugging Face. [TRL DPO Trainer](https://huggingface.co/docs/trl/dpo_trainer) and [SFT Trainer](https://huggingface.co/docs/trl/sft_trainer). Implementation references; not evidence for this proposal’s throughput target.
4. Lambda. [On-demand GPU pricing](https://lambda.ai/pricing). Checked September 12, 2026.
5. Lambda. [Billing overview](https://docs.lambda.ai/public-cloud/billing/). Checked September 12, 2026.

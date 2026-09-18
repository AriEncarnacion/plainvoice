# Plainvoice：训练方法、底座规模与 prompting 对照

执行口径：本备忘录的 B0–B5 编号、400→1,600→4,000 学习曲线为备选设计；统一实验臂及阶段样本采用[主方案](../09-12-research-and-experiment-plan.zh-CN.md)。未实际启动实验。

研究日期：2026-09-12（America/Los_Angeles）。本文件是研究与实验建议；未下载模型、采购算力、创建训练数据或启动训练。中文、英文 × technical docs、marketing 四个分层同等优先。模型存在性、结构和许可证来自官方卡；其通用 benchmark 分数不等于本任务效果。

建议先把任务定义为 **有约束的编辑**：在保持事实、论证关系、用途与作者声音的前提下，减少空泛、机械铺陈和不必要的修辞。首轮训练用 7–9B 档 instruction/post-trained 底座做 SFT + LoRA/QLoRA，同时保留 4B 成本对照和 27B 提示词参照。只有 SFT 仍有稳定、可标注的风格偏好问题，才追加小规模 DPO。现在没有证据支持直接投入在线 RL，也没有证据支持某一个参数规模已经足够。

## 1. 原方案中最需要改的训练假设

**优质人类文章适合提供风格参照，不直接构成改写训练对。** 只在旧文章上做 next-token continued pretraining，教的是该语料的续写分布；它没有教模型如何根据输入保留数字、限制条件、API 名称与论证。将文章包装成随意反推的 prompt，也可能制造输入缺事实、输出却有事实的训练样本。模型会学到“写具体一点”就可以补出不存在的细节。这是任务定义推导出的风险，而不是某篇论文已经测定的失败率。

应优先收集 `原稿 + 使用场景/受众 + 不可改事实/结构约束 → 编辑后稿`，并记录编辑原因。让真人编辑真实模型原稿、真实人的冗长原稿和已经不错的原稿；后一类要允许不改或轻改。没有必要把所有原稿都标成 AI：产品面对的应是具体写作缺陷。

把人类佳作“AI 化”后再还原，可以作为合成数据补充，但不应作为主测试集。它容易让模型只学习反转某个生成器的污染规则；原佳作也可能包含生成 prompt 从未提供的事实。同一原文及其所有污染、改写、译文、候选稿必须属于同一数据 split。

技术文档通常应保留步骤、前置条件、警告、代码和精确术语；marketing 可以保留有效的对比、节奏、品牌口气和情绪。“不是 X，而是 Y”不是自动负例：问题是它有没有解释一个真实区分。把句式禁用规则当成训练目标，会得到另一套模板。

## 2. 与决策直接相关的论文

| 来源与日期 | 实际研究结果/方法 | 对本项目的含义及证据边界 |
|---|---|---|
| [LoRA — Hu et al.，2021-06-17](https://arxiv.org/abs/2106.09685) | 冻结主模型，通过低秩矩阵学习参数更新，是参数高效微调方法。 | LoRA 不是与 SFT/DPO 并列的学习目标；可以用 LoRA 实现 SFT 或 DPO。先用 adapter 便于比较和回滚；论文不能证明低秩更新足以消除四个分层的所有风格问题。 |
| [QLoRA — Dettmers et al.，2023-05-23](https://arxiv.org/abs/2305.14314) | 在冻结的 4-bit 量化主模型上训练 LoRA，并用 NF4、double quantization、paged optimizers 降低显存需求；论文展示特定设置下 65B 在 48GB GPU 微调。 | 支持先做低成本试验。65B/48GB 是论文具体条件下的结果，不能推出本项目长文训练、现代混合架构或 DPO 都能用同样资源；量化对事实保留需另测。 |
| [Direct Preference Optimization — Rafailov et al.，2023-05-29；修订 2024-07-29](https://arxiv.org/abs/2305.18290) | 通过同一输入下 preferred/rejected 回答直接优化偏好，不需要单独训练显式 reward model 或在标准离线训练环节 rollout；在 sentiment、summary、dialogue 上实验。 | 适合处理“都正确，但哪一个写法更自然”的成对偏好。没有测试这里的中英技术文档/marketing 编辑任务，也没有证明它必然比精心制作的 SFT 更好。 |
| [Self-Refine — Madaan et al.，2023-03-30](https://arxiv.org/abs/2303.17651) | 同一 LLM 生成、给出反馈、再修订，不更新模型权重，在七类任务上比较单次生成。 | 应纳入强基线，尤其是定位冗余后局部修改。论文提升不能直接移植到 2026 年底座；每轮可能引入新错，需记录轮数、token、延迟，并与同预算候选选择比较。 |
| [Improving Iterative Text Revision by Learning Where to Edit from Other Revision Tasks — Kim et al.，EMNLP 2022](https://aclanthology.org/2022.emnlp-main.678/) | 将可编辑 span 与 edit intent 显式建模，再迭代修改；利用其他编辑任务数据。 | 比“整篇重写得像人”更接近技术文档需求。可借鉴 `定位 → 编辑 → 校验` 和 edit-intent 标签；不能据此断言 span editing 必然优于现代 LLM 全文改写，需要配对实验。 |
| [The Importance of Online Data: Understanding Preference Fine-tuning via Coverage — Song et al.，2024-06-03；修订 2024-07-16](https://arxiv.org/html/2406.01462v2) | 在其理论设定中，离线对比方法需要更强的数据覆盖条件；提出用在线样本做 KL 正则的 HyPO，并在摘要和 general chat 上实验。 | 不应把 DPO 当成与所有在线 RL 完全等价。初期更实际的应对是从当前 SFT 模型采样并补标偏好，再做一轮离线训练；这是本项目的工程建议，不是论文对该工作流的直接验证。 |
| [Scaling Laws for Reward Model Overoptimization in Direct Alignment Algorithms — Rafailov et al.，2024-06-05；修订 2024-11-05](https://arxiv.org/html/2406.02900v2) | DPO/IPO/SLiC 也会过优化，性能可随优化推进下降。主实验为 TL;DR 与 Pythia，使用 GPT-4 胜率代理评估，并讨论长度投机。 | “不训练 reward model”不等于没有奖励投机。需要独立人类 holdout、检查长度/删信息、频繁存 checkpoint；论文不是对真实人类偏好的直接、跨域证明。 |

这些论文给出方法和失败模式，不能代替专门的任务验证。特别是摘要/对话结论不能直接视作 technical docs 或 marketing 改写结论；中文母语风格判断也不能从英文结果推断。

## 3. 先做哪些 prompting / harness 基线

把以下配置在**相同底座、相同冻结测试输入、同一事实约束**下比较。再额外加入一个强商用模型作为产品替代方案；跨模型结果不能归因为“训练优于 prompting”。

| 配置 | 实验内容 | 要回答的问题 |
|---|---|---|
| B0 原样返回 | 不做改写；保留所有原稿 | 模型是否把好稿改差？改写是否真的有价值？ |
| B1 简单 prompt | 明确用途、受众、事实约束，要求减少冗余并保持语气 | 产品最低成本能做到什么？ |
| B2 任务 rubric + few-shot | 每个语言/场景提供若干已授权的编辑前后示例；包含应该保留的句式及不改样例 | 写作偏好能否被少量具体例子表达？ |
| B3 检索例子 | 只从训练 split 取相同语言、体裁、缺陷类型的编辑对作示例 | 可控的示例库是否比固定 prompt 更有效？不得检索测试原稿或近重复版本。 |
| B4 定位/改写/校验 | 先指出冗余或虚假对比位置，再有限修改，最后核对事实与代码；最多一轮修复 | 多步骤是否换来足够改善？特别看事实损失和 p95 延迟。 |
| B5 同预算 best-of-N | 例如生成两份候选，由独立评估器选取，设与 B4 接近的总 token 预算 | B4 的收益究竟来自修订策略，还是只是用了更多推理资源？ |
| T1 SFT adapter | 同一底座，使用真人审校的编辑对，尽量单次输出 | 能否把可重复的提示词能力压缩成便宜且稳定的模型行为？ |
| T2 SFT + DPO adapter | 由 T1/current policy 产生同一输入的候选；都过事实门槛后标成对偏好 | 偏好训练是否带来 SFT 之外的增益？ |

固定训练/开发/测试划分之后才能调 prompt。为每条输出记录底座 revision、template、thinking 设置、量化方式、sampling seed、输入/输出/思考 token、wall time、失败与重试。先比较 matched compute，再给出各方法实际部署的质量/成本曲线；不能只比一次 SFT 调用与三次 API 调用的风格分数。

校验器至少分两层：数字、链接、引用、代码、API/flag 等可进行确定性 diff；因果、条件、范围、可能性/确定性等语义变化交给独立审查及抽样人工验证。事实检查不是一个笼统的 embedding similarity 分数。技术文档可设置关键语义错误直接不合格；marketing 不得用编造客户案例、数据或夸大承诺换取具体感。

## 4. 底座选择：已核验的候选，不是宣称最优的排名

以下官方页面于 2026-09-12 回读。新版架构与旧版传统 decoder 的差异会影响训练工具支持，所以实际训练前还需在固定版本工具链上验证加载、backward、adapter 保存/重载与量化部署。

| 档位与精确模型 ID | 官方卡确认的结构和参数 | 许可证 | 建议角色 |
|---|---|---|---|
| 3–4B：[`Qwen/Qwen3.5-4B`](https://huggingface.co/Qwen/Qwen3.5-4B) | 卡片标注 4B **language model**，带 vision encoder；32 层，Gated DeltaNet 与 Gated Attention 混合，FFN；不是 4B active 的 MoE。 | Apache-2.0 | 成本/延迟对照。先验证双语复杂条件保留，不能预设它只能做简单英文任务。 |
| 7–9B：[`Qwen/Qwen3.5-9B`](https://huggingface.co/Qwen/Qwen3.5-9B) | 9B language model、vision encoder；32 层混合 DeltaNet/Attention，FFN。 | Apache-2.0 | 首选实验规模。是预算与容量的起点判断，不是本任务实测最优。 |
| 12–14B：[`google/gemma-4-12B-it`](https://huggingface.co/google/gemma-4-12B-it) | 11.95B dense unified；48 层；局部 sliding-window 与全局 attention；统一多模态，无独立 vision/audio encoder。 | Apache-2.0 | 作为不同家族 12B 对照，可检验结果是否只在 Qwen 家族成立。需要独立测中文写作与术语稳定性。 |
| 12–14B 备选：[`Qwen/Qwen3-14B`](https://huggingface.co/Qwen/Qwen3-14B) | 实际总参数 14.8B，非 embedding 13.2B；40 层、GQA、纯文本 causal LM。 | Apache-2.0 | 较成熟的传统架构对照；它与 9B 是不同代，性能差异不能视作纯参数 scaling。 |
| 27–32B：[`Qwen/Qwen3.8-27B`](https://huggingface.co/Qwen/Qwen3.8-27B) | 27B language model、vision encoder；64 层混合 DeltaNet/Attention，FFN。 | Apache-2.0 | 较高容量开放权重参照及候选生成器；先跑 baseline，再决定是否花钱训练。 |

发布日期有独立官方依据：[Qwen 官方仓库 News](https://github.com/QwenLM/Qwen3.8) 记录 2026-03-02 发布 3.5-4B/9B、2026-08-14 发布 3.8-27B；[Google 官方公告](https://blog.google/innovation-and-ai/technology/developers-tools/introducing-gemma-4-12B/) 日期为 2026-06-03。Qwen3-14B 在这里仅作为已可访问的候选，未另外核定最初公开日期。未声称上述列表覆盖截至研究日所有最新/最强模型。

不要把 Qwen 全家族介绍里的 MoE 概述错误套到这些 FFN 型号上；也不要把模型名字中的 “4B active/effective” 当成总权重。上表的 Qwen3.5/3.8 参数为卡片 **Language Model** 项，完整 checkpoint 还有视觉等组件，部署/训练占用需另测。

第一轮可以只训练 9B；4B、12B、27B 先跑提示词。如果 4B 通过完整四分层测试且达到成本目标，再训练 4B；若 9B 的事实保留明显落后于 27B，而风格已接近，优先调查容量/输入组织，而非继续提高风格 reward。不同家族、年代的模型比较能帮助选产品底座，但不是干净的 scaling-law 实验。

## 5. 分阶段训练设计

这些数量是用于估算工作量的起始范围，并非文献证明的数据门槛；最终以学习曲线和标注一致性决定。

1. **先校准任务与基线。** 建一个四分层均衡、来源隔离的试验集；各层至少包含原本写得好的稿、真实坏稿、技术/商业关键约束、长度跨度。B0–B5 做人工盲评，允许 tie；记录理由，而非只问“像不像 AI”。若 B2/B4 已达到产品需求，训练的价值主要是降低调用成本、延迟或部署依赖。
2. **SFT：先小样本学习曲线。** 人工审校 400 → 1,600 → 4,000 个编辑对，每档四层各占 25%；不可复用冻结测试数据。训练目标只覆盖 assistant 的正式改写，不训练模型输出“以下是去 AI 味版本”等包装。训练集中加入不改/轻改案例；具体比例通过过度编辑率选定。预先标注需保留事实，拒收通过删去约束换取流畅的 target。
3. **参数高效实现。** 先用 LoRA；若设备不足则 QLoRA。候选 rank 16/32，较小 learning-rate 网格、1–2 epoch 起步，按开发集选 checkpoint。数值是待调假设。现代混合 attention 架构不能盲目复用旧模型的 `q_proj/v_proj` 清单；按实际 module 名称决定 adapter 覆盖。只训练文本路径，是否卸载/冻结其他组件需先验证框架支持。
4. **DPO：只解决剩余偏好。** 由当前模型为同一原稿产生多个候选，人工比较通过事实检查的两个版本。保留语言、体裁、缺陷类型与长度差标签；重点加入“更短但丢事实”“更活泼但过度口语”“保留恰当对比比生硬禁用更好”等难例。可从 1,000–3,000 个偏好对试起；训练早期也评估，不能只保存最后一个 checkpoint。可把直接 DPO 与 SFT→DPO 作小型消融，但不能省掉 SFT-only。
5. **在线学习放后面。** 若固定偏好集覆盖不足、出现新生成器风格、已校准 evaluator 在新数据仍可信，再考虑当前 policy 采样、补标和迭代 DPO。只有这一过程的收益仍受探索限制、流量和资金足够时，才立项在线 PPO/GRPO。事实硬约束是候选门槛，风格只是通过门槛后的排序项；不采用“AI detector 分数越低 reward 越高”的单目标。

如果两个候选一个更自然但有关键事实错误，不能把它作为总体 preferred 样本；应该明确事实优先，或把该比较单独标注成某一个风格维度，避免与总偏好混用。DPO 的训练目标没有自动知道“保真优先”。

## 6. 显存与成本：先给公式，再测真实吞吐

下表是 **十进制 GB 的权重下界与工程规划范围**，不是 benchmark，也不是可装载承诺。4-bit 权重下界按 `参数量 × 0.5 byte`；BF16 按 `参数量 × 2 bytes`。实际还需要量化 metadata、非量化层、adapter、optimizer、activations、workspace，推理另有 KV cache。Qwen 行只用 language-model 标称参数计算，完整 checkpoint 可能更大。

| LM 参数量 | 4-bit 权重理论下界 | BF16 权重理论下界 | 短序列 QLoRA 训练起始设备规划* |
|---|---:|---:|---|
| 4B | 2 GB | 8 GB | 16–24GB 显存档 |
| 9B | 4.5 GB | 18 GB | 24–48GB 显存档 |
| 11.95B | 约 6 GB | 约 23.9 GB | 32–48GB 显存档 |
| 14.8B | 7.4 GB | 29.6 GB | 48GB 显存档 |
| 27B | 13.5 GB | 54 GB | 48–80GB 显存档 |

\* 假设文本总序列长约 2K–4K、microbatch 1、gradient checkpointing、低秩 adapter、只训练文本路径且工具链兼容；只是安排试跑的设备档，不排除优化后更小设备可行，也不保证所列设备在任意配置下可行。长文、吞吐优先的大 batch、双候选 DPO 会改变预算。DPO reference 可通过预计算 reference log-prob 降显存，但 policy 的 chosen/rejected 序列仍需要算力。全参数 Adam 训练常见存储项粗算约 16 bytes/param（BF16 权重/梯度、FP32 master/moments）；9B 仅这些项即约 144GB，尚未算激活，实际随 optimizer/sharding 精度变化。

训练费用必须由试跑测定。例：4,000 对、平均 input+target 共 2,048 token、2 epoch，处理约 16.4M token。若**假设**实际训练吞吐为 100–1,000 token/s，单次 run 约 4.6–45.5 小时；若**假设**算力价为 $1–$3/GPU-hour，则约 $5–$137。两项均为敏感性分析，不是市场报价或某张 GPU 实测；不包括超参搜索、评估、失败重跑、存储、老师模型生成和人工标注。此例不能直接用于 DPO 或在线 RL。

需要报告 `总训练支出 / 通过事实检查且被人偏好的改写数`、推理每千字成本与 p50/p95 延迟。若训练的一次性成本为 C，每次合格改写比 harness 节省 Δc，粗略回本量是 `C/Δc`；人工数据维护和模型更新成本要计入 C。价格/硬件未选择前，不应给承诺式预算。

## 7. 必须保留的未知项

- 目前没有本项目四分层上的训练结果；不能断言 post-training 优于强提示词，更不能断言 4B/9B/27B 的质量顺序。
- 没有证据表明一个统一风格 reward 能兼容 technical docs 的结构需求与 marketing 的品牌声音；应报告每层结果和失败类别，macro average 不能掩盖中文或技术文档退步。
- 通用写作 benchmark、官方 model-card 分数、LLM judge 胜率可用于筛选，不能作为商业文案转化率或技术文档可执行性的替代证明。
- 论文上的 QLoRA 内存结果来自不同年代底座；新模型混合 attention 和多模态路径的训练支持必须实测。
- 人工标注不一致如果来自真实审美差异，应保留条件化偏好、style profile 和 tie，不应把它们都强行压成统一的 gold scalar。
- 单纯变短、删除标题、避开高频词、增加口语或错误，都可能让部分 judge 认为更像人；需要“信息保留 + 写作质量 + 使用场景有效性”三方面同时验证。

下一步应先产出可讨论的 rubric、四分层样例与冻结 baseline protocol；训练配置只是这些定义稳定后的实现选择。

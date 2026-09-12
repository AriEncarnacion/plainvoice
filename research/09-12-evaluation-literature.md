# Plainvoice：如何定义 ground truth，并验证「去 AI 味」真的改善了写作

执行口径：本备忘录保留文献推导出的备选量表与规模；第一轮统一采用[标注协议 v0.1](../09-12-annotation-protocol.md)的 0–3 问题严重度，以及[主方案](../09-12-research-and-experiment-plan.md)的 80 项 pilot、实验臂编号和统计规则。

研究日期：2026-09-12。范围：中文与英文、technical documentation 与 marketing copy 四个场景同等优先。本备忘录聚焦测量与评估，属于第一轮有针对性的文献调研；不是穷尽到 2026 年的系统综述。文献均链接原始论文或作者发布的正文，未以二手文章作为结论依据。

## 核心判断

用户提出「先做 evaluator，再训练 rewriter，再和 prompting / harness 比较」的顺序基本合理，但 evaluator 的目标不能设成「检测作者是不是 AI」。至少要分开三件事：

| 要测的对象 | 标签来源 | 在本项目中的用途 |
|---|---|---|
| Provenance：实际由谁、用什么流程产生 | 可核验的来源、时间戳、生成日志、编辑记录 | 分析数据覆盖和混淆因素，不能直接当优劣标签 |
| Perceived AI-ness：读者觉得模板化、泛化、机械的程度 | 目标读者盲评，最好附具体文本证据 | 用户感知指标，必须承认文化、语言、场景和个人差异 |
| Writing utility：是否准确、具体、清楚、适用 | 编辑/领域专家依据 brief 和源材料评估；适用时做客观检查 | 产品主要目标，与内容保真一起作为选择模型的依据 |

把 pre-ChatGPT 文本标成「好」，把模型生成文本标成「坏」，很容易训练出年代、词汇、网站和排版分类器。高质量的人类文字、糟糕的人类套话、优质 AI 改写、糟糕 AI 文本都应该进入标注范围。AI 来源不是负类，人类来源也不是正类。这是本项目的数据设计建议，不是某一论文已经证明的普适分类法。

对用户举的「不是 X，而是 Y」，应标注它是否提供真实区分、边界或机制。比如「此操作不是追加写入，而是覆盖现有文件」有重要含义；「这不是一次升级，而是一场革命」在没有证据时可能只增加情绪。句式出现次数可以辅助定位，不能单独决定质量。避免把「去 AI 味」变成另一个固定腔调。

## 12 篇关键文献与适用边界

### E01. 人类也会把「听起来像人」与真实来源混淆

**Maurice Jakesch, Jeffrey T. Hancock, Mor Naaman. 2023. _Human heuristics for AI-generated language are flawed_. PNAS 120(11), e2208839120.** [论文 DOI](https://doi.org/10.1073/pnas.2208839120) · [作者预印本全文](https://arxiv.org/pdf/2206.07271)

六个实验共 4,600 名参与者，考察职业、约会与住宿平台的自我介绍。主要实验的来源判断准确率约 50%–52%。第一人称、家庭话题等让读者感觉更像人，却未必真能区分来源。另一方面，让另一组人直接评价「重复」「不通顺」时，可以测到部分真实问题。论文还展示了根据人类感知选出的文本，比实际人类文字更容易被判为人写。

**本项目采用：**把「模板感/空泛/冗余」拆成可定位的编辑问题；另问整体 AI 感，不让来源猜测主导所有评分。

**限制：**这是英文 self-presentation、较早模型的研究，不能推出今天专业编辑对中文技术文档也只有随机判断水平。可迁移的是测量警示，不是准确率。

**阅读范围：**全文中的实验设置、主结果、启发式分析、优化文本与讨论；未复核附录所有统计模型。

### E02. Detector 的低困惑度信号可能惩罚清楚、朴素的非母语英文

**Weixin Liang, Mert Yuksekgonul, Yining Mao, Eric Wu, James Zou. 2023. _GPT detectors are biased against non-native English writers_. Patterns 4(7), 100779.** [正式全文](https://pmc.ncbi.nlm.nih.gov/articles/PMC10382961/)

研究用七种 detector 评估 91 篇 TOEFL 文章与 88 篇美国八年级文章，TOEFL 文章平均误报率为 61.3%；增强词汇后降到 11.6%。这是特定检测器、样本与时间的结果，不是所有现有检测器的现行误报率。它说明稀有词、复杂表达和检测分数有可能绑在一起。

**本项目采用：**单列非母语英文切片；把清晰、朴素、专业的英文放进正例。不要训练模型为了「像人」故意增加罕见词、语法错误或口语填充。

**限制：**两组人的年龄、体裁、写作环境也不一致；该设计不能把全部差异精确归因于母语身份。中文应独立验证，不能直接套用 TOEFL 结论。

**阅读范围：**正式全文的样本、误报、词汇干预与讨论。

### E03. 多语言 detection 数据集不能直接充当双语文案质量集

**Yuxia Wang et al. 2024. _M4: Multi-Generator, Multi-Domain, and Multi-Lingual Black-Box Machine-Generated Text Detection_. EACL.** [正式论文](https://aclanthology.org/2024.eacl-long.83/) · [PDF](https://aclanthology.org/2024.eacl-long.83.pdf)

M4 覆盖多个生成器、领域及包括中英文在内的七种语言，发现未见领域与生成器上的泛化仍困难。其中文部分是 Baike/Web QA；英文包括 Wikipedia、WikiHow、Reddit、arXiv 与 PeerRead。论文表 1 的总数为 147,895 条人类/机器文本，中文为 9,000 条，其中 3,000 条人类文本；不要把「parallel」理解成逐句忠实改写对。

**本项目采用：**借鉴跨生成器、跨领域和跨语言切分；可用它做外部分布压力测试。

**限制：**中英文领域不匹配，无法仅由整体分数区分语言影响与领域影响；QA 不代表技术文档或营销文案。没有本项目所需的「更好改写」偏好标签。

**阅读范围：**数据构造、表 1、中文来源、human evaluation 与跨语言实验定义。

### E04. Detection 分数对解码和表面改动很脆弱

**Liam Dugan, Alyssa Hwang, Filip Trhlík, Andrew Zhu, Josh Magnus Ludan, Hainiu Xu, Daphne Ippolito, Chris Callison-Burch. 2024. _RAID: A Shared Benchmark for Robust Evaluation of Machine-Generated Text Detectors_. ACL.** [正式论文](https://aclanthology.org/2024.acl-long.674/) · [PDF](https://aclanthology.org/2024.acl-long.674.pdf)

RAID 含超过 600 万条 generation/变体，覆盖 11 个生成器、8 个主要领域、11 类攻击和 4 种解码设置；测试 12 个检测器。换采样方式、repetition penalty、生成器或表面形式都会影响检测。主集采用 pre-2022 人类来源；这是一种 provenance 选择，并未把人类文字定义为优秀。

**本项目采用：**保留 decoding、模型版本、prompt、来源文档的完整元数据；相同源文的全部生成与改写必须在同一数据分区。

**限制：**核心任务是 detection，主集不是中文市场文案。某些压力测试会损坏数字等内容，因此「检测分数下降」本身不能说明 rewriter 有益。

**阅读范围：**数据构建、生成设置、检测器与阈值评估、limitations；未逐项复现攻击。

### E05. Detection 的理论边界不能被夸大成「任何检测都无效」

**Vinu Sankar Sadasivan, Aounon Kumar, Sriram Balasubramanian, Wenxiao Wang, Soheil Feizi. _Can AI-Generated Text be Reliably Detected?_ 2023 首发；本轮阅读 2025-01-17 v4.** [全文](https://arxiv.org/html/2303.11156v4)

论文研究递归 paraphrasing 对多类 detector 的影响，也指出改写可能轻微降低文本质量。其理论把最佳 detector 的 AUROC 上界与人类/模型文本分布的 total variation distance 联系起来：分布越接近，来源识别越困难。

**本项目采用：**detector 只作为诊断指标；自然、准确的 AI 改写也可能难以检测，反之则未必。

**限制：**「模型进步一定让真实世界所有文本分布无限接近」不是该定理直接证明的事实；实际 TV 难以从有限文本精确估计。论文不证明所有给定领域的 detector 都没有用。

**阅读范围：**v4 摘要、paraphrase 质量说明、理论第 4 节、Theorem 1 及假设解释；未逐行检查证明。

### E06. 风格迁移已有更合适的多维评估传统

**Remi Mir, Bjarke Felbo, Nick Obradovich, Iyad Rahwan. 2019. _Evaluating Style Transfer for Text_. NAACL.** [正式论文](https://aclanthology.org/N19-1049/) · [PDF](https://aclanthology.org/N19-1049.pdf)

论文区分 style transfer intensity、content preservation、naturalness，主张观察这些目标间的取舍。在 Yelp 情感迁移实验中，自然度的相对判断比绝对分数有更高的标注一致性；但风格强度并没有同样的普遍收益。该实验中的句子困惑度没有与自然度人评显著相关。

**本项目采用：**同时记录改写幅度、保真、自然度与任务质量；用 blinded pairwise preference 做主要比较，并用分维度评分诊断原因。

**限制：**情感转换比开放式「去 AI 味」边界清楚得多；论文提出的词级 masking 和 WMD 不应直接作为技术文档事实检查器。

**阅读范围：**评估定义、human evaluation、结果与 tradeoff 讨论；未复现旧模型。

### E07. 通用 LLM judge 可以有用，但必须先对当前任务做 meta-evaluation

**Lianmin Zheng et al. 2023. _Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena_. NeurIPS Datasets and Benchmarks.** [全文](https://arxiv.org/html/2306.05685)

论文系统分析位置、冗长、自我偏好与推理能力限制。GPT-4 judge 在其具体人类偏好数据上达到超过 80% 的一致性；这不是对任何新写作任务、任何新 judge 的准确率保证。它区分 pairwise、单答案打分、带参考答案的评判。

**本项目采用：**隐藏模型名与来源，随机 A/B，交换顺序重复一部分样本；校准集上比较 judge 与领域编辑的一致性，分别报告四个场景。用不同家族 judge 可以发现分歧，但不能证明偏差独立。

**限制：**通用聊天偏好不等于专业文案效果；人类评价本身也可能偏爱长、整齐和自信的答案。

**阅读范围：**评估形式、bias 章节、human agreement 与数据定义。

### E08. Rubric judge 的可行起点与自我强化风险来自同一篇论文

**Yang Liu, Dan Iter, Yichong Xu, Shuohang Wang, Ruochen Xu, Chenguang Zhu. 2023. _G-Eval: NLG Evaluation using GPT-4 with Better Human Alignment_. EMNLP.** [正式论文](https://aclanthology.org/2023.emnlp-main.153/) · [PDF](https://aclanthology.org/2023.emnlp-main.153.pdf)

G-Eval 使用任务/维度定义、评价步骤与结构化填表。论文在 SummEval 上报告平均 Spearman 相关 0.514，同时明确提出 judge 可能偏好 LLM 生成的摘要，并警告把这种评价直接用于调优可能强化自身偏好。

**本项目采用：**先用 rubric + 锚点样例 + evidence spans 作为 evaluator baseline；分别校准各维度。让评价输出局部证据和简短理由，并不意味着理由必然正确，仍要抽检。

**限制：**偏好 LLM 文本在论文中是初步分析和潜在解释，不是已排除混淆因素的普遍结论；摘要/对话上的相关性不能直接外推。

**阅读范围：**方法、SummEval 表 1、LLM 输出偏好分析、limitations。

### E09. 控制长度，但不能把「越短越好」换成新的奖励

**Yann Dubois, Balázs Galambosi, Percy Liang, Tatsunori B. Hashimoto. _Length-Controlled AlpacaEval: A Simple Way to Debias Automatic Evaluators_. 2024 首发；本轮阅读 2025-03-10 v2.** [全文](https://arxiv.org/html/2404.04475v2)

通过回归调整输出长度差，估计相同长度时的偏好；在其 AlpacaEval 实验中，与 Chatbot Arena 排名的 Spearman 相关从 0.94 提升到 0.98。作者明确列出假设与适用边界：英文简单指令、特定 judge prompt、希望比较相同长度的输出。

**本项目采用：**同时报告原始偏好、长度变化、信息保留和长度匹配的敏感性分析。

**限制：**本项目的目标之一可能就是删掉废话，长度也是方法实际产生的中介结果。仅报告控制长度后的分数会把真实收益也一起消掉；不能强制技术文档与 tagline 长度相同，也不能把中英文 token 数直接混用。

**阅读范围：**定义、回归控制、主结果、other biases 与 limitations。

### E10. 用原子事实检查改写，但必须补上 recall

**Sewon Min, Kalpesh Krishna, Xinxi Lyu, Mike Lewis, Wen-tau Yih, Pang Koh, Mohit Iyyer, Luke Zettlemoyer, Hannaneh Hajishirzi. 2023. _FActScore: Fine-grained Atomic Evaluation of Factual Precision in Long Form Text Generation_. EMNLP.** [正式论文](https://aclanthology.org/2023.emnlp-main.741/) · [PDF](https://aclanthology.org/2023.emnlp-main.741.pdf)

FActScore 把长文拆成原子事实，逐条检查可信来源是否支持，再计算 factual precision。论文明确说明它不衡量 recall：少说甚至不说，可以减少出错机会却仍不满足任务。

**本项目采用：**对改写做两个方向的检查：输出新增/改变的断言是否有材料支持，以及原文要求保留的断言是否仍完整存在。另检查数字、单位、否定、条件、版本、API 标识符与承诺强度。

**限制：**输入文本本身可能错误；「忠于原文」与「真实世界正确」要区分。严谨模式应提供 source pack 或经人确认的 claim ledger。营销比喻和观点不能全部当成事实去打分。

**阅读范围：**定义、知识源假设、biography 范围、precision/recall 限制。

### E11. Judge 要能拒绝「好听但没完成任务」

**Zhiyuan Zeng, Jiatong Yu, Tianyu Gao, Yu Meng, Tanya Goyal, Danqi Chen. 2024. _Evaluating Large Language Models at Evaluating Instruction Following_. ICLR.** [全文](https://arxiv.org/html/2310.07641v2) · [作者数据仓库](https://github.com/princeton-nlp/LLMBar)

LLMBar 有 419 个成对样本，100 个 natural、319 个 adversarial。每对中一个遵守指令，另一个偏离，但可能更有吸引力、更流畅。作者以此检查 judge 是否被表面质量误导，并测试改进评价的 prompting 方法。

**本项目采用：**构造「更口语但漏条件」「更具体但捏造数据」「去掉套话但改错含义」「更有情绪但不符合品牌」等 challenge pairs。把约束失败与风格偏好分开记录。

**限制：**LLMBar 的偏好尽可能客观，本项目的自然度与品牌适配是主观的；不能假定每一对改写都有唯一赢家。

**阅读范围：**任务定义、419 条构成、adversarial construction 与 prompting 设计。

### E12. 多采样挑最好也会过拟合 reward，不只是 RL

**Leo Gao, John Schulman, Jacob Hilton. 2023. _Scaling Laws for Reward Model Overoptimization_. ICML.** [正式论文](https://proceedings.mlr.press/v202/gao23h.html) · [PDF](https://proceedings.mlr.press/v202/gao23h/gao23h.pdf)

论文在 synthetic 设置下，以一个固定 gold reward model 代替人类，训练 proxy reward model。优化 proxy 时，gold score 可能先升后降；研究同时覆盖 RL 和 best-of-n。因此「无训练 harness」也有过优化 evaluator 的风险。

**本项目采用：**训练/选样 judge 与最终盲评隔离；留出从未用于 prompt 迭代、选 checkpoint、选 n 的测试集。观察人工质量随优化强度是否下降。

**限制：**gold 仍是模型，论文没有完整捕捉人类标签与真实需求之间的偏差；不能把其 scaling law 系数直接用于本项目预算预测。

**阅读范围：**研究设置、RL/best-of-n 定义及 4.5 limitations；未复现实验。

## 建议的 ground truth 结构

以下是基于文献的项目设计建议，尚未做真实采集或验证。

1. **来源记录。** 保存 URL、抓取/存档日期、原始发布日期、作者/品牌、许可证、允许使用范围、语言、领域、篇幅和 source pack。pre-ChatGPT 页面应使用当时快照或可核验版本，不能仅凭页面上一个旧日期；旧文字也可能已进入模型预训练语料。
2. **内容约束。** 每个输入对应一个人工核实的 claim ledger：不可丢的事实、数字、条件、术语、证据、CTA、语气与长度约束。技术文档保留可执行性；营销材料保留卖点依据与承诺边界。
3. **质量标签。** 由目标读者/编辑独立评价，不让他们看到 human/AI 标签、模型名、生成时间或 detector 分数。保存分维度结果、胜负/平局、证据片段和分歧，不能把无共识样本自动删除。
4. **改写对。** 同一 source pack 下，包含原稿、人工最小修改、较大重写、不同模型/不同 prompt 的输出。高质量原稿需要「无需改写/轻微修改」标签，防止模型每次都强行改动。

必须避免的最主要混淆是：人类原文获得完整事实背景，AI 却只拿到标题或一句 generic prompt，然后 evaluator 奖励人类的具体信息。主实验应给所有方法同样的 source pack、受众、目的、长度预算。仅凭标题重建人类原文的任务可以保留，但只能作为另一种任务。

四个场景各占相同数量的核心测试单元；中文应有独立原生来源和评审，不只翻译英文。需要把简体/繁体、地区市场、英文非母语表达作为元数据或后续切片，不能在样本不足时声称全面覆盖。

## 初版 rubric：先判约束，再看读者体验

建议每维使用 1–5 级并提供该场景的锚点；不要预先把所有维度压成一个未经验证的「AI 味 0–100 分」。下列是初版标签定义，权重与门槛待小规模人评校准。

| 维度 | 差的表现 | 好的表现 | 记录方式 |
|---|---|---|---|
| 事实与意图保留 | 捏造信息、删条件、改变否定、把可能说成保证 | 保留必要信息、因果、边界与不确定性 | 重大失败/轻微问题/通过；证据定位 |
| 信息贡献 | 同义重复、空泛开场、结尾复述、没有作用的评价词 | 每段提供事实、解释、判断依据或必要过渡 | 1–5；冗余 span；遗漏 claim |
| 具体与可验证 | 假具体、凭空编数字、给所有品牌都适用的话 | 具体到场景、对象、机制、证据与下一步 | 1–5；标明所依赖材料 |
| 结构与句子自然度 | 对称模板、机械三点式、滥用反转句与小标题 | 结构服从内容，句子长短与重点自然 | 1–5；不得靠错字获得高分 |
| 场景适配 | 技术文档抒情；营销文案堆实现细节；不符读者背景 | 技术内容可操作，营销内容有明确受众与承诺 | 1–5；使用场景 rubric |
| 品牌/作者声音 | 所有来源改成同一种语气，伪造个人经历 | 保留必要个性和术语，符合给定参考 | 1–5；无参考时可 abstain |
| 主观 AI 感 | 读者觉得明显泛化、模板化 | 读者觉得自然、有内容、有明确目的 | 独立 1–5；不解释成来源概率 |
| 整体可用性 | 仍需大量改写，或不敢使用 | 可直接采用或只需小改 | A/B/平局/两者均不可用 + 采用理由 |

技术文档的专属检查：前置条件、命令与参数、返回值、异常和边界、版本、权限及错误恢复信息。若原文包含代码，可做语法或相关示例执行检查；不要为纯文字变换编造形式主义测试。

Marketing 的专属检查：受众、问题/利益点、差异化理由、证据、品牌声音、CTA 与禁止承诺。不要把文案人评偏好当成 CTR/CVR；真实转化需要独立实验，并控制受众、渠道、offer 等因素。

## 最小 evaluator 校准与模型 benchmark

**校准阶段。** 建议起步每个场景 30–50 个 brief/source 单元，共 120–200 个；这是预算友好的设计建议，不是统计功效保证。每个单元选择少量质量有差异的输出对，至少三位合适评审做盲评，Jason 提供一部分锚点和偏好即可。技术与营销分别邀请有该领域经验、且熟悉相应语言的评审。记录一致性和分歧原因，再改 rubric。

**Judge 选择。** 比较简单规则特征、单模型 rubric judge、另一个家族 judge；仅在校准数据证明有益时采用 ensemble。至少报告各维度与人类的一致性、pairwise accuracy（在有人类共识的子集）、平局处理、A/B 翻转率、非母语/语言切片、强制约束漏检率。对同一模型重复 prompt 不算独立证据。

**挑战集。** 纳入本来就好的文本、允许的有效对比句、非常朴素但正确的英文、中文正式技术规范、短 slogan、长文档，以及好听但有重大事实错误的改写。特别检查「只删内容」「改数字」「故意错字」「加入无来源轶事」「把所有句子口语化」是否会骗过 judge。

**公平比较。** 同一 frozen 测试集上比较 no-op、基础 rewrite prompt、rubric + examples prompt、critique–rewrite harness、best-of-n、SFT、偏好调优。每个方法只在开发集调参；评估时给相同事实材料与任务约束。分别报告相同单次推理预算和实际质量–成本曲线；harness 额外调用数、延迟、训练摊销不能隐去。最终 judge 不要兼任所有方法的选样 reward。

**主结果。** 优先报告「改写整体采用偏好」与「重大保真失败率」两个结果，并保留四个场景独立表格及等权平均。对有错误但读起来更顺的样本，记录原始偏好同时按照预设重大失败规则判不合格；不能先过滤失败样本再只宣传幸存者胜率。辅助结果报告冗余减少、必要事实 recall、unsupported claim rate、编辑工时、长度变化、主观 AI 感。

**统计与切分。** 按 source/brief 为单位划分 train/dev/test，作者、品牌、站点和派生版本尽量整体隔离；再做留出生成器与新日期数据测试。置信区间应按 source 聚类重采样，避免把同一个源文的多个改写当成独立样本。使用至少两种不同随机种子的训练运行用于验证候选结果时，不应把种子输出混成独立文本样本。样本量应在 pilot 后依据实际变异与期望最小收益做功效规划；不能用一小批「看起来不错」宣布优于 prompting。

**继续训练的判断。** 先证明人类能稳定辨别期望改写、judge 能捕捉这种偏好，再做训练。若强 prompt/harness 已达到目标，post-training 的价值可能主要是成本、延迟、稳定性与部署方式；若只有自动 judge 分数变好而人评没有改善，不应继续加大同一个 reward 的优化。

## 尚未建立的证据

- 这 12 篇论文不能证明中文与英文、technical docs 与 marketing 存在一个统一「AI 味」标量，也不能证明用同一个 reward 可以同时改善四个场景。
- 尚未采集授权语料、做真实人评、校准 judge、测模型或运行训练；文中数字来自各原论文，不是 Plainvoice 实验结果。
- 专业创意评价与一般写作评价可能显著不同。主研究另行覆盖 2025 年 _Creativity Benchmark_ 等营销相关工作，不应只依据 MT-Bench / G-Eval 决定营销 judge。
- 本轮为定向 background research，重点是使第一轮实验不把错误代理指标优化得更好；最终基座、训练方法与成本选择需结合另一份训练调研和实测。

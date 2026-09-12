# 编辑任务、数据来源与行业评测

## 可借鉴的已有工作

这里的文献支持任务设计，不构成已验证的“去 AI 味儿”数据集。文献检索截至 2026-09-12；未下载或重新分发这些数据集。

| 工作 | 原始证据与范围 | 对项目的用途和限制 |
|---|---|---|
| Raheja et al., 2023, **CoEdIT: Text Editing by Task-Specific Instruction Tuning** | 82K 编辑指令；含简化、语气和其他编辑任务。论文明确承认主要覆盖句子级编辑，长文效果待验证，统一提示格式也未充分控制每个模型的提示敏感性。[论文](https://aclanthology.org/2023.findings-emnlp.350/) | 支持训练“输入文本＋编辑要求→改稿”。其历史基线表现不能用来预测今天强模型在中英双语长文上的胜负。已读 PDF 方法、实验与 Limitations。 |
| Du et al., 2022, **Understanding Iterative Revision from Human-Written Text** | IteraTeR 从 Wikipedia、arXiv、Wikinews 收集约 31K 文档修订，并标注编辑意图。后续版本数量不同，应锁定版本。[论文](https://aclanthology.org/2022.acl-long.250/)、[作者代码](https://github.com/vipulraheja/iterater) | 借鉴 edit intent 和多粒度修订；不是营销文案、API 文档或中英混写的现成 gold。后一个版本也不必然在所有维度优于前一个版本。已读方法、语料统计及作者 README。 |
| Rao & Tetreault, 2018, **Dear Sir or Madam, May I Introduce the GYAFC Dataset: Corpus, Benchmarks and Metrics for Formality Style Transfer** | 从 Yahoo Answers 构建正式／非正式平行改写数据。[论文](https://aclanthology.org/N18-1012/) | 可学多种合法改写及独立评价意义保留；正式程度不是自然感，不能把 informal 当作正例。仅核查官方摘要和元数据；实际使用前需读完整协议及数据条款。 |
| Wu et al., 2025, **WritingBench: A Comprehensive Benchmark for Generative Writing** | v4：1,000 条任务，445 中文、555 英文，6 大领域、100 子领域；动态任务 rubric。其 300 个独立任务的人评用于检验 judge。[论文](https://arxiv.org/html/2503.05244v4) | 适合借鉴“任务相关评价”。它研究生成写作，并非改写自然感。writer 用 critic 筛选的合成数据训练，相关评测仍处于相同评价体系，必须加独立人工终测。已读 §§3–4 及附录 D。 |
| Bhat, Browne & Bingemann, 2025, **Creativity Benchmark: A benchmark for marketing creativity for LLM models** | 678 位行业人员作 11,012 次匿名配对比较；100 个品牌；任务为 insights、ideas、wild ideas。LLM judge 与专家排序的一致性较弱且随 judge 变化。[论文](https://arxiv.org/html/2509.09702v1) | 对营销创意，不能直接照搬通用 judge。志愿参与、英语市场人口偏斜、短创意任务和解码设置限制外推；也不测销售转化。已读 §§4–7、9。 |
| Liu et al., 2025, **LLMs for Customized Marketing Content Generation and Evaluation at Scale** | MarketingFM 用产品／搜索上下文、任务串联与规则＋模型评审，报告离线评审及线上广告实验。[论文](https://arxiv.org/html/2506.17863v1) | 强 harness 应包含真实材料；否则训练组获得更多事实会造成不公平比较。广告相关性改善不能直接解释为自然感提升。已读摘要、架构、实验与 human evaluation 部分。HTML 的 “Received 2009” 是异常模板字段，本条采用 arXiv v1 的 2025-06-22 版本日期。 |
| Lin & Ma, 2024, **Generating Attractive and Authentic Copywriting from Customer Reviews** | 利用评论中的体验生成产品文案，同时评价吸引力与忠实性。[论文](https://aclanthology.org/2024.naacl-long.259/) | 提醒“更具体”常依赖更好的输入证据。评论中的体验不可自动推广成产品保证。当前仅核查官方摘要；保留为后续完整阅读候选。 |
| **MCTS: A Multi-Reference Chinese Text Simplification Dataset**, LREC-COLING 2024 | 中文多参考简化数据。[论文与作者元数据](https://aclanthology.org/2024.lrec-main.969/)、[作者仓库](https://github.com/blcuicall/mcts) | 多参考适合验证“可有多个好答案”；简化目标不能替代技术准确或品牌声音。仅核查官方摘要／项目说明；未确认可直接用于目标任务。 |
| Wang et al., 2022, **CCTC: A Cross-Sentence Chinese Text Correction Dataset for Native Speakers** | 面向母语者，跨句纠错；官方摘要说明母语者与学习者错误分布不同。[论文](https://aclanthology.org/2022.coling-1.294/) | 用作中文纠错的相关工作，不能将语法正确当作没有 AI 味儿。仅核查官方摘要。 |

## Ground truth 应分为四类材料

**来源锚点。** 有日期证据的 2022-11-30 之前文本，有助于降低 ChatGPT 辅助写作的混入概率；日期不能证明完全人工写作，也不能证明质量。保留原始发布日期、版本证据、作者／品牌、来源和使用权。网页今天显示的旧日期可能掩盖后续重写，应优先可固定版本的 commit 或档案快照。

**质量锚点。** 母语领域编辑基于同一 brief 和事实材料评价、修改和解释的文本。写作质量有可争议部分，标签应保留分歧和不同可接受版本。不要强迫一条“标准答案”。

**受控对照。** 同一事实包、受众、渠道、长度约束，分别获得人工稿、多模型稿、强提示稿及混合编辑稿。历史作品无法保证重建出其真正 brief，应将此类重建样本单独标记，避免与前瞻性任务混为一谈。

**反事实最小对。** 单独改一个现象：空洞对比、删除关键条件、捏造数字、过度加标题、同义词替换术语、合理对比、必要重复。最小对用于检查 judge 是否理解功能；主测试仍使用真实完整文档，防止只会解人造练习。

## 数据获取优先级

| 来源 | 获取方式 | 质量与使用权处理 |
|---|---|---|
| 新委托的中英领域编辑 | 围绕相同证据包，从零写或改稿 | 明确记录 AI 辅助情况、编辑理由、训练及再分发许可；这是最贴合目标的 gold 候选 |
| 自有且获授权的旧文案、旧文档及版本差异 | 按作者／品牌／项目成组导入 | 不自动访问公司材料；真实采用前单独确定哪些内容允许进个人仓库和训练集 |
| 开源项目历史文档 | 选择许可明确的文档路径，固定 commit 和时间 | 文档许可未必等于代码许可；保存每个来源的使用条件，审核修订质量 |
| 历史营销网站／广告档案 | 先建链接和元数据清单 | “公开可读”“年代久远”不等于已获训练或再分发许可；本轮不复制全文入库 |
| 公开编辑／简化数据集 | 依任务用途筛选小样本，核实版本与条款 | 作为辅助训练或 sanity check；不把它们命名成已验证的去 AI 味儿数据集 |

## 需要避免的数据捷径

随机按段落切 train/test 会泄漏作者风格、同一文档事实和品牌语言。先按 source family 分组，再切分，再生成变体；翻译、同题不同模型稿、同一次 campaign、相邻版本必须同组。公开历史材料也可能出现在基座预训练中，因此测试集需要相当比例的新委托材料。

从优秀人工稿合成“坏稿”再训练反向恢复，可以提供便宜的局部监督，但容易学到特定破坏器的习惯。此类数据必须单独标记，限制占比，终测使用真实模型原生缺陷和真实用户草稿。给每个模型相同事实包，防止模型组因为缺材料而输给原作者。

中文与英文需分别原生写作、原生标注；翻译对只作额外一致性测试。中文不应因使用排比就扣分，英文不应因正式语气或非母语措辞就扣分。所有“AI 特征”都需要语境中的功能证据。

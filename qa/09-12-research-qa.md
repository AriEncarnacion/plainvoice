# 研究覆盖与核验记录

本轮为有针对性的背景研究，不是 PRISMA 式系统综述。检索截至 2026-09-12；语料、人评、模型训练及真实 benchmark 均未执行。研究覆盖中英双语与技术／营销四个同等优先单元。

## 证据范围

四份文献备忘录合计列出 40 项论文／数据集研究，以及 5 个官方模型卡和发布佐证。重心包括语言学风格与同质化、AI 来源检测及偏差、编辑与风格迁移、人类／LLM 评价、参数高效训练、偏好优化和行业写作实验。

同日 follow-up 增加 literature-first 导读，并补齐首轮弱覆盖的 direct humanization prior art：DIPPER、HUMPA、CoPA 三篇论文，以及单列证据级别的社区 Unslopper model card。CoPA 的人评表和 Unslopper 的质量表已回读，明确相对原稿与相对弱 baseline 的不同结论；没有据此宣称已复现效果。

原始来源主要为 ACL Anthology、arXiv 作者版本、PNAS、Nature、Science Advances、ICML/ICLR 及出版社正文。模型配置来自发布者组织的模型卡与官方发布说明。搜索中的商业宣传、社交帖子及二手解读不承担结论证据。

每份备忘录记录了阅读范围和限制；部分数据集只核查官方摘要与元数据，未伪称完整复现。所有文献分数属于论文指定模型、任务和人群，不属于 Plainvoice。部分 2026 研究尚为 preprint，或正式版与作者版阅读范围不同，已注明。

## 检索方向

- AI writing style / AI-ese / grammatical and rhetorical variation / lexical overrepresentation / homogenization。
- Human and LLM judge bias / non-native detection bias / RAID / M4 / style transfer evaluation / factual preservation。
- Text editing instruction tuning / CoEdIT / IteraTeR / Chinese revision and simplification。
- WritingBench / marketing creativity / copywriting / technical writing evaluation / real marketing experiments。
- LoRA / QLoRA / DPO / online preference coverage / reward overoptimization / current official model cards。

## 重要校正

1. 句法密集与有效信息不足可以共存，不互相矛盾。
2. 历史人工来源不自动等于高质量；AI 来源判别不能当作质量标签。
3. Base/instruct 对照未能隔离 SFT、RLHF 或其他具体后训练因素，不能作单因素因果归因。
4. 中文“不是，而是”过用在本轮没有找到足够直接实证，保留为待验证产品假设。
5. Wine Access 的定制小模型和 prompted Claude 位于不同实验轮次，不能当成训练与 prompting 的受控消融。
6. FActScore 类 precision 不覆盖必要信息 recall；embedding 相似度也不足以证明无立场漂移。
7. 模型卡提供存在性、结构及许可信息，不能证明所荐规模在该任务最优；Qwen 的 LM 参数不是完整多模态 checkpoint 的总存储。
8. 显存表区分权重理论下界与实际设备规划；价格示例为假设敏感性分析，没有采购报价或已发生支出。
9. 各备忘录的量表、学习曲线及 arm 编号是研究选项；统一执行版本在主方案与标注协议，入口已标明。

## 独立方法复核

对主方案另做一次独立 review，发现并补齐三处规则：

- 双方失败、无法判断、缺评、空输出、评审无多数与事实争议的处理，保留全部任务分母；未决标签用上下界，不能删除。
- 每格非劣界限与重大错误上限需在终测前确定；未发现显著退化不能解释成已证明非劣。
- 一致性统计只使用裁决前独立原始评分，不能混入只评价分歧的裁决人。

复核了 800 项 × 3 人 × 3–5 分钟 = 120–200 小时的标注估算；确认 n=200/格并不足以支持很窄的效果或低错误率承诺。费用与样本量仍需 pilot 校准。

## 尚未建立的结果

Ground truth follow-up 核查 AdParaphrase v2.0、IteraTeR、arXivEdits、MCTS、ASSET 和 CoEdIT 的作者入口，新增独立采集方案。区分了广告释义／偏好与 AI 味标签、人工编辑与自动标签、论文使用规模与实际公开规模。MCTS 完整数据许可本轮未核实；CoEdIT 82K 为论文规模，公开 train 约 69K。未下载整套语料，未把提议的 80 项采集方案计作已采集 gold。

采集方案经独立方法复核：80 项、四格各 20、两人初评共 160 次 pair 评审的算术成立；明确补入 DPO chosen 必须通过约束，平局、两稿均不合格和未解决的 uncertain 不直接转成普通 DPO 胜负标签。

没有可信依据宣布一个模型或训练方法在四场景胜出，也没有经过校准的统一“AI 味”分数。没有获取历史营销文案的批量训练许可，没有采集公司资料，没有下载训练权重或启动付费计算。当前仓库是可继续执行的研究起点。

Markdown 内部链接、文件清单和 Git 提交差异在推送前检查。只有本项目原创研究文档与模板进入个人仓库，未纳入父级管理工作区文件。

# 桌面数据包与第一次改写采样

2026-09-12。用户明确要求下载到桌面；原始数据和文章副本保存在 `~/Desktop/plainvoice/data/local/`，没有上传此 Git 仓库。以下是实际完成记录，区别于先前的采集建议。

## 已下载六套公开数据

`datasets/` 共 105 个文件、610,783,737 bytes（约 611 MB，含 IteraTeR 压缩包与解压数据）。六套均取得本次选定的完整公开数据文件，无因体积而截取的 partial 文件；作者未公开或另外受限的版本不包括在内。

| 来源 | 本地实测规模 |
|---|---|
| [AdParaphrase v2.0](https://github.com/CyberAgentAILab/AdParaphrase-v2.0) | main 22,337 对，其中 16,460 对通过等价多数票；pt 8,721 三元组 |
| [IteraTeR](https://github.com/vipulraheja/iterater) | FULL 196,987 句对／31,631 文档修订；HUMAN 4,018 句对／559 文档修订 |
| [arXivEdits](https://github.com/chaojiang06/arXivEdits) | 751 论文组、1,790 版本；1,000 人标句对 |
| [MCTS](https://github.com/blcuicall/mcts) | 723 原句 × 5 人工参考；691,474 机器构造句对 |
| [ASSET](https://github.com/facebookresearch/asset) | 2,359 原句 × 10 人工参考 |
| [CoEdIT](https://huggingface.co/datasets/grammarly/coedit) | train 69,071；validation 1,712 |

原始 README、许可文件或数据卡声明、固定 revision、文件 URL、SHA-256、记录数和人工／机器来源均保留在各包 manifest。JSON／JSONL／CSV 解析、平行行数、ZIP CRC 和 104 个清单文件的 SHA-256 检查通过。不同粒度的记录有重叠，不能把表中数字直接相加。

MCTS 之前只读到 Git LFS pointer，本次已获取 GPLv3 LICENSE 正文；这不自动说明全部上游新闻内容的训练权利。IteraTeR Plus/v2 与 CoEdIT 未公开实例没有通过其他渠道补取。下载与结构验证不等于已完成全部来源的训练、再分发用途确认。

## Agentic trace 与 technical writing

`agentic-technical/` 保存单独的来源说明和小样本。研究与字段区别见 [agentic／技术写作数据调查](research/09-12-agentic-technical-datasets.zh-CN.md)。

更贴近工程总结改写的入口是 [NVIDIA SWE-Hero OpenHands trajectories](https://huggingface.co/datasets/nvidia/SWE-Hero-openhands-trajectories)：本次抽取 3 条有可观测工具调用、环境反馈和最终工程总结的轨迹。它们提供可约束改写的执行材料，尚无对应人类改稿。不可把模型叙述的“测试成功”等当作已独立验证的事实，应回查轨迹。

研究报告类数据另分“任务＋专家标准＋AI 报告”“人类参考文章”“同题人类与 AI 报告”。同题不保证内容等价，公开最终稿也不等于公开了完整 action trace。本轮未找到能直接用于本项目的完整“轨迹＋AI 稿＋高质量人类同内容改稿”现成三元组。

## 六份来源与六组已生成的短片段改写

入口为 `human-rewrite-pairs/review.html`。页面并排呈现来源片段与 AI 改写，支持记录是否适合成对、个人偏好、备注以及导出 JSON。它是来源可见的探索性审阅，不是盲评实验。

| 来源 | 发表日期／来源边界 | 本次输入长度 |
|---|---|---:|
| [Howard Marks: How Quickly They Forget](https://www.oaktreecapital.com/docs/default-source/memos/2011-05-25-how-quickly-they-forget.pdf) | 2011-05-25，PDF 署名与日期 | 108 英文词 |
| [Howard Marks: There They Go Again . . . Again](https://www.oaktreecapital.com/docs/default-source/memos/there-they-go-again-again.pdf) | 2017-07-26，PDF 署名与日期 | 119 英文词 |
| [Stripe: Designing robust and predictable APIs with idempotency](https://stripe.com/blog/idempotency) | Brandur Leach，2017-02-22 | 99 英文词 |
| [Stripe: Idempotent requests](https://docs.stripe.com/api/idempotent_requests) | 当前文档，无已确认原始日期或个人作者；不能当作确定的 pre-AI 人类文本 | 104 英文词 |
| [阮一峰：RESTful API 设计指南](https://www.ruanyifeng.com/blog/2014/05/restful_api.html) | 2014-05-22 | 171 汉字／257 总字符 |
| [阮一峰：如何降低软件的复杂性？](https://www.ruanyifeng.com/blog/2018/09/complexity.html) | 2018-09-10；基于 Ousterhout 演讲与书评的中文笔记 | 164 汉字／240 总字符 |

完整官方文件与提取文本在 `sources/`，页码／小节和原文日期证据在各来源 metadata。历史文章保存的是本次下载版本，未与历史网页存档逐字比较。署名与年代也不保证质量。所有六组都保持 `unreviewed_candidate`，原文不预设为 winner。

## 实际生成过程及限制

1. 最初尝试本机 Codex CLI 0.144.6 调用配置中的 `gpt-6-astra`。服务返回“模型要求更新的 CLI”，因此该尝试未产生改写；失败日志单独保留在 `generation-cli-failed/`，没有升级或更改用户配置。
2. 随后通过新的 Codex subagent 生成六组改写，`fork_turns=none`，不继承本任务的前文讨论；输入为六个短片段，指令要求用自己的结构与措辞改写并保留事实，没有禁用词表或“故意增加 AI 味”的要求。
3. 子智能体的原始六组输出直接保存，主 agent 没有再次润色。实际 prompt、输入、响应、运行说明在 `generation/`。输出 ID／数量、原文片段一致性和少量技术标识符通过机械检查；没有把机械检查当作语义等价或人评通过。

限制：六段在同一任务中生成，仍受 Codex 系统／开发者指令影响。返回工具元数据没有提供精确 backend checkpoint、token 用量或费用，运行记录写明未暴露，没有伪填。此次短文本生成不是完整 agent 工具轨迹。它只能探索词句与段落节奏，不能证明整篇文章的论证、结构或技术完整性。

这批材料尚未经过独立人评，也没有训练 judge 或 rewrite 模型。好原文经模型重写不一定变差；评审应允许模型胜、平局和内容变化。人工认可的 pair 才进入下一步标注与用途划分。

## 可复用辅助脚本

- `scripts/build_rewrite_review.py`：用本地 `pairs.json` 构建无外部依赖的审阅 HTML。
- `scripts/run_rewrite_pilot.py`：记录 prompt、结构化输出与运行状态的 CLI 采样助手。本机旧 CLI 的尝试失败，不能将该路径报告为本轮成功生成器；实际成功路径是上文的隔离 subagent。

第三方原文、改写内容、下载语料及运行日志仅保存在本地数据包；此 Git 仓库保存原创研究说明与辅助脚本。

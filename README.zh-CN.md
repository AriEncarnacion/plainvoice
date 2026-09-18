# Plainvoice

[English](README.md) · [简体中文](README.zh-CN.md)

研究如何让内容改写更自然、更有信息价值，同时保留事实、用途和作者声音。中文、英文以及 technical docs、marketing 四个场景同等优先。

当前阶段：背景研究、数据采集和内容改写试验。最新用 Gemini Flash-Lite 保存 848 条候选与诊断输出，包含完整文章、句段、模型比较和早期诊断；均采用内容抽取后乱序成文。没有已训练模型、已验证 judge、真实 benchmark 分数或经独立人评确认的 gold。

## 本地目录与启动

2026-09-15：完整 Git 仓库迁至 `~/Desktop/plainvoice`，保留原有 Git 历史及 `origin`。代码在 `scripts/`，文献调研在 `research/`。原桌面数据包已移入 `data/local/`，该目录整体由 `.gitignore` 排除；`data/README.md` 继续纳入版本管理。

双击仓库根目录的 `Open Plainvoice Viewer.command`，或在仓库目录运行：

```bash
python3 scripts/serve_data_viewer.py --database data/local/data-viewer/review.sqlite
```

浏览器打开 <http://127.0.0.1:8876/?view=clean>。历史数据和 QA 中的旧绝对路径保留为采集时的 provenance；查找对应文件时，把 `~/Desktop/plainvoice-data-2026-09-12/` 替换为本仓库的 `data/local/`。

## 从这里开始

- **[全库正文清理](09-12-text-cleaning.zh-CN.md)**：统一原文／AI 格式、正文导出、原始版本切换与质量隔离。

- **[统一 Data Viewer](09-12-unified-data-viewer.zh-CN.md)**：全部 1,247,891 条本地记录、28 个分组，支持全文对照、筛选、参考答案、trace、评审导入导出。[本机入口](http://127.0.0.1:8876) 需要先启动资料库；[网上入口](https://plainvoice-data-review.jason62-h.chatgpt.site) 提供来源目录与获许可的示例，访问受 Sites 账户权限控制。
- **[双语 AI 候选补全与模型对照](09-12-low-cost-ai-enrichment.zh-CN.md)**：新增数量、来源覆盖、实际费用、缺项及语义 QA；先在本机 viewer 的新分组审阅。
- [全文重写 v2：内容抽取、乱序与独立成文](09-12-article-reconstruction-v2.zh-CN.md)：最新方法、六篇来源、完整性与结构变化的局限，以及可复用的 prompts 和脚本。桌面最新入口为 `human-rewrite-pairs/article-v2/review.html`。
- [桌面数据包与第一次改写采样](09-12-local-data-and-rewrite-pilot.zh-CN.md)：已下载数据、agentic／技术写作样本，以及可逐组审阅的六个改写候选。
- [Existing literature：研究脉络与最相关论文](research/09-12-literature-review.md)：先看已有研究做了什么、发现什么、哪些问题仍未解决。
- [直接相关的 humanizer prior art](research/09-12-humanization-prior-art.md)：DIPPER、HUMPA、CoPA 和社区 Unslopper；区分检测器指标与写作质量。
- [Ground truth 获取方案](09-12-ground-truth-acquisition.zh-CN.md)：已核查数据集、真实模型稿与人工编辑、盲评和 80 项采集 pilot，以及 SFT／DPO 数据形状。
- [研究结论与实验方案](09-12-research-and-experiment-plan.zh-CN.md)：批判性审视 ground truth、evaluator、训练方法、模型规模与实验成本。
- [风格与行业文献](research/09-12-style-literature.zh-CN.md)：AI 味儿的语言学证据、反证、中文和行业边界。
- [评价文献](research/09-12-evaluation-literature.zh-CN.md)：检测器、人工评价、judge bias 和保真。
- [训练文献](research/09-12-training-literature.zh-CN.md)：SFT、LoRA/QLoRA、DPO、RL 与模型候选。
- [数据与任务文献](research/09-12-data-and-task-literature.zh-CN.md)：编辑数据集、写作 benchmark 及 ground truth 来源。
- [标注协议](09-12-annotation-protocol.zh-CN.md)、[baseline 提示模板](prompts/README.zh-CN.md)、[数据约定与示例](data/README.zh-CN.md)。
- [研究覆盖与核验记录](qa/09-12-research-qa.zh-CN.md)。

## 下一次实验

先完成每个场景 20 项、共 80 项的人工 rubric pilot。用人类分歧修订评价标准，再比较强 prompting／harness，然后决定是否训练。最终 success 由独立人工测试和实际用途决定，AI 检测分数只可作为研究诊断。

## 工作约定

文献事实、作者报告结果、本项目推论和实验建议必须区分。新增结果要注明模型 checkpoint、数据 split、提示版本、随机种子、全部调用成本和限制。不能把示例、自动标签或文献中的分数写成项目实测。

第三方原文与数据只在逐项核实使用权后导入；本轮只保存研究笔记、链接和原创演示。个人项目不自动获得公司资料的使用权。原始数据及未来模型产物保持独立目录并默认不进入 Git。

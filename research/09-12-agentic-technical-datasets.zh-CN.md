# Agentic trace 与技术写作：公开数据核查及小样本

核查日期：2026-09-12。目标是寻找 AI 文本、可验证的任务/执行证据，以及高质量人类写法之间的可配对材料。本轮阅读官方论文、作者仓库和数据卡，并检查实际样本字段；未运行生成模型、训练或重放软件环境。

**结论：已经取得可观测工具轨迹和最终工程总结，也找到一个已核实同一 prompt 的 AI 报告—人类参考文章对；没有找到可直接称为「同内容、事实不变、真人精修 AI 初稿」的现成 gold 数据。** 工具轨迹最合适的入口是 NVIDIA 的 SWE-Hero；研究报告可先看 DeepResearch Bench II 与 CogGen。代码注释数据更接近技术文档，但人类来源和质量仍需逐条核查。

数据实际保存在用户指定的桌面目录：`~/Desktop/plainvoice/data/local/agentic-technical/`。`source-manifest.json` 记录来源、revision、选样、许可说明和文件校验；第三方正文仅保存在桌面，不纳入本仓库。

## 1. 先区分四种“配对”

| 类型 | 能回答的问题 | 不能直接推出什么 |
|---|---|---|
| 同一个 topic 的真人文章与 AI 文章 | 文体差异的探索 | 信息量、事实、目的和长度受控 |
| 同一个 task/prompt 的两份文章 | 相同需求下的整体输出质量 | 两份文章表达同一组事实；真人稿是在修订 AI 稿 |
| 同一份 code/brief/evidence 下的人与 AI 输出 | 有共同事实依据的生成质量 | 已获得事实完全等价的改写偏好 |
| AI 初稿及真人精修稿，附事实核验 | 改写 SFT / DPO 所需目标 | 每一次人类改动都一定更好 |

另一个独立维度是 trace。带 `assistant.tool_calls` 与对应 `tool` observation 的日志是可观测交互记录；模型叙述“我检索了……”或 `thought` / rationale 字段不是工具确实执行的证据。数据导出的 message history 也不保证包含所有重试、环境状态、隐藏过程或可重放依赖。

## 2. 优先查看的实际样本

| 数据 | 桌面已取得 | 配对与 trace 级别 | 优先用途 |
|---|---|---|---|
| **SWE-Hero / OpenHands** | 3 条轨迹；分别 143、145、117 messages；各自保留最终 assistant turn、`finish.message` 和 `model_patch` | 可观测 actions / observations + final 工程总结；没有真人修订 | 给最终总结建立执行证据约束，再收集真人精修 |
| **DeepResearch Bench II** | Software Development 的 idx 41–50：中文 5、英文 5；10 份 Doubao 最终报告；对应任务、rubrics、人类来源文章链接 | 同任务 AI 报告 + 专家来源标准；本包没有人类来源文章全文，也没有 trace | 中英技术研究报告的事实与风格分离评估 |
| **CogGen / OWID** | 20 篇人类参考正文及 task；2 篇官方 AI 示例；其中 deforestation 已核实 query 逐字相同 | **1 个 exact-same-task AI—human reference pair**，不是 same-content rewrite；没有发布的完整 trace | 最直观的 AI / 人类研究写作比较起点 |
| **STORM / FreshWiki** | 10 篇技术、科学和相关商业百科文章，保留正文、来源 URL、references | 人类参考池；官方发布物未找到对应 AI 输出/轨迹 | 内容卡与人类参考的探索性构造 |
| **Code2Doc** | test 前 20 行：Java 10、Python 8、TypeScript 2；代码及原有文档 | 同一代码对应已有 docstring；无 AI 对照、无真人修订链 | 技术文档来源池；需补版本/作者核验和新对照 |
| ResearcherBench（补充） | 前 10 个问题、专家 rubric、Claude 回答，按 id 对齐 | 同任务 AI 回答 + 专家标准；没有真人参考文章或 trace | 技术问题的保真评估与 AI 初稿来源 |

这些是可阅读的探索性样本，不是代表性 benchmark。除 DRB II 的 5+5 双语任务外，本轮可用内容主要是英文，也没有 marketing 与 technical 四格平衡；不能代替主方案的分层采样。

### SWE-Hero：真实执行轨迹与 final 都有，适合继续收集精修

[NVIDIA 官方数据卡](https://huggingface.co/datasets/nvidia/SWE-Hero-openhands-trajectories)说明该数据使用 OpenHands 与 Qwen3-Coder-480B-A35B-Instruct，发布 34,269 条轨迹、11,766 个 issue。issue 来自 SWE-Gym、R2E-Gym 与 SWE-rebench，其中部分问题描述也是合成的。[技术报告](https://arxiv.org/abs/2604.01496)为 *From SWE-ZERO to SWE-HERO: Execution-free to Execution-based Fine-tuning for Software Engineering Agents*（Ludwig、Ahmad、Majumdar、Ginsburg，2026）。

本包使用 HF rows API 下载前 3 条，均是 pandas 任务；API `truncated_cells` 为空。实际可见 `execute_bash` 等工具调用、环境回显、最终 `finish` 调用及其总结文本。最后一轮单独放在 `traces/swe-hero-openhands/samples/row-*.final.json`，方便先读；完整记录在 `trajectories.3.jsonl`。

限制：没有真人同内容修订；轨迹中的 assistant 文本不一定都是对用户可见的执行更新。`model_patch` 不等于经过本轮验证的正确补丁，final 中“成功”“全部正常”等宣称也尚未逐条与日志对照。本轮仅检查字段、结束状态和 API 是否截断，没有重跑测试。数据卡声明 CC BY 4.0，同时各行保留源仓库许可；这 3 行是 BSD-3-Clause。

### DeepResearch Bench II：标准来自专家文章，文章正文并不在任务文件里

[作者仓库](https://github.com/imlrz/DeepResearch-Bench-II)与[论文](https://arxiv.org/abs/2601.08536)介绍 132 个任务、9,430 条 rubrics。实际 `tasks_and_rubrics.jsonl` 的 `content` 包含 `task`、`rubric`、`blocked`；后者保存来源标题、作者与 URL，并不是原文正文。任务要求被测 agent 不读取这篇来源文章；这是 benchmark 构造的一部分，不是人类编辑 AI 初稿的记录。

本包的 10 个 task 与 [HF 官方模型报告发布](https://huggingface.co/datasets/muset-ai/DeepResearch-Bench-II-Dataset)中 `Doubao-DeepResearch/idx-*.md` 按 idx 对齐，覆盖低代码、强化学习、Kubernetes 调度、可观测性、视频编码与云扩缩容等。抽查 idx 41/42 的正文标题与任务对应；未对全部语义、引用与指标作质量标注。

许可必须分开：仓库代码 Apache-2.0；任务/rubrics 使用逐条来源许可。作者当前 `DATA_LICENSE` 写明 129 条 CC BY 4.0、idx 26/110 为 CC BY-NC 4.0、idx 119 为 CC0。本次 41–50 均为 CC BY 4.0。HF 模型报告卡另标 Apache-2.0，不能用它覆盖人类来源文章的许可。

### CogGen：一对确实同 prompt，但内容仍未受控

[作者仓库](https://github.com/NJUNLP/CogGen)与[数据卡](https://huggingface.co/datasets/tk1111/coggen-benchmark)将 50 篇 OWID 报告列为人类专家参考，保留作者、日期、来源 URL、Markdown 正文。另有 20 篇 WildSeek 参考由 Gemini Deep Research 生成；**后者不能当作人类 ground truth**。

本次保留 OWID main_001–019，加 main_033。`global_deforestation/config.json` 中的 query 与 `owid_main_033` query 逐字相同，后者通过 `source_report_id` 对应 OWID 人类文章；配对文件为 `coggen/samples/deforestation.same-task-pair.json`。这验证了同任务来源，未验证 AI 与人类稿的事实覆盖相同，也不代表人类看过/修改过这份 AI 稿。另一个 oil/gas IoT 示例只有 AI 稿；未伪造人类配对。

作者代码能生成日志、上下文池等文件，不等于这些完整轨迹已经发布。当前仓库内查到的是两个最终报告示例与 config。OWID 文字数据卡标 CC BY 4.0，原始作者/链接保留；第三方图表和数据许可需独立处理。本次未下载图像，只保留文字内已有 URL。

### FreshWiki 与 Code2Doc：适合作为原始材料，不直接当偏好金标

[FreshWiki 数据卡](https://huggingface.co/datasets/EchoShao8899/FreshWiki)发布 100 篇英语 Wikipedia 文章，采样关注 2022-02 至 2023-09 的高编辑量页面。[STORM 论文](https://aclanthology.org/2024.naacl-long.347/)研究从主题到长文章的流程。10 篇样本有 `title/url/summary/content/references` 等字段。主仓库、论文存档分支与 HF 文件清单未找到这些参考对应的公开生成结果或 conversation log；该结论限于本轮检查的发布物。文本 CC BY-SA 4.0，不能沿用 STORM 代码 MIT。文章发布日期/历史窗口也不是未经机器辅助的作者身份证明。

[Code2Doc 数据卡](https://huggingface.co/datasets/kaanrkaraman/code2doc)宣称 13,358 组代码—文档对，覆盖五种**编程语言**。[论文](https://arxiv.org/abs/2512.18748)的质量与 AI 来源过滤依赖启发式；没有为本项目提供经过人类核验的“无 AI”身份标签或“去 AI 味儿”胜负标签。现有字段包括 repo、文件路径、行号、代码、文档、quality_score，但不是历史修改链。数据卡 CC BY 4.0 与原仓库 MIT/Apache/BSD 的归属仍应一起保留。随机按行拆分还可能让同 repo/风格泄漏到测试集。

## 3. 其他核查对象与排除原因

| 对象 | 核查结果 | 对本项目的意义 |
|---|---|---|
| [WildSeek](https://huggingface.co/datasets/YuchengJiang/WildSeek) | 官方数据点是 topic + 用户 goal；独立发布物不是真人文章/AI 报告/轨迹集 | 需求分布参考；不要把“真实用户需求”误当“真人写作” |
| [ResearcherBench](https://github.com/GAIR-NLP/ResearcherBench) | 65 个前沿 AI 研究问题；Claude 辅助提炼 insights，再由专家构造加权 rubrics；公开多系统最终回答 | 有专家评价标准，不等于 65 篇真人高质量文章。检查的 revision 未找到 LICENSE，训练/再分发权限未验证 |
| [DeepResearch Bench I](https://github.com/Ayanami0730/deep_research_bench) | 100 个研究任务、criteria、reference 与模型最终报告文件；本轮未建立 reference 的逐条人类写作证据 | 可作评测设计参考，不能仅凭文件名 reference 推断 gold 人类稿 |
| [ReportBench](https://github.com/ByteDance-BandAI/ReportBench) | 由专家综述构造研究需求与参考依据；公开任务和 citation ground truth | 人类参考与生成任务的内容范围仍需对齐；没有找到现成的人类精修 AI 稿或全轨迹三件套 |
| [Meta DocAgent](https://github.com/facebookresearch/DocAgent) | 多 agent 代码文档生成方法；公开代码/小型示例，采用自动检查与 LLM 评价；[论文](https://arxiv.org/abs/2504.08725)讨论缺少 gold reference | 方法相关，未发现可直接下载的高质量人类—AI 改写对；注意与同名多模态 DocAgent 区分 |
| [CodeSearchNet](https://github.com/github/CodeSearchNet) | 代码与已有函数注释的数据和收集方法 | 原始技术文档来源池，无现成 AI 对照、真人修订标签或 workflow trace |

### SWE-smith：额外下载 3 条，保留为数据 QA 反例

[官方 SWE-smith 发布](https://huggingface.co/datasets/SWE-bench/SWE-smith-trajectories)的 tool split 前 3 条确实有 49/43/65 条消息、工具调用和 observation，以 `submit` 结束；无 API 单元格截断。但是 `patch` 两条为空，另一条 `instance_id` 为 apispec 而 patch 路径为 `flashtext/keyword.py`。这是本地抽查发现的**疑似对应异常**，不能由这 3 行推断整个数据集失效，也不能将此列直接当正确最终补丁。

[官方转换代码](https://github.com/SWE-bench/SWE-smith/blob/main/swesmith/train/traj_mgr/utils.py)还明确说明 message history 的导出近似，部分 blocked-action requery 未完整保存。下载的 `tool` 表保留工具结构，比把 rationale 文本当轨迹可靠，但仍不能称作环境全部事件的无损记录。故本轮 trace 首选 SWE-Hero，SWE-smith 仅保留于 `traces/swe-smith/` 供检查。

## 4. 如何补成真正适合 rewrite 的数据

1. **最终工程总结路线**：从 SWE-Hero 的 final 和可观测 trace 出发。先提取实际改动、实际执行测试及结果、未解决限制的 evidence packet；让工程师在相同 packet 下修订原 final。严格区分日志支持的事实与 agent 自述成功。保留 code/tool/action/observation 不变，改写仅作用于指定的对用户可见文字。
2. **技术研究报告路线**：从 DRB II 的中英任务及 AI 初稿出发，另外核对来源/事实后请研究编辑精修。CogGen 的 same-task pair 可帮助讨论风格，但不能直接把两篇全文放入 chosen/rejected：信息差和覆盖差尚未控制。
3. **技术文档路线**：固定 repo commit、代码与上下文，保留既有文档并生成 AI 对照；请维护者/技术作者在相同代码证据下选择或修订。Code2Doc 的启发式 quality_score 不作为最终权重或来源金标。
4. **标注与切分**：先 factual pass/fail/uncertain，再比较信息密度、可操作性、语气与重复；两者都保真时才形成风格 DPO pair。人类精修且复核通过的目标可用于 SFT。按 repo/项目/文档家族/原任务划分 train/dev/test，多个 trace、语言版本和段落必须跟随母任务。

本轮桌面样本尚未经过上述人工精修与事实核验，所以只标 `candidate/source/example`；不赋予 `human_preferred`、`style_gold` 或 `same_content` 标签。

## 5. 复现与阅读覆盖

- GitHub README、许可证和数据文件采用获取时解析的 commit；HF README 与可直接下载文件采用 dataset revision。详见两个 manifest。
- Code2Doc、SWE-Hero、SWE-smith 使用 HF rows API 的有界请求。实际响应和 SHA 留在本地；API 行视图未证明与同时下载的数据卡 revision 完全一致，因此记录为访问时快照。
- 实际验证了 JSON/JSONL 可解析、样本数、3+3 条 trace 的 tool 与结束状态、API 无截断、CogGen 一个 query 完全相等、DRB II 10 条任务中英 5+5，以及文件哈希。没有执行第三方代码、回放环境或作全量语义质量判断。
- 阅读程度：STORM/Co-STORM、ResearcherBench、DRB II、DocAgent、Code2Doc 阅读论文相关方法/局限与官方发布说明；CogGen、ReportBench、DRB I、CodeSearchNet 以作者发布说明/文件结构为主；新增 SWE-Hero 以官方数据卡及真实行记录为主，SWE-smith 另读官方 export 函数。未据此声称完成各论文全文复现。

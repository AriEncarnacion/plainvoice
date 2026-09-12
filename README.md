# Plainvoice

研究如何让内容改写更自然、更有信息价值，同时保留事实、用途和作者声音。中文、英文以及 technical docs、marketing 四个场景同等优先。

当前阶段：背景研究和实验设计。没有已训练模型、已验证 judge、真实 benchmark 分数或可直接训练的 gold 数据。仓库内的门槛和规模均为待验证建议。

## 从这里开始

- [Existing literature：研究脉络与最相关论文](research/09-12-literature-review.md)：先看已有研究做了什么、发现什么、哪些问题仍未解决。
- [直接相关的 humanizer prior art](research/09-12-humanization-prior-art.md)：DIPPER、HUMPA、CoPA 和社区 Unslopper；区分检测器指标与写作质量。
- [Ground truth 获取方案](09-12-ground-truth-acquisition.md)：已核查数据集、真实模型稿与人工编辑、盲评和 80 项采集 pilot，以及 SFT／DPO 数据形状。
- [研究结论与实验方案](09-12-research-and-experiment-plan.md)：批判性审视 ground truth、evaluator、训练方法、模型规模与实验成本。
- [风格与行业文献](research/09-12-style-literature.md)：AI 味儿的语言学证据、反证、中文和行业边界。
- [评价文献](research/09-12-evaluation-literature.md)：检测器、人工评价、judge bias 和保真。
- [训练文献](research/09-12-training-literature.md)：SFT、LoRA/QLoRA、DPO、RL 与模型候选。
- [数据与任务文献](research/09-12-data-and-task-literature.md)：编辑数据集、写作 benchmark 及 ground truth 来源。
- [标注协议](09-12-annotation-protocol.md)、[baseline 提示模板](prompts/README.md)、[数据约定与示例](data/README.md)。
- [研究覆盖与核验记录](qa/09-12-research-qa.md)。

## 下一次实验

先完成每个场景 20 项、共 80 项的人工 rubric pilot。用人类分歧修订评价标准，再比较强 prompting／harness，然后决定是否训练。最终 success 由独立人工测试和实际用途决定，AI 检测分数只可作为研究诊断。

## 工作约定

文献事实、作者报告结果、本项目推论和实验建议必须区分。新增结果要注明模型 checkpoint、数据 split、提示版本、随机种子、全部调用成本和限制。不能把示例、自动标签或文献中的分数写成项目实测。

第三方原文与数据只在逐项核实使用权后导入；本轮只保存研究笔记、链接和原创演示。个人项目不自动获得公司资料的使用权。原始数据及未来模型产物保持独立目录并默认不进入 Git。

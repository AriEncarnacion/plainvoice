# 全库正文清理

全库覆盖 **1,247,891 条记录／28 组**，其中 **214,048 条、397,342 个文本字段**发生格式变化。860 条改写实验中，600 条为待人评候选、260 条隔离；其他记录保留原任务含义。核验见 [QA](qa/09-12-text-cleaning-qa.zh-CN.md)，清理前后计数见 [长度对比](research/clean-text-2026-09-12/length-comparison.zh-CN.md)。

原始数据保留不动，统一生成 `clean-text-v1` 派生库。原文、AI 改写和所有参考答案使用同一套规则；来源、作者、日期、许可、任务说明、模型及 QA 保留在正文外。没有调用模型或重新生成句子。

## 查看与下载

[本机 viewer](http://127.0.0.1:8876/?view=clean) 默认显示清理后的 A/B 正文。详情的「文本版本」可切换原始采集／生成稿，「清理记录」显示删掉的内容、原因和待复核问题。左侧可筛选改写候选、已隔离记录和其他原始任务。单条可下载当前所见正文。

完整文件位于桌面 `plainvoice/data/local/clean-text-v1/`：

| 文件 | 用途 |
|---|---|
| `review.sqlite` | 全量清理文本、原配对角色、来源、模型和审计记录 |
| `text-only/*.jsonl.gz` | 按 28 个分组导出全部记录，字段为 `id,a,b,references` |
| `rewrite-candidates.jsonl.gz` | 未触发隔离规则的 source/AI 改写候选，仍待人工评审 |
| `quarantined-rewrites.jsonl.gz` | 失败、语义或格式问题需要处理的 source/AI 记录 |
| `metadata.jsonl.gz` | 按 ID 对应角色、语言、许可、原始／清理 hash、候选状态及原因 |
| `format-flags.jsonl.gz` | 全库带格式警告或隔离原因的记录；按 ID／clean hash 连接正文，包括清理后为空的警告 |
| `summary.json`、`qa/` | 全量计数、规则指纹、精确删除与缺陷范围 |

模型输入只取正文列。`id` 用于连接元数据，不拼进训练文本。`null` 表示未配对，空字符串可能是有效的插入／删除编辑，不能互换。多参考答案保留原来的顺序和角色。

## 清理范围

- 移走明确的 YAML 元数据、文档标题副本、署名日期、面包屑导航、引用／转载说明及空页尾。
- 去掉普通 Markdown／HTML 排版、装饰分隔线、图片标签；保留链接的可读文字以及有技术含义的 URL。
- 规范 HTML entities、Unicode、空白和正文标点间距；针对 PDF 来源保守连接段内硬换行。
- 对已经被 AI 改写成普通句子的网页元数据，使用原文 SHA 和唯一精确片段删除；每一处留有审计。混入实质内容、无法仅靠删除解决的句子保留并隔离。
- OWID 下载快照含孤立脚注锚点、未附尾注正文：移除这些网页编号，保留研究归属和年份，并标记来源缺少尾注。没有补造引用。

代码、API endpoint、数学表达、科学上下标、单位、否定词、Javadoc、列表顺序和表格结构都属于内容。为保持可重复清理与技术含义，代码围栏、行内代码及公式／表格分隔符有意保留。有效 JSON trace 原样保存，不改造成 prose。arXiv 的 `[MATH]`／`[CITATION]` 保留并标记来源局限。

仍有少量采集层面的歧义：部分 PDF 段落硬换行、`CO 2`／`B 12` 一类科学记号间距，以及缺失公式／引用的占位符。这些不通过猜测修复；相应来源限制保留，具体例子见本地 QA。

不按“copyright”“cookies”等单个词删除段落，不任意去重正文，不修复事实，不把连写句子或拼写问题猜成新表达。

## 隔离与训练边界

只有明确的改写实验进入候选／隔离导出；其他已发表数据保持原任务语义，不能统一当作 human–AI pair。原文的作者身份沿用来源证据，格式清理不会将其升级为“高质量人类 gold”。

已知失败 stub、中文任务生成英文、确认遗漏、过度压缩、相同文本、原有独立语义缺陷及其他需要复核的诊断单独隔离。数字差异等自动标记可能有合理解释；隔离表示需要处理，并不等于每条都是事实错误。没有自动生成 SFT 的正确答案或 DPO 的 chosen/rejected 标签。

原始 ID 保留，清理后另算内容 hash。旧评审仍对应旧 hash，不会被静默搬到清理后的文本。

## 复现

清理脚本要求 Python 3.11+ 和 SQLite FTS5，只有标准库依赖。精确源文本片段的 sidecar 只在本地数据包中，不公开到 GitHub。

```sh
python3 scripts/clean_data_corpus.py \
  --database "$HOME/Desktop/plainvoice/data/local/data-viewer/review.sqlite" \
  --output "$HOME/Desktop/plainvoice/data/local/clean-text-v2" \
  --removals "$HOME/Desktop/plainvoice/data/local/clean-text-v1/qa/scoped-removals.json" \
  --defects "$HOME/Desktop/plainvoice/data/local/clean-text-v1/qa/scoped-defects.json" \
  --warnings "$HOME/Desktop/plainvoice/data/local/clean-text-v1/qa/review-warnings.json"
```

正文构建后，可单独导出便于训练适配器读取的来源警告：

```sh
python3 scripts/export_cleaning_flags.py \
  --database "$HOME/Desktop/plainvoice/data/local/clean-text-v2/review.sqlite" \
  --output "$HOME/Desktop/plainvoice/data/local/clean-text-v2/format-flags.jsonl.gz"
```

输出目录必须不存在；脚本校验 raw 文件 hash、清理幂等性、全量行数及 SQLite 完整性后才发布派生目录。更新版本可通过 viewer 的 `--clean-database` 参数选择。

后续 `plainvoice_prepare_enrichment.py` 默认优先从清理库准备新队列，并记录清理版本和 raw hash；显式 `--db` 可以复现指定输入版本。旧队列与生成结果不修改。明显损坏的公式／引用占位、维基编辑残留和非正文 trace 会从后续自动改写选样中跳过；其余来源限制随队列保留。

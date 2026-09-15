# 统一 Data Viewer

一个界面审阅本项目已下载、生成的全部可归一化记录。全量正文通过本机 SQLite 索引读取，浏览器按页载入；无需把 1.25M 行一次性装入页面。

## 覆盖范围

| 来源 | 记录数 |
|---|---:|
| 六篇全文改写 v2 + 六组段落改写 v1 | 12 |
| Agentic / technical 本地样本 | 77 |
| AdParaphrase | 31,058 |
| IteraTeR | 230,141 |
| arXivEdits | 219,598 |
| MCTS | 692,197 |
| ASSET | 3,177 |
| CoEdIT | 70,783 |
| 本轮廉价模型 AI 候选与诊断 | 848 |
| **总计** | **1,247,891** |

共有 28 个可筛选分组。记录不是相互独立、已经验证的训练 pair：人类修订、多参考简化、机器合成、同任务报告、偏好标注和未配对文本各自标记。中文、英文、日文均按真实数据标注；AdParaphrase 是日文。单侧样本的 B 栏不伪造答案。

保留完整文本、全部参考答案、任务指令、split、文件与行定位、来源 URL 和许可说明。文章 v2 的内容卡与 QA、真实 trace 的全部事件可展开查看。全量复核发现原库有 2,650 个空目标和 116 个空源文本（空白字符串按空计），分别保留删除／插入语义；62,595 个 null 目标保留为未配对。ASSET 的 4,500 条评分和 2,154 条比较标注按样本合并，未丢弃。3,054 个 IteraTeR HUMAN/FULL 精确重叠与 978 个 arXiv 标注重叠合并并保留来源；22 个未匹配 arXiv 标注单列。

技术样本包括 SWE-Hero、SWE-smith、DRB II、CogGen/OWID、FreshWiki、Code2Doc、ResearcherBench，共 77 条。这里的“全部”指此前实际下载的有界样本，不是这些上游数据集全量。已有训练目录中的 12 个候选副本与段落 v1 文本相同，不重复展示；36 个虚构程序测试夹具不作为研究数据。

新增 AI 对照见 [本轮交付说明](09-12-low-cost-ai-enrichment.md)。共覆盖 839 个目标来源；11 稿附具体语义问题标记，其他稿件也尚未人工验收。默认进入新文章组，旧记录和个人评审不变。

## 审阅方式

最新默认使用[清理后的正文](09-12-text-cleaning.md)。可切换原始版本、查看逐条清理记录、按候选／隔离状态筛选，并下载当前对照文本。原始评审与清理后的评审按内容 hash 分开。

选择数据集，按语言、配对方式、关键词或评审状态筛选。A/B 全文各自滚动，也可同步滚动、调整字号、隐藏来源标签。多参考样本可切换 B。J/K 查看下一条或上一条。查询覆盖标题与对照/参考正文；任务上下文和 trace 的附加 JSON 可在详情查看，未纳入全文搜索索引。

每条可记录保留/修改/排除、表达偏好、内容保真、AI 味比较及备注。标注保存在当前浏览器 localStorage，导出 JSON 后可导入恢复。记录 ID、内容哈希、B 候选编号一起标识评审，文本版本变化不会自动继承旧评审。标签仍是个人判断；隐藏来源标签不等于严格盲评，正文可能透露来源身份。

## 启动完整资料库

需要 Python 3.10+，带 SQLite FTS5；全部使用标准库，无第三方安装步骤。

```sh
python3 scripts/build_data_viewer.py \
  --root "$HOME/Desktop/plainvoice/data/local" \
  --output "$HOME/Desktop/plainvoice/data/local/data-viewer/review.sqlite"

python3 scripts/serve_data_viewer.py \
  --database "$HOME/Desktop/plainvoice/data/local/data-viewer/review.sqlite"
```

打开 [本机全量 viewer](http://127.0.0.1:8876)。首次构建读取所有来源，创建约 2.51 GB 的派生索引；之后直接启动第二条命令。输入文件不被修改。服务器仅绑定 loopback，API 为只读，评审不上传服务器。停止后再次运行启动命令即可。

## 网上入口与公开代码

[网上 viewer](https://plainvoice-data-review.jason62-h.chatgpt.site) 使用同一前端，提供 28 个分组的来源目录，以及一篇具备 CC BY 4.0 依据、完整保留署名的 OWID 示例。它可跳转到当前电脑的完整资料库。网上入口沿用 Sites 默认 owner-only 访问；GitHub 仓库的 public 可见性与 Sites 访问权限是两回事。

GitHub 保存前端、解析器、构建/服务脚本、统计目录和上述许可示例。桌面完整文本、SQLite、原始下载包及个人评审未上传。公开下载并不自动表示适用于任何训练或再分发用途；各记录保留原始权利证据。

公开示例：Max Roser, “Smoking: How large of a global problem is it? And how can we make progress against it?”, Our World in Data, 2021-07-14。[原文](https://ourworldindata.org/smoking-big-problem-in-brief)，[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)。正文来自 CogGen 下载快照，清理版移除网页元数据与排版，未重新改写措辞。署名、原文链接、许可和修改说明保留在来源信息中；不下载或展示外链图片。

核验范围见 [QA 记录](qa/09-12-viewer-qa.md)。

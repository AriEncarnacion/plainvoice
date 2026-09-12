# 全文重写 v2：SVO 内容抽取 → 乱序 → 独立成文

用户要求重做第一轮六篇来源：先从全文抽出 pure content，再由 AI 自行组织语言，评价单位改为整篇文章。原文、内容包、生成结果和对照页面保存在桌面 `plainvoice-data-2026-09-12/human-rewrite-pairs/article-v2/`。本文件记录方法；不把未经人评的结果称为 gold。

## 本次改变

第一轮只给模型开头短片段，直接要求改写。第二轮读取六篇完整文字正文，经过独立的内容表示后再写整篇文章。没有原文长度目标，也没有预设段落数。

1. **抽取全文内容。** 每条命题具有 subject、predicate、object，并保留 qualifiers、attribution、modality、polarity、depends_on。协调者另存 source_locator 和全文覆盖记录。简单三元组不足以表达“在参数相同且原 key 仍保留时重试”之类的限定，不能在拆句时抹掉这些条件。
2. **消除原文组织提示。** 从 writer packet 去掉原文定位、标题元数据、原编号和源顺序。使用固定种子 20260912、HMAC 不透明编号与确定性排序打乱全部命题。真实因果、事件先后、API 操作含义不随机化。
3. **新会话成文。** 每篇由一个 `fork_turns: none` 的 Codex subagent 写作，只给单篇内容包和写作指令。模型自行选择标题、切入点、组织、段落和句子；禁止回看来源、相邻文件或搜索原文。全部限定与独有内容应被表达，文章不带 claim ID。
4. **保留原始输出并审阅。** 输出正文和独立 coverage JSON。协调者不润色正文。机械检查覆盖记录是否齐全，审阅页另问事实、遗漏、组织相似度与综合偏好。

六篇全文抽取了 **579 条命题**。所谓全文是清洗后的完整文字正文；HTML 外链图片未新增转录，PDF 页脚、版权声明、网站导航和评论等非正文有单独排除记录。

| 来源 | 语言 | 命题数 | 范围 |
|---|---|---:|---|
| Howard Marks, How Quickly They Forget, 2011 | EN | 192 | 正文与附言，含表格 |
| Howard Marks, There They Go Again . . . Again, 2017 | EN | 196 | 全文文字，保留历史判断 |
| 阮一峰，RESTful API设计指南，2014 | ZH | 81 | 全文与代码例子 |
| 阮一峰，如何降低软件的复杂性？，2018 | ZH | 40 | 全文 |
| Stripe, Designing robust and predictable APIs with idempotency, 2017 | EN | 46 | 全文与两段实际示例代码 |
| Stripe, Idempotent requests，当前快照 | EN | 24 | 完整 API 文档文字与演示含义 |

## 需要批判性看待的地方

**打乱输入顺序不保证输出结构独立。** Stripe 2017 新稿仍形成“网络失败 → 幂等 → key → 退避”的教学顺序。模型可能从语义关系重建近似提纲。因此须分别评价句式变化和篇章变化；乱序完成本身不是改写成功的证据。

**抽取是有损风险点。** 模型可能在写作前已丢失语气、例外或作者立场。本轮保留来源定位，使错误能够区分为 source → content 或 content → rewrite。命题仍是自然语言，书名、作者自述和历史备忘录名称有时属于内容；这既不是彻底的来源匿名化，也不是已经证实能抹去所有句法痕迹的纯语义表示。

**完整性记录不是保真结论。** 来源单位数量一致、claim ID 全部出现在 coverage 中，只能说明记录对齐。coverage 是生成器自报，不能据此宣布 100% 信息保留。字符数、n-gram 重合与次序逆转比例只是诊断，不是质量、AI 味或语义等价分数。

另一个模型复核了 Stripe 2017 与阮一峰 REST 两篇完整原文、新稿及共 127 条抽取命题，未确认重大遗漏或反转，但记录了两个具体问题：REST 的“列表（数组）”在抽取时变为“列表或数组”，引入轻微格式歧义；Stripe 新稿关于完整回滚的末句可能把充分条件说成必要条件，作为低置信观察项。两项已放在本地审阅页，正文保留原始生成结果。这次模型复核不能外推到其余四篇，也不能代替人评。

**来源本身也有问题。** Howard 2017 文内同一备忘录存在 2007／2008 年份矛盾，需作为未解决项记录。阮一峰 2018 的 Windows／Unix 文件行为按历史来源保留，技术细节没有独立核验。当前 Stripe 文档的作者来源与初始时间未知。旧日期的文章也只是本次下载快照，并未与历史存档逐字校验。

**生成环境有边界。** 新会话防止继承本次对话，并通过读取指令限制来源接触；没有另建 OS 级文件沙箱。部分 writer 根据仓库约定先读取根 README，其不包含这些原文。系统写作指令仍影响结果。工具未返回精确 backend checkpoint、token 或金额，这些字段保持空值；固定 seed 只用于内容包排列，不是生成采样 seed。

**任务与未来部署的分布还不同。** 当前方向是人类文章 → 内容卡 → AI 新稿。它可以提供候选对和检查方法，但未来模型收到的通常是 AI 草稿。人类原文并不必然胜出；需要人工偏好与语义审阅后，才能决定如何进入 SFT 或 preference 数据。

## 文件与复现

- [内容抽取 prompt](prompts/article-content-extraction.md)
- [按内容包成文 prompt](prompts/article-from-content.md)
- [验证并打乱内容包](scripts/prepare_article_packets.py)
- [生成全文审阅页](scripts/build_article_review.py)

```sh
python3 scripts/prepare_article_packets.py \
  --input-dir /path/to/article-v2/content-extraction \
  --writer-dir /path/to/article-v2/writer-packets \
  --audit-dir /path/to/article-v2/packet-audit \
  --seed 20260912

python3 scripts/build_article_review.py /path/to/article-v2/article-results.json
```

准备脚本不调用生成模型。每篇 writer 只获得自己的 packet 和成文指令；输出应保存为 `<packet_id>.md` 与 `<packet_id>.coverage.json`。原始来源、运行输入、覆盖自报和生成记录保存在桌面，不提交仓库。旧的段落实验保留在 `human-rewrite-pairs/review-paragraph-v1.html`。

脚本检查包括 schema、重复 ID、缺失引用、语义依赖环、未覆盖来源单位与固定种子可复现性。页面构建检查全文嵌入、HTML 转义、缺失输入失败及 JavaScript 语法。浏览器交互未完成实际验收；这不是人类写作质量测试。

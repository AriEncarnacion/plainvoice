# Plainvoice 标注协议草案

本文件是第一轮 pilot 的统一协议 v0.1，尚未通过人评校准。与研究备忘录中的备选量表、样本规模或实验臂编号不同之处，以本文件和[主方案](09-12-research-and-experiment-plan.md)为准。真实实验开始前冻结新版本，禁止用测试结果反向改规则。

## 评审所见内容

语言、地区／受众、领域、渠道、任务、原稿、可用事实材料、不可丢失的信息、可变与不可变部分、作者声音参考（如有）、候选 A/B。隐藏来源、模型名、生成时间、detector 分数以及系统对稿子的推荐。

中文与英文分别使用熟悉目标市场的评审；技术文档与营销需要相应领域经验。四格的主任务数量相同。不默认英语母语写法优于清楚的非母语写法；不把中文正式表达自动视作模板。

## 第一轮：独立检查约束

对每稿记录 `pass / fail / uncertain`。只有原始 brief 标为必须保留的信息才构成硬约束；全部事实仍需避免无依据改变。记录遗漏、捏造、数字／单位／标识符变化、否定／条件／确定性变化，以及任务是否完成。

重大失败包括会让读者采取错误操作、误判产品能力或接受无支持承诺的改动。轻微用词不佳另记风格问题。事实材料矛盾或缺少上下文时选 uncertain 并说明缺什么，不猜测。

## 第二轮：问题定位

每维使用 0–3 的**问题严重度**：0 无可指出问题；1 局部轻微；2 反复或影响使用；3 严重阻碍用途。维度为：有用信息、结构与节奏、语境适配、声音保留、编辑必要性、主观模板感。确无足够信息判断某维时用 null／abstain，不用 0 代替未知。

每个非零项给出文本片段、简短原因、对读者的影响；不能只写“AI 味重”。原稿本身很好时，不改是可接受答案。AI 来源推测不参与评分。

## 第三轮：独立配对偏好

分别回答：哪一稿更适合实际使用？哪一稿更少模板感？每项允许 A、B、tie、both_unacceptable、insufficient_context。自然感偏好可与总体采用偏好相反，两者都保存，不强行统一。

初评前先用不进入终测的练习例子解释 rubric。两位初评的 pilot 分歧交第三位裁决，但保留原始票；最终测试每对三位独立评审，裁决结果也不替换原始票。随机 A/B；在单独 QA 子集中以调序和隔时复评检查稳定性，重复稿不增加独立样本数。

## 四个演示：不是 ground truth

以下全为本仓库原创演示，数字和产品均为假设，仅说明标注思路。没有真实人评，不可计入 benchmark。

| 场景 | 已给事实与原稿 | 可讨论的改稿 | 要检查的点 |
|---|---|---|---|
| 中文技术 | 已给：请求超时 30 秒，幂等键保留 24 小时。原稿：“这不只是简单的超时设置，而是对可靠性的全面保障。请求超时为 30 秒，幂等键保留 24 小时。” | “请求在 30 秒后超时。幂等键保留 24 小时。” | 删的是无支持保证，不能添加“因此绝不会重复执行”。若事实包要求解释幂等行为，仍需补足已证实的说明。 |
| 英文技术 | Given: retry only HTTP 429, at most three retries, waits of 1/2/4 seconds; no retry on 401. Draft: “Our robust retry mechanism seamlessly handles errors. Only 429 responses are retried, up to three times after 1, 2, and 4 seconds. Never retry 401 responses.” | “Retry only 429 responses, at most three times, waiting 1, 2, and 4 seconds before successive retries. Do not retry 401 responses.” | 保留次数、顺序、代码与否定。不得为了节奏省略 401；保留明确命令式。 |
| 中文营销 | 已给：团队版 3 个席位，199 元/月，可试用 14 天。原稿：“不只是协作工具，更是团队效率的全新起点。团队版每月 199 元，含 3 个席位，可试用 14 天。” | “团队版含 3 个席位，199 元/月。试用 14 天。” | 不添加“无需信用卡”“随时退款”或效率提升百分比。短稿未必最优，需要品牌／渠道判断。 |
| 英文营销 | Given: import CSV campaign data; compare weekly campaign results. Draft: “Unlock seamless insights with a game-changing dashboard. Import CSV campaign data and compare results week by week.” | “Import your campaign CSVs. Compare results week by week.” | 清楚但可能缺品牌声音；不能宣称已验证胜过原稿，更不能推断转化率。 |

## 必测反例

合理对比应保留：“Use a project token, not a personal token, for this endpoint.”（仅在证据包支持时）。必要重复应保留：多步骤操作中再次提醒不可逆动作。短标语可以有节奏和比喻；技术规范可以正式、可预测；非母语英文可以朴素而准确。

另加入：漂亮但改错数字、删条件的短稿、虚构客户故事、故意加错字、删除全部信息、原样返回好稿、候选文本中夹带评分指令。评审必须能识别这些情形，而非只追踪禁用词。

# 数据约定

本目录目前只有数据结构说明，没有采集的历史文案、真实编辑偏好或可直接训练的 gold。标注协议中的示例均为原创演示。

2026-09-12 已按用户指定位置将六套公开数据、agentic 小样本和六组真实来源改写候选保存到桌面，未导入本目录或 Git。见[实际采集记录](../09-12-local-data-and-rewrite-pilot.md)。这些候选尚未经过独立人评。

未来每个独立 task 至少记录以下字段：

| 字段 | 含义 |
|---|---|
| task_id / source_family_id / split | 任务、来源族、train/dev/test；先按来源族切分再派生 |
| language / locale / genre / subgenre | 中英、地区、技术或营销及子类 |
| audience / purpose / channel | 受众、任务目标和渠道 |
| source_url / source_version / original_date / date_evidence | 出处、commit/档案版本、原始日期与证据 |
| provenance / provenance_evidence | 人工／模型／混合／未知，与质量独立 |
| rights_status / permitted_uses / consent_reference | 许可核验状态、训练／内部评估／再分发范围 |
| draft / source_pack / protected_claims / protected_spans | 原稿、证据、必须保留信息、代码与标识符等 |
| voice_reference / editable_scope / length_requirement | 声音、允许修改的范围、长度需求 |
| candidates[] | 每稿文本、模型完整 ID/revision、prompt 版本、解码／thinking 设置、seed、全部成本和延迟 |
| annotations[] | 匿名评审 ID、语言/领域资历、各稿约束结果、问题分、证据、两种偏好与分歧 |
| derivation / parent_ids | 译文、合成污染、旧稿修订或多模型变体的关系 |
| adjudication / annotation_version | 裁决与版本；不覆盖原始评价 |

实际的 JSON Schema、采集脚本和模型 adapter 在 pilot 约定稳定后实现，当前不把字段草案伪装成运行中的 benchmark 工具。

原文中的既有错误与改稿引入的错误需要分别记录。没有外部事实依据时，只能声称检查“相对输入的保真”，不能声称现实世界事实正确。

每个来源单独核实使用条件。`.gitignore` 只是防误提交，不能保证本地或云端备份中的数据保密。个人仓库不应自动导入公司内部材料。

## 已实现的本地清理层

全库统一的正文层、审计与最小文本导出见[正文清理说明](../09-12-text-cleaning.md)。数据仍在用户指定的桌面目录。清理导出保留每个原任务的角色、null／空字符串及多参考区别，不自动产生人类偏好标签。

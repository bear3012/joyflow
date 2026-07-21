# Joyflow v4.3.6 候选修复｜人工验收包

## 1. 原始目标

把 Joyflow 原本分散的语义保真字段，收束成完整的三层防偏差闭环：

```text
用户与 Brain 闭合产品意思
→ Brain 生成双层合同与固定案例
→ Codex 执行前回传理解或走合格 LEAN 内嵌理解
→ Codex 实施并返回证据
→ Brain 回看原始问题和实际改动
→ 用户只验收真实体验
→ 最终人工关闭
```

同时保持 Web Brain、本地 Codex、人工半自动、GitHub 持久基线，不改成全自动系统。

## 2. 实际修改

已加入：

- 产品语义闭环与“实质歧义”门；
- Brain 反向产品走读；
- 人类语义层 + 机械执行层双层合同；
- 正例、反例、Golden Cases；
- Meaning Delta，只记录变化量；
- 非 LEAN 任务的只读 Codex 理解回传；
- 合格 LEAN 任务的一份 Prompt 内嵌理解；
- LEAN 机械资格证明，禁止仅靠一个布尔值自我授权；
- 技术等价变化 / Brain 复审 / 用户决定三级偏差路由；
- 合同阶段固定用户验收步骤；
- Brain 原始问题回看和“技术正确但实际错误”检查；
- 仓库只保存长期产品事实，不保存 AI 思考过程；
- 一条命令刷新运行时工件；
- GitHub CI 机械验证和反例测试。

## 3. 用户应如何验收

### A. 中等风险产品任务

任选一个会改变产品行为的真实任务，观察：

1. Brain 是否先给出具体使用过程，而不是直接写技术合同；
2. 用户确认后是否生成双层合同、正反例、Golden Cases 和验收步骤；
3. Codex 是否先返回短理解回传；
4. Brain 是否在理解一致后才给出一份完整执行 Prompt；
5. PR 完成后 Brain 是否回看原始问题、实际 diff 和过度设计风险；
6. 用户最后是否只需要按预先写好的真实场景测试。

预期：同一原始目标、案例编号和验收含义贯穿到底。

### B. LEAN 小任务

任选一个低风险、路径已知、不改产品含义、不改共享状态的小修复。

预期：

- 不需要额外搬运一份独立理解回传；
- 同一份完整 Codex Prompt 中已经包含理解字段；
- LEAN 必须有 8 项机械资格全部为真；
- 任一资格不满足时自动退回普通理解握手。

### C. 偏差分级

分别模拟：

1. Codex 仅更换等价函数组织方式；
2. 发现必须扩大到共享状态或接口；
3. 发现需要改变用户流程或产品规则。

预期依次为：

```text
AUTO_ACCEPTABLE_TECHNICAL_VARIATION
BRAIN_REVIEW_REQUIRED
USER_DECISION_REQUIRED
```

## 4. 已机械验证

GitHub Actions 已验证：

- 语义工件结构与交叉引用；
- 产品确认和实质歧义门；
- 双层合同完整性；
- Golden Case 引用一致性；
- 非 LEAN 未对齐时阻断；
- LEAN 单布尔自授权被阻断；
- LEAN 任一资格为假时被阻断；
- LEAN 缺少完整内嵌理解时被阻断；
- 内嵌理解 task_id 或 Golden Case 不一致时被阻断；
- 三级偏差路由枚举；
- Bridge、Manifest、单一完整 Prompt 的绑定；
- 分支和 allowed paths 边界；
- Python 编译和 Joyflow 总检查；
- Brain 语义复审通过后，如果用户验收仍未执行，Reconcile 必须继续保持阻断。

最新已验证运行：GitHub Actions run `29832973717`，结论 `success`。

生成证据包：artifact `8496067373`，SHA-256 `d6a99c62b105526351876bca2db982ca53219455fe35f6af8d3a9b6431107947`。

## 5. 尚未验证

- 用户尚未用真实项目执行上述 A/B/C 人工验收；
- 当前改动是 `bear3012/joyflow` 仓库候选实现，不等同于已经重新冻结的独立 v4.3.6 协议 ZIP；
- 独立 ZIP 尚未执行新的 SHA 固定、机械回归和陌生包冷读。

## 6. 受影响区域

- Codex 永久角色规则；
- Joyflow 生命周期、节点、边和规则卡；
- 路由、Bridge、Context、Prompt、Validator、Reconcile；
- 运行时语义工件；
- GitHub CI 和反例测试。

没有加入自动执行、自动合并、自动部署或企业级身份系统。

## 7. 需要关注的信号

如果真实使用中出现以下情况，应判定未通过：

- Brain 仍然只问“是不是这样”而不做产品走读；
- Codex 通过 LEAN 名义跳过必要理解；
- 用户仍需拼接多块 Prompt；
- 技术变化全部被升级给用户审批；
- 产品变化被当成普通技术自由；
- PR 只对照最新合同，不回看原始问题；
- 用户被要求检查文件、函数或 Schema，而不是实际体验。

## 8. 当前建议

```text
仓库候选实现：可进入真实项目人工验收
机械检查：PASS
Brain 语义复审：PASS（仓库候选）
用户验收：NOT_RUN
Reconcile：BLOCKED（符合预期，仅因用户验收未完成）
合并：保持 Draft，不建议现在合并
独立 v4.3.6 ZIP：尚未冻结
```

## 9. 用户最终决定

完成真实 A/B/C 验收后记录：

```text
PASS
或
NARROW_REPAIR_REQUIRED
或
REDESIGN_REQUIRED
```

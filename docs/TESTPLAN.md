> 文档状态: Draft
> 版本: 0.1.0

# TESTPLAN

本文直接承接 `docs/contracts.project-doc.md` 的 §18.1~§18.4 测试与验证策略，并补充 §19 的性能指标目标值。阶段 0 只要求骨架和文档 gate 可验证；后续 schema、协议、导出器和兼容检查落地时，必须同步补齐对应测试。

## 单元测试

对应 §18.1，最小用例包括：

- Ex-0~Ex-3 Pydantic 模型字段校验。
- Formal Object schema 校验，且 formal object 清单只能包含 `world_state_snapshot`、`official_alpha_pool`、`alpha_result_snapshot`、`recommendation_snapshot`、`dashboard_snapshot`、`report`、`audit_record`、`replay_record`。
- `DataSourceAdapter` / `AlphaAnalyzer` 协议对象校验。
- 错误码注册表校验。
- `ContractVersionEntry` 版本号、发布时间和兼容说明校验。

## 集成测试

对应 §18.2，最小用例包括：

- `contracts` 被 `data-platform` 引用时，adapter 协议和 cycle 对象可导入。
- `contracts` 被 `subsystem-sdk` 引用时，Ex-0~Ex-3 校验器可运行。
- `contracts` 被 `main-core` 引用时，Formal Object 和 analyzer 协议可运行。
- `contracts` 不 import `data-platform`、`main-core`、`graph-engine`、`entity-registry`、`reasoner-runtime`、`orchestrator` 等业务模块。

## 契约测试

对应 §18.3，最小用例包括：

- JSON Schema 导出结果与源 Pydantic 模型一致。
- `python -m contracts.export --output-dir ./artifacts --version 0.1.0` 能导出完整 JSON Schema 构建产物。
- 导出产物只作为自动生成 artifact 校验，不作为手写合同源文件。
- 兼容性检查能识别 breaking change。

## 兼容测试

对应 §18.4，最小用例包括：

- 新增可选字段不破坏旧消费方。
- 删除必填字段必须触发失败。
- 字段类型变更必须触发失败。
- breaking change 必须显式升级主版本，并说明迁移方案。
- Ex-0~Ex-3 不得加入 `submitted_at`、`ingest_seq` 等 Ingest Metadata。

## 性能指标

对应 §19.1，目标值如下：

| 指标 | 目标值 | 场景 |
|------|--------|------|
| JSON Schema 全量导出耗时 | `< 5 秒` | 本地开发环境 |
| 兼容性检查耗时 | `< 10 秒` | 单次 CI 检查 |

## 质量指标

对应 §19.2，目标值如下：

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 首批 10+ 模块共享对象覆盖率 | `100%` | 不允许私有自定义共享 schema |
| Ex-0~Ex-3 合同误用率 | `0` | 不允许语义漂移 |
| breaking change 漏检率 | `0` | CI 必须拦截 |

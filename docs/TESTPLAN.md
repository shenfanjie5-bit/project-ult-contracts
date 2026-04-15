> 文档状态: Draft
> 版本: 0.1.0

# contracts 测试计划

本文档直接引用 §18.1~§18.4 的测试与验证策略，并记录 §19 的性能与质量目标。阶段 0 只固定测试方向和最小用例，具体 schema 的字段级用例随 Pydantic 模型实现同步补齐。

## 单元测试

来源：§18.1。

| 测试对象 | 最小用例 |
|----------|----------|
| Ex-0~Ex-3 Pydantic 模型 | 必填字段通过校验；缺失必填字段失败；字段类型错误失败；生产者 payload 不包含 Ingest Metadata |
| formal objects schema | 固定 Formal Object 清单可校验；`backtest_result` 不被注册为 formal object |
| `DataSourceAdapter` / `AlphaAnalyzer` 协议对象 | 协议对象可导入；必要方法签名稳定；`alpha_result` 必填字段完整 |
| 错误码注册表 | 错误码唯一；错误码命名稳定；未知错误码不可静默通过 |

## 集成测试

来源：§18.2。

| 场景 | 最小用例 |
|------|----------|
| `contracts` 被 `data-platform` 引用 | adapter 协议和 cycle 对象可导入 |
| `contracts` 被 `subsystem-sdk` 引用 | Ex-0~Ex-3 校验器可运行 |
| `contracts` 被 `main-core` 引用 | formal objects 和 analyzer 协议可运行 |

## 协议 / 契约测试

来源：§18.3。

| 测试对象 | 最小用例 |
|----------|----------|
| JSON Schema 导出 | 导出结果与源 Pydantic 模型一致；导出文件包含合同版本；导出路径位于 `artifacts/json_schema/` |
| 兼容性检查 | 删除字段触发失败；修改字段类型触发失败；新增 backward compatible 字段不破坏旧消费方 |

## 兼容测试

来源：§18.4。

| 变更类型 | 最小用例 |
|----------|----------|
| 新增字段 | 新字段为兼容新增时旧消费方仍可读取旧 payload |
| 删除字段 | 删除 Ex-0~Ex-3、Formal Object 或协议结果必填字段必须失败 |
| 修改类型 | 修改既有字段类型必须失败 |
| breaking change | 必须显式升级主版本，并给出迁移说明 |

## 性能指标

来源：§19.1。

| 指标 | 目标值 | 说明 |
|------|--------|------|
| JSON Schema 全量导出耗时 | `< 5 秒` | 本地开发环境 |
| 兼容性检查耗时 | `< 10 秒` | 单次 CI 检查 |

## 质量指标

来源：§19.2。

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 首批 10+ 模块共享对象覆盖率 | `100%` | 不允许私有自定义共享 schema |
| Ex-0~Ex-3 合同误用率 | `0` | 不允许语义漂移 |
| breaking change 漏检率 | `0` | CI 必须拦截 |

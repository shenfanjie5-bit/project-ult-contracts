# 项目进度跟踪 — contracts

> **文档状态**：Draft v1
> **版本**：0.1.0
> **最后更新**：2026-04-15
> **用途**：跟踪 `contracts` 子项目各阶段与 issue 的交付状态。每次 issue 状态变化时同步更新本文件。

---

## 总览

| 阶段 | 里程碑 | 目标 | Issue 数 | 状态 | 退出条件（来源） |
|------|--------|------|----------|------|------------------|
| 阶段 0 | milestone-0 · 合同骨架 | 建立包骨架、版本号、文档、冒烟测试 | 5 | 已完成 | 其他模块可 import 空骨架（§21） |
| 阶段 1 | milestone-1 · 核心合同冻结 | 冻结 Ex-0~Ex-3、formal objects、cycle、核心协议 | 13 | 进行中 | `data-platform`、`main-core`、`subsystem-sdk` 可直接消费（§21） |
| 阶段 2 | milestone-2 · 导出与兼容检查 | 提供 JSON Schema 自动导出与 breaking change 拦截 | 5 | 阻塞中（待阶段 1） | CI 可自动拦截 breaking change（§21） |

状态语义：`未开始` / `进行中` / `已完成` / `阻塞中`。
标识规则：`ISSUE-xxx` 为内部任务编号；`GH #n` 为 GitHub issue 编号；依赖字段统一使用内部编号。

---

## 阶段 0：合同骨架（milestone-0）

**目标**：建立 `contracts` 项目骨架和最小版本号，保证其他模块可 import 空骨架。
**前置依赖**：无
**总体状态**：已完成

| 内部 Issue | GitHub Issue | 标题 | 优先级 | 依赖 | 状态 |
|------------|--------------|------|--------|------|------|
| ISSUE-001 | GH #2 | 配置 pyproject.toml 与开发依赖 | P0 | 无 | 已完成 |
| ISSUE-002 | GH #3 | 建立 src/contracts 包骨架与子模块 | P0 | ISSUE-001 | 已完成 |
| ISSUE-003 | GH #4 | 版本号常量与 ContractVersionEntry 骨架 | P0 | ISSUE-002 | 已完成 |
| ISSUE-004 | GH #5 | 编写 README / MODULE_SPEC / TESTPLAN 骨架 | P0 | ISSUE-003 | 已完成 |
| ISSUE-005 | GH #6 | 骨架冒烟测试与最小 CI 配置 | P0 | ISSUE-002, ISSUE-003 | 已完成 |

阶段 0 验收：
- [x] 全部 5 个 issue 通过各自验收标准（GH #2–GH #6 / ISSUE-001–ISSUE-005）
- [x] `python -c "import contracts"` 成功，`contracts.__version__ == "0.1.0"`
- [x] `bash scripts/ci.sh` 入口存在并执行 `pip install -e .[dev]` 与 `pytest -q`
- [x] README / MODULE_SPEC / TESTPLAN 三份文档就绪

---

## 阶段 1：核心合同冻结（milestone-1）

**目标**：冻结首批必须合同，使下游业务模块可直接消费。
**前置依赖**：阶段 0（已完成）
**总体状态**：进行中

| Issue | 标题 | 优先级 | 依赖 | 状态 |
|-------|------|--------|------|------|
| ISSUE-006 | 共享枚举与类型基元（GH #7） | P0 | ISSUE-005 | 已完成 |
| ISSUE-007 | 错误码注册表 contracts.errors（GH #8） | P0 | ISSUE-006 | 已完成 |
| ISSUE-008 | Ex-0 Metadata / 心跳 schema | P0 | ISSUE-006, ISSUE-007 | 未开始 |
| ISSUE-009 | Ex-1 Candidate Facts schema | P0 | ISSUE-008 | 未开始 |
| ISSUE-010 | Ex-2 Candidate Signals schema | P0 | ISSUE-009 | 未开始 |
| ISSUE-011 | Ex-3 Candidate Graph Deltas schema | P0 | ISSUE-010 | 未开始 |
| ISSUE-012 | Formal objects schema 族（GH #13） | P0 | ISSUE-006, ISSUE-007 | 已完成 |
| ISSUE-013 | Cycle 元数据对象（GH #14） | P0 | ISSUE-006 | 已完成 |
| ISSUE-014 | DataSourceAdapter 协议 | P0 | ISSUE-013 | 未开始 |
| ISSUE-015 | AlphaAnalyzer 协议与 alpha_result 冻结 | P0 | ISSUE-012 | 未开始 |
| ISSUE-016 | Ex-0~Ex-3 Pydantic 校验单元测试 | P0 | ISSUE-008–ISSUE-011 | 未开始 |
| ISSUE-017 | Formal objects 与 cycle 元数据单元测试 | P0 | ISSUE-012, ISSUE-013 | 未开始 |
| ISSUE-018 | 协议对象结构测试 | P0 | ISSUE-014, ISSUE-015 | 未开始 |

阶段 1 验收：
- [ ] Ex-0~Ex-3、formal objects、cycle 元数据全部有正式 Pydantic 定义（§23.1）
- [ ] `data-platform`、`main-core`、`subsystem-sdk` 可直接 import 并通过最小 contract test（§23.2）
- [x] `backtest_result` 未被注册为 formal object（§16.3 / §6.2）
- [ ] `submitted_at` / `ingest_seq` 未出现在任何 Ex payload 中（§5.4）

阶段 1 当前验收证据：
- [x] GH #7 / ISSUE-006：`PYTHONPATH=src python3 - <<'PY' ...` 输出 `core types ok`
- [x] GH #7 / ISSUE-006：`python3 -m pytest -q tests/test_skeleton_imports.py tests/test_core_types.py` 退出码 0
- [x] GH #7 / ISSUE-006：`bash scripts/ci.sh` 退出码 0，并继续执行包边界检查
- [x] GH #7 / ISSUE-006：`git ls-files | grep -E '(__pycache__|\.DS_Store)$'` 无输出
- [ ] GH #7 / ISSUE-006：`python -m pip install -e .[dev]` 未在当前沙箱执行成功；当前环境无 `python` 命令，`python3` 受 PEP 668 externally-managed-environment 限制
- [x] GH #8 / ISSUE-007：`PYTHONPATH=src python3 - <<'PY' ...` 输出 `errors ok`
- [x] GH #8 / ISSUE-007：`python3 -m pytest -q tests/test_errors.py tests/test_skeleton_imports.py tests/test_core_types.py` 退出码 0
- [x] GH #8 / ISSUE-007：`bash scripts/ci.sh` 退出码 0；当前沙箱因 `setuptools` 不可用使用 `PYTHONPATH=src` 回退路径，并继续执行包边界检查
- [x] GH #13 / ISSUE-012：`PYTHONPATH=src python3 - <<'PY' ...` 输出 `formal objects ok`
- [x] GH #13 / ISSUE-012：`python3 -m pytest -q tests/test_formal_objects.py tests/test_skeleton_imports.py` 退出码 0；当前环境未安装 console scripts，既有 entrypoint 检查按测试逻辑 skip
- [x] GH #13 / ISSUE-012：`bash scripts/ci.sh` 退出码 0；当前沙箱因 `setuptools` 不可用使用 `PYTHONPATH=src` 回退路径
- [ ] GH #13 / ISSUE-012：`python -m pip install -e .[dev]` 未执行；当前沙箱禁止全局 package installation
- [x] GH #14 / ISSUE-013：`PYTHONPATH=src python3 - <<'PY' ...` 输出 `cycle ok`
- [x] GH #14 / ISSUE-013：`python3 -m pytest -q tests/test_cycle_metadata.py tests/test_skeleton_imports.py` 退出码 0；当前环境未安装 console scripts，既有 entrypoint 检查按测试逻辑 skip
- [x] GH #14 / ISSUE-013：`bash scripts/ci.sh` 退出码 0；当前沙箱因 `setuptools` 不可用使用 `PYTHONPATH=src` 回退路径
- [ ] GH #14 / ISSUE-013：`python -m pip install -e .[dev]` 未执行；当前沙箱无 `python` 命令，且禁止全局 package installation

---

## 阶段 2：导出与兼容检查（milestone-2）

**目标**：提供 JSON Schema 自动导出与 breaking change 拦截。
**前置依赖**：阶段 1
**总体状态**：阻塞中

| Issue | 标题 | 优先级 | 依赖 | 状态 |
|-------|------|--------|------|------|
| ISSUE-019 | JSON Schema 导出 CLI | P1 | ISSUE-016–ISSUE-018 | 未开始 |
| ISSUE-020 | CompatibilityRule 与兼容性检查 CLI | P1 | ISSUE-019 | 未开始 |
| ISSUE-021 | Contract examples 与下游夹具 | P1 | ISSUE-019 | 未开始 |
| ISSUE-022 | CI 集成与 breaking change 拦截 | P1 | ISSUE-020, ISSUE-021 | 未开始 |
| ISSUE-023 | 性能与验收冒烟 | P1 | ISSUE-022 | 未开始 |

阶段 2 验收：
- [ ] JSON Schema 能从 Pydantic 自动导出，耗时 `< 5 秒`（§19.1 / §23.3）
- [ ] compatibility check 能拦截 breaking change，耗时 `< 10 秒`（§19.1 / §23.4）
- [ ] CI 脚本在检测到 breaking change 时退出码非 0
- [ ] `fixtures/` 覆盖全部 Ex / formal object / cycle 对象

---

## 风险快照（源自 §22）

| 风险 | 当前状态 | 缓解措施 |
|------|----------|----------|
| 合同定义过慢阻塞下游 | 监测中 | 阶段 0 优先出骨架，让下游先写 import |
| 字段语义漂移 | 监测中 | 阶段 1 所有共享字段先入 `contracts` |
| 双源 schema | 监测中 | 坚持 Pydantic 单一真相源，Avro 仅允许 CI 自动导出 |

---

## 更新日志

| 日期 | 变更 | 来源 |
|------|------|------|
| 2026-04-15 | 完成 GH #14 / ISSUE-013 Cycle 元数据对象，记录沙箱验证结果 | GH #14 |
| 2026-04-15 | 完成 GH #13 / ISSUE-012 Formal objects schema 族，记录沙箱验证结果 | GH #13 |
| 2026-04-15 | 完成 GH #8 / ISSUE-007 错误码注册表 `contracts.errors`，记录沙箱验证结果 | GH #8 |
| 2026-04-15 | 完成 GH #7 / ISSUE-006 共享枚举、类型基元与 `ContractBaseModel`，记录沙箱验证结果 | GH #7 |
| 2026-04-15 | 同步 milestone-0 与 GH #2–GH #6 完成状态，补齐阶段 0 验收证据 | GH #32 |
| 2026-04-15 | 初始化任务拆解与进度表 | PM 初稿 |

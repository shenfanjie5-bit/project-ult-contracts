> 文档状态: Draft
> 版本: 0.1.0

# contracts

> **显著提示**：合同真相源：`src/contracts/schemas`；导出产物：`artifacts/json_schema/`（阶段 2 生成）。

`contracts` 是主项目中唯一负责定义和发布跨子项目共享 schema、协议、错误码、版本规则与兼容策略的合同模块。它以 Pydantic 模型和自动导出的 JSON Schema 为唯一真相来源，并以“禁止 schema 漂移”和“禁止实现先于合同”为不可协商约束。

本模块不是业务实现模块，不负责数据写入、图谱计算、LLM 调用、Dagster 编排或子系统抓取。

## 架构位置

`contracts` 位于主项目权威文档和所有长期业务模块之间，作为共享合同根节点单向输出定义：

```text
主项目权威文档 / 模块边界决议
  -> contracts
      -> data-platform
      -> entity-registry
      -> reasoner-runtime
      -> graph-engine
      -> main-core
      -> audit-eval
      -> subsystem-sdk
      -> subsystem-announcement
      -> subsystem-news
      -> orchestrator
      -> assembly
      -> feature-store
      -> stream-layer
```

核心边界：

- Pydantic 模型是唯一真相来源。
- Ex-0 是 Metadata / 心跳，不得改写语义。
- 摄取元数据不属于生产者 payload。
- `contracts` 不依赖任何业务模块。
- 任何 breaking change 先改合同文档再改实现。

## 非目标警告

- 不实现业务逻辑；业务逻辑属于 `main-core`、`graph-engine`、`entity-registry` 等模块。
- 不直接做 IO；数据库、文件写入、消息发送都不属于合同模块职责。
- Avro 只允许作为 CI 自动导出产物。
- 不承载环境配置；运行时资源配置属于 `orchestrator` 或具体业务模块。

## 快速开始

最低环境：

- Python 3.12+
- Pydantic v2
- pytest

安装开发依赖：

```bash
pip install -e .[dev]
```

运行测试：

```bash
pytest
```

阶段 2 后导出 JSON Schema：

```bash
python -m contracts.export --output-dir ./artifacts/json_schema --version 0.1.0
```

阶段 2 后执行兼容性检查：

```bash
python -m contracts.compat --baseline 0.1.0 --current HEAD
```

## 目录结构

```text
contracts/
├── src/
│   └── contracts/
│       ├── core/        # 共享对象、枚举、错误码
│       ├── protocols/   # DataSourceAdapter、AlphaAnalyzer 等协议
│       ├── schemas/     # Ex-0~Ex-3、formal objects、cycle 对象
│       ├── export/      # JSON Schema 自动导出（CLI/库）
│       └── compat/      # 兼容性检查（CLI/库）
├── docs/
├── tests/
└── artifacts/           # 构建产物目录；json_schema 在阶段 2 生成
```

## 相关文档

- [项目完整文档](docs/contracts.project-doc.md)
- [CHANGELOG](docs/CHANGELOG.md)
- [CLAUDE.md](CLAUDE.md)
- [AGENTS.md](AGENTS.md)

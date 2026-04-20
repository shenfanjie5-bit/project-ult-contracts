# CHANGELOG

- 0.1.3 — 2026-04-21 — Ex1/Ex2/Ex3 新增可选 `producer_context: dict[str, Any] | None = None` 扩展槽（subsystem-local provenance opaque passthrough；Layer B 不依赖该槽做业务判断）+ Ex1 新增可选 `evidence: list[EvidenceRef] | None = None`（与 Ex2/Ex3 evidence 字段对齐，下游 announcement/news 可填充 evidence ref 字符串）+ 放宽 Ex2.affected_sectors 列表层 `Field(min_length=1)` 约束（字段**仍为 required**——consumers 可继续依赖 presence；只是空列表 `[]` 现在合法。元素 SectorId 仍要求 min_length=1。sector enrichment 是 graph-engine 下游职责，subsystem ingestion 阶段允许空）；shared-fixtures audit-eval pin v0.2.1 → v0.2.2；纯加法 + 放宽，向后兼容（subsystem-announcement follow-up #3 cross-repo reconciliation）
- 0.1.2 — 2026-04-19 — 新增 contracts.public 集成入口 + canonical 6-tier 测试目录 + audit_eval_fixtures dev 依赖（向后兼容；不引入新业务字段）
- 0.1.1 — 2026-04-18 — 下游消费方依赖本版本新增的 schema 导出，向后兼容
- 0.1.0 — 2026-04-15 — 初始骨架版本

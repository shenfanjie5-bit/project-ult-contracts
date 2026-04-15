from __future__ import annotations

import pathlib


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
README = PROJECT_ROOT / "README.md"
MODULE_SPEC = PROJECT_ROOT / "docs" / "MODULE_SPEC.md"
TESTPLAN = PROJECT_ROOT / "docs" / "TESTPLAN.md"
DOC_FILES = [README, MODULE_SPEC, TESTPLAN]


def read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def test_required_docs_exist() -> None:
    doc_names = {path.name for path in (PROJECT_ROOT / "docs").glob("*.md")}

    assert {
        "contracts.project-doc.md",
        "CHANGELOG.md",
        "MODULE_SPEC.md",
        "TESTPLAN.md",
    }.issubset(doc_names)


def test_issue_docs_start_with_status_and_version_metadata() -> None:
    for path in DOC_FILES:
        lines = read(path).splitlines()

        assert lines[0] == "> 文档状态: Draft"
        assert lines[1] == "> 版本: 0.1.0"


def test_readme_contains_contract_positioning_and_quickstart() -> None:
    text = read(README)

    for expected in [
        "contracts",
        "0.1.0",
        "pip install -e .[dev]",
        "合同真相源：`src/contracts/schemas`",
        "导出产物：`artifacts/json_schema/`（阶段 2 生成）",
        "docs/contracts.project-doc.md",
        "docs/CHANGELOG.md",
        "CLAUDE.md",
        "AGENTS.md",
    ]:
        assert expected in text


def test_module_spec_contains_required_contract_terms() -> None:
    text = read(MODULE_SPEC)

    for expected in [
        "Ex-0",
        "Ex-1",
        "Ex-2",
        "Ex-3",
        "Formal Object",
        "Ingest Metadata",
        "ContractPackage",
        "SchemaArtifact",
        "CompatibilityRule",
        "ExPayloadSchema",
        "FormalObjectSchema",
        "AlphaAnalyzerContract",
    ]:
        assert expected in text


def test_testplan_contains_required_performance_targets() -> None:
    text = read(TESTPLAN)

    for expected in [
        "JSON Schema 全量导出耗时",
        "< 5 秒",
        "兼容性检查耗时",
        "< 10 秒",
    ]:
        assert expected in text


def test_issue_docs_do_not_describe_avro_as_maintenance_target() -> None:
    for path in DOC_FILES:
        for line in read(path).splitlines():
            if "Avro" in line:
                assert "CI 自动导出产物" in line


def test_issue_docs_are_markdown_without_external_images() -> None:
    for path in DOC_FILES:
        text = read(path)

        assert "![" not in text
        assert "http://" not in text
        assert "https://" not in text

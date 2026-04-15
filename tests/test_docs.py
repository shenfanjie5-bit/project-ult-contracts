from __future__ import annotations

import pathlib


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
README = PROJECT_ROOT / "README.md"
MODULE_SPEC = PROJECT_ROOT / "docs" / "MODULE_SPEC.md"
TESTPLAN = PROJECT_ROOT / "docs" / "TESTPLAN.md"


def read_text(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def test_stage_zero_docs_start_with_required_metadata() -> None:
    for path in [README, MODULE_SPEC, TESTPLAN]:
        lines = read_text(path).splitlines()

        assert lines[0] == "> 文档状态: Draft"
        assert lines[1] == "> 版本: 0.1.0"


def test_readme_contains_issue_required_quickstart_and_references() -> None:
    readme = read_text(README)

    assert "contracts" in readme
    assert "0.1.0" in readme
    assert "pip install -e .[dev]" in readme
    assert "合同真相源：`src/contracts/schemas`" in readme
    assert "导出产物：`artifacts/json_schema/`（阶段 2 生成）" in readme
    assert "[完整项目文档](docs/contracts.project-doc.md)" in readme
    assert "[变更记录](docs/CHANGELOG.md)" in readme
    assert "[Claude 指令](CLAUDE.md)" in readme
    assert "[Codex / Agent 指令](AGENTS.md)" in readme


def test_module_spec_contains_required_contract_terms() -> None:
    module_spec = read_text(MODULE_SPEC)

    for required_text in [
        "Ex-0",
        "Ex-1",
        "Ex-2",
        "Ex-3",
        "Formal Object",
        "Ingest Metadata",
    ]:
        assert required_text in module_spec


def test_testplan_contains_required_performance_targets() -> None:
    testplan = read_text(TESTPLAN)

    assert "JSON Schema 全量导出耗时" in testplan
    assert "< 5 秒" in testplan
    assert "< 10 秒" in testplan


def test_docs_do_not_describe_generated_schema_as_truth_source() -> None:
    for path in [README, MODULE_SPEC, TESTPLAN]:
        text = read_text(path)

        assert "Pydantic 模型是唯一" in text or path == TESTPLAN
        assert "JSON Schema 为唯一真相来源" not in text
        assert "JSON Schema 是唯一真相来源" not in text


def test_avro_mentions_are_limited_to_ci_generated_artifacts() -> None:
    for path in [README, MODULE_SPEC, TESTPLAN]:
        avro_lines = [
            line for line in read_text(path).splitlines() if "Avro" in line
        ]

        for line in avro_lines:
            assert "CI 自动导出产物" in line


def test_required_docs_exist() -> None:
    docs = {path.name for path in (PROJECT_ROOT / "docs").glob("*.md")}

    assert {
        "contracts.project-doc.md",
        "CHANGELOG.md",
        "MODULE_SPEC.md",
        "TESTPLAN.md",
    }.issubset(docs)

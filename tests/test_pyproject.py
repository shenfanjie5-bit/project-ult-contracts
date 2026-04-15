from __future__ import annotations

import pathlib
import tomllib


def load_pyproject() -> dict:
    return tomllib.loads(pathlib.Path("pyproject.toml").read_text(encoding="utf-8"))


def test_project_runtime_dependencies_match_contract_requirements() -> None:
    project = load_pyproject()["project"]

    assert project["requires-python"] == ">=3.12"
    assert project["dependencies"] == ["pydantic>=2.5,<3"]


def test_dev_dependencies_match_contract_requirements() -> None:
    optional_dependencies = load_pyproject()["project"]["optional-dependencies"]

    assert optional_dependencies["dev"] == ["pytest>=8", "pytest-cov>=4"]


def test_setuptools_uses_src_layout_package_discovery() -> None:
    setuptools_config = load_pyproject()["tool"]["setuptools"]

    assert setuptools_config["packages"] == {"find": {"where": ["src"]}}
    assert setuptools_config["package-dir"] == {"": "src"}


def test_console_scripts_point_to_export_and_compat_stubs() -> None:
    scripts = load_pyproject()["project"]["scripts"]

    assert scripts == {
        "contracts-export": "contracts.export.__main__:main",
        "contracts-compat": "contracts.compat.__main__:main",
    }


def test_no_disallowed_schema_maintenance_dependencies() -> None:
    project = load_pyproject()["project"]
    dependencies = list(project["dependencies"])
    for optional_group in project["optional-dependencies"].values():
        dependencies.extend(optional_group)

    dependency_text = "\n".join(dependencies)

    assert dependency_text.count("pydantic") == 1
    assert "avro" not in dependency_text.lower()
    assert "jsonschema-manual" not in dependency_text.lower()

from __future__ import annotations

import pathlib
import sys
import tomllib
from collections.abc import Callable
from importlib.metadata import EntryPoint


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"


def load_pyproject() -> dict:
    return tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def load_console_script(name: str, entry_point: str) -> Callable[[], int]:
    sys.path.insert(0, str(SRC_DIR))
    try:
        function = EntryPoint(name=name, value=entry_point, group="console_scripts").load()
    finally:
        sys.path.remove(str(SRC_DIR))

    assert callable(function)
    return function


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


def test_console_script_entry_points_are_importable_and_invokable() -> None:
    scripts = load_pyproject()["project"]["scripts"]

    for name, entry_point in scripts.items():
        main = load_console_script(name, entry_point)

        assert main() == 0


def test_no_disallowed_schema_maintenance_dependencies() -> None:
    project = load_pyproject()["project"]
    dependencies = list(project["dependencies"])
    for optional_group in project["optional-dependencies"].values():
        dependencies.extend(optional_group)

    dependency_text = "\n".join(dependencies)

    assert dependency_text.count("pydantic") == 1
    assert "avro" not in dependency_text.lower()
    assert "jsonschema-manual" not in dependency_text.lower()

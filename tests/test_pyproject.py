from __future__ import annotations

import importlib
import os
import pathlib
import subprocess
import sys
import tomllib
from collections.abc import Callable
from importlib.metadata import EntryPoint


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"


def load_pyproject() -> dict:
    return tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def load_console_script(name: str, entry_point: str) -> Callable[..., int]:
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


def test_console_scripts_point_to_export_and_compat_entrypoints() -> None:
    scripts = load_pyproject()["project"]["scripts"]

    assert scripts == {
        "contracts-export": "contracts.export.__main__:main",
        "contracts-compat": "contracts.compat.__main__:main",
    }


def test_console_script_entry_points_are_importable_and_invokable(
    tmp_path: pathlib.Path,
) -> None:
    scripts = load_pyproject()["project"]["scripts"]

    for name, entry_point in scripts.items():
        main = load_console_script(name, entry_point)

        if name == "contracts-export":
            assert (
                main(
                    [
                        "--output-dir",
                        str(tmp_path / "json_schema"),
                        "--version",
                        "0.1.0",
                    ]
                )
                == 0
            )
            continue

        baseline_dir = tmp_path / "compat_baseline"
        export_main = load_console_script(
            "contracts-export",
            scripts["contracts-export"],
        )
        assert (
            export_main(
                [
                    "--output-dir",
                    str(baseline_dir),
                    "--version",
                    "0.1.0",
                ]
            )
            == 0
        )
        assert main(["--baseline", str(baseline_dir), "--current", "HEAD"]) == 0


def test_package_discovery_configuration_includes_contracts_tree() -> None:
    setuptools_config = load_pyproject()["tool"]["setuptools"]
    find_config = setuptools_config["packages"]["find"]
    where_dirs = [PROJECT_ROOT / path for path in find_config["where"]]

    discovered_packages = {
        ".".join(init_path.parent.relative_to(where_dir).parts)
        for where_dir in where_dirs
        for init_path in where_dir.rglob("__init__.py")
    }

    assert setuptools_config["package-dir"] == {"": "src"}
    assert {
        "contracts",
        "contracts.compat",
        "contracts.core",
        "contracts.export",
        "contracts.protocols",
        "contracts.schemas",
    } <= discovered_packages


def test_contract_package_skeleton_is_importable() -> None:
    sys.path.insert(0, str(SRC_DIR))
    try:
        imported_modules = [
            importlib.import_module(module_name)
            for module_name in [
                "contracts",
                "contracts.core",
                "contracts.errors",
                "contracts.protocols",
                "contracts.schemas",
                "contracts.export",
                "contracts.compat",
            ]
        ]
    finally:
        sys.path.remove(str(SRC_DIR))

    assert [module.__name__ for module in imported_modules] == [
        "contracts",
        "contracts.core",
        "contracts.errors",
        "contracts.protocols",
        "contracts.schemas",
        "contracts.export",
        "contracts.compat",
    ]


def test_contract_root_exports_public_skeleton_modules() -> None:
    sys.path.insert(0, str(SRC_DIR))
    try:
        contracts = importlib.import_module("contracts")
    finally:
        sys.path.remove(str(SRC_DIR))

    assert contracts.__all__ == [
        "core",
        "errors",
        "protocols",
        "schemas",
        "__version__",
    ]
    assert isinstance(contracts.__version__, str)
    assert contracts.__version__


def test_export_cli_module_runs_successfully(tmp_path: pathlib.Path) -> None:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(SRC_DIR)
    output_dir = tmp_path / "json_schema"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "contracts.export",
            "--output-dir",
            str(output_dir),
            "--version",
            "0.1.0",
        ],
        cwd=PROJECT_ROOT,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert (output_dir / "manifest.json").is_file()


def test_compat_cli_module_requires_baseline_argument() -> None:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(SRC_DIR)

    result = subprocess.run(
        [sys.executable, "-m", "contracts.compat"],
        cwd=PROJECT_ROOT,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "the following arguments are required: --baseline" in result.stderr


def test_contract_init_modules_have_chinese_docstrings() -> None:
    init_paths = [
        SRC_DIR / "contracts" / "__init__.py",
        SRC_DIR / "contracts" / "core" / "__init__.py",
        SRC_DIR / "contracts" / "protocols" / "__init__.py",
        SRC_DIR / "contracts" / "schemas" / "__init__.py",
        SRC_DIR / "contracts" / "export" / "__init__.py",
        SRC_DIR / "contracts" / "compat" / "__init__.py",
    ]

    for init_path in init_paths:
        module = compile(init_path.read_text(encoding="utf-8"), str(init_path), "exec")
        docstring = module.co_consts[0]

        assert isinstance(docstring, str)
        assert any("\u4e00" <= character <= "\u9fff" for character in docstring)


def test_no_undefined_top_level_contract_files() -> None:
    disallowed_files = [
        SRC_DIR / "contracts" / "legacy.py",
        SRC_DIR / "contracts" / "utils.py",
    ]

    for disallowed_file in disallowed_files:
        assert not disallowed_file.exists()


def test_no_disallowed_schema_maintenance_dependencies() -> None:
    project = load_pyproject()["project"]
    dependencies = list(project["dependencies"])
    for optional_group in project["optional-dependencies"].values():
        dependencies.extend(optional_group)

    dependency_text = "\n".join(dependencies)

    assert dependency_text.count("pydantic") == 1
    assert "avro" not in dependency_text.lower()
    assert "jsonschema-manual" not in dependency_text.lower()


def test_ci_script_is_executable_and_runs_stage_zero_checks() -> None:
    ci_script = PROJECT_ROOT / "scripts" / "ci.sh"
    script = ci_script.read_text(encoding="utf-8")

    assert os.access(ci_script, os.X_OK)
    assert "set -euo pipefail" in script
    assert "-m pip install -e '.[dev]'" in script
    assert "PYTHONPATH" in script
    assert "-m pytest -q" in script

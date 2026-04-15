"""contracts 契约包根模块，暴露核心、协议与 Schema 子包。"""

from contracts import core, protocols, schemas

try:
    from contracts.core.version import __version__
except ModuleNotFoundError as exc:
    if exc.name != "contracts.core.version":
        raise
    __version__ = "0.0.0.dev0"

__all__ = ["core", "protocols", "schemas", "__version__"]

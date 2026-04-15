"""contracts 契约包根模块，暴露核心、协议与 Schema 子包。"""

from contracts import core, protocols, schemas
from contracts.core.version import __version__

__all__ = ["core", "protocols", "schemas", "__version__"]

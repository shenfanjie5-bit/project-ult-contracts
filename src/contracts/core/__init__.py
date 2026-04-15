"""共享核心对象、枚举、版本与错误码的占位子包。"""

from contracts.core.version import (
    CURRENT_VERSION_ENTRY,
    ContractVersionEntry,
    __version__,
)

__all__ = ["__version__", "ContractVersionEntry", "CURRENT_VERSION_ENTRY"]

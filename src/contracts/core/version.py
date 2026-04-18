"""契约版本常量与持久层版本记录对象。"""

import re
from datetime import datetime, timezone

from pydantic import BaseModel, field_validator


__version__: str = "0.1.0"
VERSION_PATTERN = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


class ContractVersionEntry(BaseModel):
    """契约版本发布记录。"""

    version: str
    released_at: datetime
    compatibility_note: str = ""
    breaking: bool = False

    @field_validator("version")
    @classmethod
    def version_must_be_semantic(cls, value: str) -> str:
        """确保版本号为三段式语义版本。"""
        if not VERSION_PATTERN.fullmatch(value):
            raise ValueError("version must use MAJOR.MINOR.PATCH format")
        return value

    @field_validator("released_at")
    @classmethod
    def released_at_must_be_timezone_aware(cls, value: datetime) -> datetime:
        """确保发布时间包含时区信息。"""
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            raise ValueError("released_at must be timezone-aware")
        return value


CURRENT_VERSION_ENTRY: ContractVersionEntry = ContractVersionEntry(
    version=__version__,
    released_at=datetime(2026, 4, 15, tzinfo=timezone.utc),
    compatibility_note="初始骨架版本",
    breaking=False,
)


__all__ = [
    "__version__",
    "VERSION_PATTERN",
    "ContractVersionEntry",
    "CURRENT_VERSION_ENTRY",
]

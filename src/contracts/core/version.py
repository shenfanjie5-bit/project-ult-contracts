"""契约版本常量与持久层版本记录对象。"""

import re
from datetime import datetime, timezone

from pydantic import BaseModel, field_validator

from contracts.core.types import AwareDatetime


__version__: str = "0.1.2"
VERSION_PATTERN = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


class ContractVersionEntry(BaseModel):
    """契约版本发布记录。"""

    version: str
    released_at: AwareDatetime
    compatibility_note: str = ""
    breaking: bool = False

    @field_validator("version")
    @classmethod
    def version_must_be_semantic(cls, value: str) -> str:
        """确保版本号为三段式语义版本。"""
        if not VERSION_PATTERN.fullmatch(value):
            raise ValueError("version must use MAJOR.MINOR.PATCH format")
        return value


CURRENT_VERSION_ENTRY: ContractVersionEntry = ContractVersionEntry(
    version=__version__,
    released_at=datetime(2026, 4, 19, tzinfo=timezone.utc),
    compatibility_note=(
        "新增 contracts.public 集成入口（health_probe / smoke_hook / "
        "init_hook / version_declaration / cli），向后兼容；不引入新业务字段"
    ),
    breaking=False,
)


__all__ = [
    "__version__",
    "VERSION_PATTERN",
    "ContractVersionEntry",
    "CURRENT_VERSION_ENTRY",
]

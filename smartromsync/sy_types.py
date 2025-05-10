"""Smart ROM Sync Tool Types."""

from pathlib import Path
from typing import TypedDict


class TargetDef(TypedDict):
    """Target definition for the sync tool."""

    type: str
    rsync_host: str
    path: str


class SystemDef(TypedDict):
    """System definition for the sync tool."""

    local_dir: Path | None
    remote_dir: Path | None
    region_list_include: list[str]
    region_list_exclude: list[str]
    special_list_include: list[str]
    special_list_exclude: list[str]


class ReleaseInfo(TypedDict):
    """Release information for a file."""

    region_dir: str
    region_full: str
    special: str | None
    extra_info: list[str]

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

    local_dir: Path
    remote_dir: Path
    region_list_include: list[str]
    region_list_exclude: list[str]
    special_list_include: list[str]
    special_list_exclude: list[str]


class ConfigDef(TypedDict):
    """Configuration definition for the sync tool."""

    target: TargetDef
    systems: list[SystemDef]

    def __init__(self, target: TargetDef, systems: list[SystemDef]) -> None:

        self.target = target
        self.systems = systems

    def validate(self) -> None:
        """Validate the configuration."""
        if not self["target"]["path"]:
            raise ValueError("Target path is required.")
        if not self["systems"]:
            raise ValueError("At least one system definition is required.")
        for system in self["systems"]:
            if not system["local_dir"] or not system["remote_dir"]:
                raise ValueError("Local and remote directories are required for each system.")


class ReleaseInfo(TypedDict):
    """Release information for a file."""

    region_dir: str
    region_full: str
    special: str | None
    extra_info: list[str]

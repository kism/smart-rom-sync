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


class ConfigDef:
    """Configuration definition for the sync tool."""

    target: TargetDef
    systems: list[SystemDef]

    def __init__(self, target: TargetDef, systems: list[SystemDef]) -> None:
        """Initialize the configuration with target and systems."""
        self.target = target
        self.systems = systems

        self.validate()

    def validate(self) -> None:
        """Validate the configuration."""
        errors = []

        if not self.target["path"]:
            errors.append("Target path is required.")
        if not self.systems:
            errors.append("At least one system is required.")
        for n, system in enumerate(self.systems):
            if not system["local_dir"] or not system["remote_dir"]:
                errors.append(f"System {n} Both local and remote directories are required.")

        if errors:
            msg = "Configuration validation failed! \n  " + "\n  ".join(errors)
            raise ValueError(msg)


class ReleaseInfo(TypedDict):
    """Release information for a file."""

    region_dir: str
    region_full: str
    special: str | None
    extra_info: list[str]

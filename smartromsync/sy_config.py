"""Functions to load and parse the configuration file."""

import tomllib
from pathlib import Path

from .sy_types import SystemDef, TargetDef


class ConfigDef:
    """Configuration definition for the sync tool."""

    def __init__(
        self,
        config_file_path: Path | None = None,
        target: TargetDef | None = None,
        systems: list[SystemDef] | None = None,
    ) -> None:
        """Initialize the configuration with target and systems."""
        self.target = target
        self.systems = systems

        if isinstance(config_file_path, Path):
            self.target, self.systems = self.load_config_from_toml(config_file_path)

        self.validate()

    def load_config_from_toml(self, config_file: Path) -> tuple[TargetDef, list[SystemDef]]:
        """Load the configuration from a TOML file."""
        config_error: str = ""

        if not config_file.exists():
            config_error += f"Config file {config_file} does not exist.\n"

        with config_file.open("rb") as f:
            config_toml = tomllib.load(f)

        target_tmp = config_toml.get("target", {})

        target: TargetDef = TargetDef(
            type=target_tmp.get("type", "local"),  # local, remote
            rsync_host=target_tmp.get("rsync_host", ""),  # user@host
            path=target_tmp.get("path", ""),
        )

        systems_temp = config_toml.get("systems", [])

        systems_list = []

        for system_def_raw in systems_temp:
            local_dir: Path | None = system_def_raw.get("local_dir", None)
            remote_dir: Path | None = system_def_raw.get("remote_dir", None)

            system_def = SystemDef(
                local_dir=local_dir,
                remote_dir=remote_dir,
                region_list_include=system_def_raw.get("region_list_include", []),
                region_list_exclude=system_def_raw.get("region_list_exclude", []),
                special_list_include=system_def_raw.get("special_list_include", []),
                special_list_exclude=system_def_raw.get("special_list_exclude", []),
            )
            systems_list.append(system_def)

        return target, systems_list

    def validate(self) -> None:
        """Validate the configuration."""
        errors = []

        if not self.target or not self.target["path"]:
            errors.append("Target path is required.")
        if not self.systems:
            errors.append("At least one system is required.")
        else:
            for n, system in enumerate(self.systems):
                if not system["local_dir"] or not system["remote_dir"]:
                    errors.append(f"System {n} Both local and remote directories are required.")

        if errors:
            msg = "Configuration validation failed! \n  " + "\n  ".join(errors)
            raise ValueError(msg)

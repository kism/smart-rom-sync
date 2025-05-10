"""Functions to load and parse the configuration file."""

import tomllib
from pathlib import Path

from .sy_types import ConfigDef, SystemDef, TargetDef


def load_config_from_toml(config_file: Path) -> ConfigDef:
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

    config: ConfigDef = ConfigDef(target=target, systems=systems_list)

    return config

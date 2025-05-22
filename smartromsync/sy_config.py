"""Config loading, setup, validating, writing."""

import json
from pathlib import Path
from typing import Self

import tomlkit
from pydantic import BaseModel, model_validator
from pydantic_settings import BaseSettings

from .logger import get_logger

# Logging should be all done at INFO level or higher as the log level hasn't been set yet
# Modules should all setup logging like this so the log messages include the modules name.
logger = get_logger(__name__)


class Target(BaseModel):
    """Flask configuration definition."""

    type: str = "local"
    remote_host: str = ""
    path: Path = Path()

    @model_validator(mode="after")
    def validate_config(self) -> Self:
        """Validate the configuration."""
        if self.type not in ["rsync", "local"]:
            msg = f"Invalid target type: {self.type}. Must be 'rsync' or 'local'."
            logger.error(msg)
        return self


class System(BaseModel):
    """Application configuration definition."""

    local_dir: Path = Path()
    remote_dir: Path = Path()
    region_list_include: list[str] = []
    region_list_exclude: list[str] = []
    special_list_include: list[str] = []
    special_list_exclude: list[str] = []

    @model_validator(mode="after")
    def validate_config(self) -> Self:
        """Validate the configuration."""
        if self.local_dir == self.remote_dir:
            msg = "local_dir and remote_dir cannot be the same."
            logger.error(msg)

        return self


class ConfigDef(BaseSettings):
    """Settings loaded from a TOML file."""

    # Default values for our settings
    target: Target = Target()
    systems: list[System] = []

    def write_config(self, config_location: Path) -> None:
        """Write the current settings to a TOML file."""
        logger.info("Writing config to %s", config_location)
        config_data = json.loads(self.model_dump_json())  # This is how we make the object safe for tomlkit

        # Write to the TOML file
        if not config_location.parent.exists():
            config_location.parent.mkdir(parents=True, exist_ok=True)

        with config_location.open("w") as f:
            tomlkit.dump(config_data, f)


def load_config(config_path: Path) -> ConfigDef:
    """Load the configuration file."""
    import tomlkit

    if not config_path.exists():
        return ConfigDef()

    with config_path.open("r") as f:
        config = tomlkit.load(f)

    return ConfigDef(**config)

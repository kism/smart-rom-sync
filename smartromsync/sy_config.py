"""Config loading, setup, validating, writing."""

import datetime
import json
import os
from pathlib import Path
from typing import Self

import tomlkit
from pydantic import BaseModel, ConfigDict, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from . import PROGRAM_NAME, URL, __version__
from .logger import get_logger

# Logging should be all done at INFO level or higher as the log level hasn't been set yet
# Modules should all setup logging like this so the log messages include the modules name.
logger = get_logger(__name__)


class Target(BaseModel):
    """Flask configuration definition."""

    model_config = ConfigDict(extra="allow")  # Fine for config

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

    model_config = ConfigDict(extra="allow")  # Fine for config

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
        if self.remote_dir.is_absolute():
            # Convert to relative path if it's absolute
            self.remote_dir = Path(str(self.remote_dir).lstrip(os.sep))  # Bit of a HACK to remove leading slashes

        return self


class ConfigDef(BaseSettings):
    """Settings loaded from a TOML file."""

    model_config = SettingsConfigDict(extra="allow")  # Fine for config

    # Default values for our settings
    target: Target = Target()
    systems: list[System] = []

    def write_config(self, config_location: Path) -> None:
        """Write the current settings to a TOML file."""
        config_location.parent.mkdir(parents=True, exist_ok=True)

        config_location.parent.mkdir(parents=True, exist_ok=True)

        config_data = json.loads(self.model_dump_json())  # This is how we make the object safe for tomlkit
        if not config_location.exists():
            logger.warning("Config file does not exist, creating it at %s", config_location)
            config_location.touch()
            existing_data = config_data
        else:
            with config_location.open("r") as f:
                existing_data = tomlkit.load(f)

        logger.info("Writing config to %s", config_location)

        new_file_content_str = f"# Configuration file for {PROGRAM_NAME} v{__version__} {URL}\n"
        new_file_content_str += tomlkit.dumps(config_data)

        if existing_data != config_data:  # The new object will be valid, so we back up the old one
            time_str = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
            backup_file = config_location.parent / f"{config_location.stem}_{time_str}{config_location.suffix}.bak"
            logger.warning("Validation has changed the config file, backing up the old one to %s", backup_file)
            with backup_file.open("w") as f:
                f.write(tomlkit.dumps(existing_data))
        if not config_location.exists():
            logger.warning("Config file does not exist, creating it at %s", config_location)
            config_location.touch()
            existing_data = config_data
        else:
            with config_location.open("r") as f:
                existing_data = tomlkit.load(f)

        logger.info("Writing config to %s", config_location)

        new_file_content_str = f"# Configuration file for {PROGRAM_NAME} v{__version__} {URL}\n"
        new_file_content_str += tomlkit.dumps(config_data)

        if existing_data != config_data:  # The new object will be valid, so we back up the old one
            time_str = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
            backup_file = config_location.parent / f"{config_location.stem}_{time_str}{config_location.suffix}.bak"
            logger.warning("Validation has changed the config file, backing up the old one to %s", backup_file)
            with backup_file.open("w") as f:
                f.write(tomlkit.dumps(existing_data))

        with config_location.open("w") as f:
            f.write(new_file_content_str)

    def print_config(self) -> None:
        """Print the current configuration."""
        msg = f"""{PROGRAM_NAME} v{__version__} {URL}
Current configuration:
  Target Type: {self.target.type}
  Remote Host: {self.target.remote_host}
  Remote base path: {self.target.path}
  Systems: {len(self.systems)}"""

        logger.info(msg)

    @classmethod
    def load_config(cls, config_path: Path) -> Self:
        """Load the configuration file."""
        if not config_path.exists():
            return cls()

        with config_path.open("r") as f:
            config = tomlkit.load(f)

        return cls(**config)

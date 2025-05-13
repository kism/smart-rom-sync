"""Config loading, setup, validating, writing."""

import json
from pathlib import Path
from typing import Self

import tomlkit
from pydantic import BaseModel, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

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
    def custom_validate(self) -> Self:
        """Validate the configuration."""
        if self.type not in ["rsync", "local"]:
            msg = f"Invalid target type: {self.type}. Must be 'remote' or 'local'."
            raise ValueError(msg)

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
    def custom_validate(self) -> Self:
        """Validate the configuration."""
        if self.local_dir == self.remote_dir:
            msg = "local_dir and remote_dir cannot be the same."
            raise ValueError(msg)

        return self


class ConfigDef(BaseSettings):
    """Settings loaded from a TOML file."""

    # Default values for our settings
    target: Target = Target()
    systems: list[System] = []

    # Custom path for the config file
    config_path: Path = Path()

    # Configure settings class
    model_config = SettingsConfigDict(
        env_prefix="APP_",  # environment variables with APP_ prefix will override settings
        env_nested_delimiter="__",  # APP_NESTED__NESTED_FIELD=value
        json_encoders={Path: str},
    )

    def __init__(self, config_path: Path) -> None:
        """Initialize settings and load from a TOML file if provided.

        Args:
            config_path (Path): Path to load config.toml
        """
        # Initialize with default values first
        super().__init__()

        self.config_path = config_path
        self._load_from_toml()
        self.write_config()

    def _load_from_toml(self) -> None:
        """Load settings from the TOML file specified in config_path."""
        if self.config_path.is_dir():
            msg = f"Config path '{self.config_path}' is a directory, not a file."
            raise ValueError(msg)

        if self.config_path.is_file():
            with self.config_path.open("r") as f:
                config_data = tomlkit.load(f)

            # Update our settings from the loaded data
            for key, value in config_data.items():
                if key == "target" and isinstance(value, dict):
                    self.target = Target(**value)
                elif key == "systems" and isinstance(value, list):
                    self.systems = [System(**system) for system in value]
                elif hasattr(self, key):
                    setattr(self, key, value)

    def write_config(self) -> None:
        """Write the current settings to a TOML file."""
        logger.info("Writing config to %s", self.config_path)
        config_data = json.loads(self.model_dump_json())  # This is how we make the object safe for tomlkit
        config_data.pop("config_path", None)  # Remove config_path from the data to be written

        # Write to the TOML file
        if not self.config_path.parent.exists():
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

        with self.config_path.open("w") as f:
            tomlkit.dump(config_data, f)

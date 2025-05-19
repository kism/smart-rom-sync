"""Config loading, setup, validating, writing."""

import json
from pathlib import Path
from typing import Self

import tomlkit
from pydantic import BaseModel, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict, PydanticBaseSettingsSource, TomlConfigSettingsSource

from .logger import get_logger

# Logging should be all done at INFO level or higher as the log level hasn't been set yet
# Modules should all setup logging like this so the log messages include the modules name.
logger = get_logger(__name__)

CONFIG_LOCATION = Path() / "config.toml"


class Target(BaseModel):
    """Flask configuration definition."""

    type: str = "local"
    remote_host: str = ""
    path: Path = Path()

    @model_validator(mode="after")
    def validate_config(self) -> Self:
        """Validate the configuration."""
        if self.type not in ["rsync", "local"]:
            msg = f"Invalid target type: {self.type}. Must be 'remote' or 'local'."
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

    # Configure settings class
    model_config = SettingsConfigDict(
        env_prefix="APP_",  # environment variables with APP_ prefix will override settings
        env_nested_delimiter="__",  # APP_NESTED__NESTED_FIELD=value
        json_encoders={Path: str},
        toml_file=CONFIG_LOCATION,
    )

    @classmethod  # This is magic, required and I don't understand it
    def settings_customise_sources(  # noqa: D102
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,  # noqa: ARG003
        env_settings: PydanticBaseSettingsSource,  # noqa: ARG003
        dotenv_settings: PydanticBaseSettingsSource,  # noqa: ARG003
        file_secret_settings: PydanticBaseSettingsSource,  # noqa: ARG003
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (TomlConfigSettingsSource(settings_cls),)

    def _load_from_toml(self) -> None:
        """Load settings from the TOML file specified in config_path."""
        if CONFIG_LOCATION.is_file():
            with CONFIG_LOCATION.open("r") as f:
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
        logger.info("Writing config to %s", CONFIG_LOCATION)
        config_data = json.loads(self.model_dump_json())  # This is how we make the object safe for tomlkit

        # Write to the TOML file
        if not CONFIG_LOCATION.parent.exists():
            CONFIG_LOCATION.parent.mkdir(parents=True, exist_ok=True)

        with CONFIG_LOCATION.open("w") as f:
            tomlkit.dump(config_data, f)

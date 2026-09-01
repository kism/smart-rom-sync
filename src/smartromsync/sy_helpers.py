"""Helper functions for smartromsync."""

import platform
from pathlib import Path


def get_system_temp_folder() -> Path:
    """Get the system temp folder."""
    if platform.system() == "Windows":
        return Path("~\\AppData\\Local\\Temp")

    return Path("/tmp")  # noqa: S108

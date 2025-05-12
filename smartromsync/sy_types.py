"""Smart ROM Sync Tool Types."""

from typing import TypedDict


class ReleaseInfo(TypedDict):
    """Release information for a file."""

    region_dir: str
    region_full: str
    special: str | None
    extra_info: list[str]

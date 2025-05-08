"""Sync object for a system."""

import logging
import re
from pathlib import Path
from typing import ClassVar

from .sy_types import ReleaseInfo, SystemDef, TargetDef

logger = logging.getLogger(__name__)

class SystemSync:
    """Sync object for a system."""

    SPECIAL_DIR_CRITERIA: ClassVar = {
        "Demo": ["Demo"],
        "Aftermarket": ["Aftermarket"],
        "Unlicensed": ["Unlicensed", "Unl", "Pirate"],
        "Unreleased": ["Unreleased", "Proto"],
    }

    REGION_ALWAYS_ALLOWED: ClassVar = [
        "World",
        "Unknown",
    ]

    REGION_LIST: ClassVar = [
        "USA",  # Sorry, highest precedence when it comes to retro gaming
        "Europe",
        "Japan",
        "World",
        "Asia",
        "Korea",
        "Australia",
        "Germany",
        "France",
        "Italy",
        "Taiwan",
        "Sweden",
        "Spain",
        "Unknown",
        "Hong Kong",
        "China",
        "Brazil",
        "Canada",
    ]

    def __init__(self, system_def: SystemDef, target_def: TargetDef, *, dry_run: bool = False) -> None:
        """Initialize the sync object with the system and target definitions."""
        self.all_files: list[Path] = []
        self.dry_run = dry_run

        self.target_def = target_def
        self.rsync_host_str: str = ""
        if self.target_def["type"] == "remote":
            self.rsync_host_str = f"{self.target_def['rsync_host']}:"

        local_dir: Path | None = system_def.get("local_dir")
        if not local_dir:
            msg = "local_dir is required"
            raise ValueError(msg)
        self.local_dir = local_dir

        remote_dir: Path | None = system_def.get("remote_dir")
        if not remote_dir:
            msg = "remote_dir is required"
            raise ValueError(msg)

        self.remote_dir = remote_dir
        self.remote_dir_full = str(Path(f"{self.target_def['path']}/{self.remote_dir}"))

        self.region_list_include: list[str] = system_def.get("region_list_include", [])
        self.region_list_exclude: list[str] = system_def.get("region_list_exclude", [])

        self.special_list_include: list[str] = system_def.get("special_list_include", [])
        self.special_list_exclude: list[str] = system_def.get("special_list_exclude", [])

        self.rsync_inputs: dict[str, list[Path]] = self._get_files_to_push()

    def print_summary(self) -> None:
        """Print a summary of the sync object."""
        logger.info("Found %s folders to push to", len(self.rsync_inputs.keys()))

    def rsync(self) -> None:
        """Run the rsync command to sync the files."""
        rsync_file_list = Path.cwd() / "rsync_file_list.txt"

        for dest_folder, files in self.rsync_inputs.items():
            logger.info("Syncing %s files to %s...", len(files), dest_folder)
            with rsync_file_list.open("w") as f:
                for file in files:
                    f.write(f"{file}\n")

            rsync_cmd = [
                "rsync",
                "-av",
                "--info=progress2",
                f"--files-from={rsync_file_list}",
                f"{self.rsync_host_str}{dest_folder}",
            ]
            if self.dry_run:
                logger.info(rsync_cmd)

        rsync_file_list.unlink(missing_ok=True)

    def _create_rsync_file_list(self) -> None:
        pass

    def _get_file_list(self) -> None:
        all_files = Path(self.local_dir).rglob("*")
        self.all_files = [f for f in all_files if f.is_file()]
        logger.info("Found %s files in %s", len(self.all_files), self.local_dir)

    def _get_region(self, release_info_raw: list[str]) -> tuple[str, str, int | None]:
        # Check for exact match
        current_candidate_region: str | None = None
        region_index: int | None = None
        for n, release_snippet in enumerate(release_info_raw):
            if release_snippet in self.REGION_LIST:
                # The furtherst match is the region, would be crazy otherwise
                current_candidate_region = release_snippet
                region_index = n

        if current_candidate_region:
            return current_candidate_region, current_candidate_region, region_index

        # Check for partial match
        region_list_reversed = self.REGION_LIST[
            ::-1
        ]  # Reversing the list, so that precidence in country name is matched.
        for n, release_snippet in enumerate(release_info_raw):
            for region in region_list_reversed:
                if region in release_snippet:
                    # The furtherst match is the region, would be crazy otherwise
                    current_candidate_region = region
                    region_full_str = release_snippet
                    region_index = n

        if current_candidate_region:
            return current_candidate_region, region_full_str, region_index

        logger.info("Region not found in %s ", release_info_raw)

        return "Unknown", "Unknown", None

    def _get_special(self, release_info_raw: list[str]) -> str | None:
        # Check for exact match
        for release_snippet in release_info_raw:
            for special, equivalents in self.SPECIAL_DIR_CRITERIA.items():
                for equiv in equivalents:
                    if equiv in release_snippet:
                        return special  # First match wins

        return None

    def _get_release_info(self, filename: str) -> ReleaseInfo:
        # Parse the No-Intro/Redump naming convention
        # Make a list of everything in brackets
        bracket_contents = re.findall(r"\((.*?)\)", filename)
        # Ensure that we have a list of strings, what is the typing of re even?
        bracket_contents = [str(x) for x in bracket_contents]

        region_dir, region_full, idx = self._get_region(bracket_contents)
        if idx:
            bracket_contents.pop(idx)  # Remove the region from the list

        special = self._get_special(bracket_contents)

        return ReleaseInfo(region_dir=region_dir, region_full=region_full, special=special, extra_info=bracket_contents)

    def _check_allowed_special(self, release_info: ReleaseInfo) -> bool:
        for extra_info in release_info["extra_info"]:
            for special_to_exclude in self.special_list_exclude:
                if special_to_exclude in extra_info:
                    return False

        if self.special_list_include:
            for extra_info in release_info["extra_info"]:
                for special_to_include in self.special_list_include:
                    if special_to_include in extra_info:
                        return True
            return False

        return True

    def _check_allowed_region(self, release_info: ReleaseInfo) -> bool:
        for region in self.region_list_exclude:
            if region in release_info["region_full"]:
                return False

        if self.region_list_include:
            temp_region_list = []
            temp_region_list.extend(self.region_list_include)
            temp_region_list.extend(self.REGION_ALWAYS_ALLOWED)
            return any(region in release_info["region_full"] for region in temp_region_list)

        return True

    def _get_files_to_push(self) -> dict[str, list[Path]]:
        if not self.all_files:
            self._get_file_list()

        files_to_push: dict[str, list[Path]] = {}

        for file_path in self.all_files:
            release_info = self._get_release_info(file_path.name)
            allowed_special = self._check_allowed_special(release_info)
            allowed_region = self._check_allowed_region(release_info)

            if allowed_special and allowed_region:
                output_dir_str = release_info["region_dir"]
                if release_info["special"]:
                    output_dir_str = release_info["special"]

                output_dir_str = str(Path(f"{self.remote_dir_full}/{output_dir_str}"))
                if not files_to_push.get(output_dir_str):
                    files_to_push[output_dir_str] = []

                files_to_push[output_dir_str].append(file_path)

        return files_to_push

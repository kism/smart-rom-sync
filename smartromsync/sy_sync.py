"""Sync object for a system."""

import re
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, TypedDict

from .logger import get_logger
from .sy_helpers import get_system_temp_folder

if TYPE_CHECKING:
    from .sy_config import System, Target
else:
    System = object
    Target = object

logger = get_logger(__name__)


class ReleaseInfo(TypedDict):
    """Release information for a file."""

    region_dir: str
    region_full: str
    special: str | None
    extra_info: list[str]


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
        "Russia",
        "United Kingdom",
        "Latin America",
        "Netherlands",
        "Scandinavia",
        "Argentina",
        "Mexico",
        "Denmark",
    ]

    def __init__(self, system: System, target: Target, *, dry_run: bool = False, no_run: bool = False) -> None:
        """Initialize the sync object with the system and target definitions."""
        self.all_files: list[Path] = []
        self.dry_run = dry_run
        self.no_run = no_run

        self.system: System = system
        self.target: Target = target
        self.rsync_host_str: str = ""
        if self.target.type == "rsync":
            self.rsync_host_str = f"{self.target.remote_host}"

        self.remote_dir_full = str(self.target.path / system.remote_dir)

        self.rsync_inputs: dict[str, list[str]] = self._get_files_to_push()

    def print_summary(self) -> None:
        """Print a summary of the sync object."""
        logger.info("Found %s folders to push to", len(self.rsync_inputs.keys()))

    def rsync(self) -> str:
        """Run the rsync command to sync the files."""
        tmp_folder = get_system_temp_folder()
        stats: str = f"  {self.system.local_dir} -> {self.remote_dir_full}\n"

        for dest_folder, files in self.rsync_inputs.items():
            stats += f"    {dest_folder}: {len(files)} files\n"
            logger.info("Syncing %s files to %s...", len(files), dest_folder)

            rsync_file_list = tmp_folder / f"rsync_fl{dest_folder.replace('/', '_')}.txt"
            logger.debug("rsync file list: %s", rsync_file_list)

            with rsync_file_list.open("w") as f:
                for file in files:
                    f.write(f"{file}\n")

            rsync_options = "-hv"
            if self.dry_run:
                rsync_options = rsync_options + "n"

            rsync_dest = dest_folder
            if self.rsync_host_str:
                rsync_dest = f"{self.rsync_host_str}:{dest_folder}"

            rsync_cmd = (
                "rsync",
                rsync_options,
                "--info=progress2",
                "--size-only",
                f"--files-from={rsync_file_list}",
                f"{self.system.local_dir}",
                rsync_dest,
            )

            mkdir_command = ["mkdir", "-p", dest_folder]
            if self.rsync_host_str:
                mkdir_command = ["ssh", self.rsync_host_str, "mkdir", "-p", dest_folder]

            if not self.no_run:
                logger.info("rsync command: %s", " ".join(rsync_cmd))
                logger.info("mkdir command: %s", " ".join(mkdir_command))

                logger.info("Running rsync")
                if not self.dry_run:
                    # Create the remote directory if it doesn't exist
                    logger.info("Creating destination directory with command %s", mkdir_command)
                    subprocess.run(mkdir_command, shell=False, check=True)  # noqa: S603

                subprocess.run(rsync_cmd, shell=False, check=True)  # noqa: S603
                logger.info("Rsync completed!")

        return stats

    def _get_file_list(self) -> None:
        if not self.system.local_dir.is_dir():
            logger.error("Local directory %s is not a directory", self.system.local_dir)
            return

        all_files = Path(self.system.local_dir).rglob("*")
        self.all_files = [f for f in all_files if f.is_file()]
        logger.info("Found %s files in %s", len(self.all_files), self.system.local_dir)

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

        logger.warning("Region not found in %s ", release_info_raw)

        return "Unknown", "Unknown", None

    def _get_special(self, release_info_raw: list[str]) -> str | None:
        # Check for exact match
        for release_snippet in release_info_raw:
            for special, equivalents in self.SPECIAL_DIR_CRITERIA.items():
                for equiv in equivalents:
                    if equiv in release_snippet:
                        if not isinstance(special, str):
                            msg = f"Expected str, got {type(special)}"
                            raise TypeError(msg)
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
            for special_to_exclude in self.system.special_list_exclude:
                if special_to_exclude in extra_info:
                    return False

        if self.system.special_list_include:
            for extra_info in release_info["extra_info"]:
                for special_to_include in self.system.special_list_include:
                    if special_to_include in extra_info:
                        return True
            return False

        return True

    def _check_allowed_region(self, release_info: ReleaseInfo) -> bool:
        for region in self.system.region_list_exclude:
            if region in release_info["region_full"]:
                return False

        if self.system.region_list_include:
            temp_region_list = []
            temp_region_list.extend(self.system.region_list_include)
            temp_region_list.extend(self.REGION_ALWAYS_ALLOWED)
            return any(region in release_info["region_full"] for region in temp_region_list)

        return True

    def _get_files_to_push(self) -> dict[str, list[str]]:
        if not self.all_files:
            self._get_file_list()

        files_to_push: dict[str, list[str]] = {}

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

                files_to_push[output_dir_str].append(file_path.name)

        return files_to_push

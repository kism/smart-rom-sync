"""Main entry point for the smart-rom-sync program."""

import argparse
import logging
import tomllib
from pathlib import Path

from .sy_sync import SystemSync
from .sy_types import SystemDef, TargetDef

logger = logging.getLogger(__name__)


def main() -> None:
    """Main function to run the script."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    parser = argparse.ArgumentParser(description="Build a sync list for the specified ROMs.")
    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Run the script with rsync in dry run mode.",
    )
    parser.add_argument(
        "--no-run",
        action="store_true",
        help="Run the script, just print the rsync commands.",
    )
    parser.add_argument(
        "config_file",
        type=str,
        help="Path to the config file containing the list of ROMs.",
    )

    args = parser.parse_args()
    config_file = Path(args.config_file)

    with config_file.open("rb") as f:
        config = tomllib.load(f)
    target_tmp = config.get("target", [])
    target: TargetDef = TargetDef(
        type=target_tmp.get("type", ""),
        rsync_host=target_tmp.get("rsync_host", ""),
        path=target_tmp.get("path", ""),
    )

    systems = config.get("systems", [])

    for system_def_raw in systems:
        print()  # noqa: T201 # Just to make the output nicer
        system_def = SystemDef(
            local_dir=Path(system_def_raw["local_dir"]),
            remote_dir=Path(system_def_raw["remote_dir"]),
            region_list_include=system_def_raw.get("region_list_include", []),
            region_list_exclude=system_def_raw.get("region_list_exclude", []),
            special_list_include=system_def_raw.get("special_list_include", []),
            special_list_exclude=system_def_raw.get("special_list_exclude", []),
        )

        logger.info("Processing %s...", system_def["local_dir"])
        system = SystemSync(system_def=system_def, target_def=target, dry_run=args.dry_run, no_run=args.no_run)
        system.print_summary()
        system.rsync()


if __name__ == "__main__":
    main()

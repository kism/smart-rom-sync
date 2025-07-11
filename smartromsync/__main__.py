"""Main entry point for the smart-rom-sync program."""

import argparse
import time
from pathlib import Path

from smartromsync.sy_config import ConfigDef

from .logger import get_logger, setup_logger
from .sy_sync import SystemSync

logger = get_logger(__name__)


def main() -> None:
    """Main function to run the script."""
    setup_logger()

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
        "--log-level",
        type=str,
        default="INFO",
        help="Set the logging level (default: INFO)",
    )
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        default="config.toml",
        help="Path to the configuration file (default: config.toml)",
    )

    args = parser.parse_args()

    config_file = Path(args.config)

    config = ConfigDef.load_config(config_file)
    config.print_config()
    for _ in range(5):
        print(".", end="")  # noqa: T201
        time.sleep(1)
    print()  # noqa: T201 # Just to make the output nicer
    config.write_config(config_file)

    stats = []

    for system in config.systems:
        print()  # noqa: T201 # Just to make the output nicer

        logger.info("Processing %s...", system.local_dir)
        system_sync = SystemSync(system=system, target=config.target, dry_run=args.dry_run, no_run=args.no_run)
        system_sync.print_summary()
        stats.append(system_sync.rsync())

    logger.info("Stats:")
    for stat in stats:
        logger.info(stat)


if __name__ == "__main__":
    main()

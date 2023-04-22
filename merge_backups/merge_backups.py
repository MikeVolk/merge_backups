import argparse
import os
import logging
from backend import merge_backup


def setup_logging(verbose):
    """
    Set up logging based on the verbose flag.

    :param verbose: Boolean, enable verbose output if True
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")


def validate_arguments(folder_to_backup, backup_location):
    """
    Validate the given folder_to_backup and backup_location paths.

    :param folder_to_backup: Path to the folder to be backed up
    :param backup_location: Path to the backup location
    :raises ValueError: If the given paths are invalid or not directories
    """
    if not os.path.exists(folder_to_backup):
        raise ValueError(f"Folder to backup '{folder_to_backup}' does not exist.")

    if not os.path.exists(backup_location):
        raise ValueError(f"Backup location '{backup_location}' does not exist.")

    if not os.path.isdir(folder_to_backup):
        raise ValueError(f"Folder to backup '{folder_to_backup}' is not a directory.")

    if not os.path.isdir(backup_location):
        raise ValueError(f"Backup location '{backup_location}' is not a directory.")


def main():
    """
    Main function to parse command line arguments, validate them, and call the merge_backup function.

    This script merges backups and moves older versions to .oldversion folders. It takes two required
    positional arguments, folder_to_backup and backup_location, and two optional flags, --verbose and
    --dry_run.

    Example usage:

    python script.py /path/to/folder_to_backup /path/to/backup_location --verbose --dry_run
    """
    parser = argparse.ArgumentParser(
        description="Merge backups and move older versions to .oldversion folders"
    )
    parser.add_argument(
        "folder_to_backup",
        help="Path to the folder to be backed up. This folder must exist and be a directory.",
    )
    parser.add_argument(
        "backup_location",
        help="Path to the backup location. This folder must exist and be a directory.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output. This will display additional information about the backup process.",
    )
    parser.add_argument(
        "-d",
        "--dry_run",
        action="store_true",
        help="Perform a dry run without actually copying files. Use this option to check the backup process without making changes to the file system.",
    )

    args = parser.parse_args()

    try:
        validate_arguments(args.folder_to_backup, args.backup_location)
        merge_backup(args.folder_to_backup, args.backup_location, args.verbose, args.dry_run)
    except ValueError as e:
        logging.error(e)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()

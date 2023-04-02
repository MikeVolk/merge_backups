import argparse
from backup_merger.merger import merge_backup


def main():
    parser = argparse.ArgumentParser(
        description="Merge backups and move older versions to .oldversion folders"
    )
    parser.add_argument("folder_to_backup", help="Path to the folder to be backed up")
    parser.add_argument("backup_location", help="Path to the backup location")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument(
        "-d",
        "--dry_run",
        action="store_true",
        help="Perform a dry run without actually copying files",
    )

    args = parser.parse_args()

    merge_backup(args.folder_to_backup, args.backup_location, args.verbose, args.dry_run)


if __name__ == "__main__":
    main()

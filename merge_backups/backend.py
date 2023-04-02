"""
merger.py

This script provides a function to merge backup folders by comparing and copying
files between the folder to be backed up and the backup location. If a file is
found in both locations, the newest file is kept, and the older file is renamed
by appending its last modified timestamp and moved to a '.oldversion' subfolder.
If the files are identical, the duplicate file in the folder to be backed up is
deleted.

The merge_backup function accepts the following arguments:
    folder_to_backup (str): The path of the folder to be backed up.
    backup_location (str): The path of the backup location.
    verbose (bool, optional): If True, displays log messages to the console.
                              Default is False.
    dry_run (bool, optional): If True, only displays the log messages of what
                              would be done without actually executing the
                              operations. Default is False.

Example usage:
    merge_backup("path/to/folder_to_backup", "path/to/backup_location", verbose=True)

"""

import filecmp
import logging
import os
import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path


def build_file_tree(root):
    file_tree = {}

    for entry in os.scandir(root):
        if entry.is_file():
            rel_path = os.path.relpath(entry.path, root)
            file_tree[rel_path] = entry.stat().st_mtime
        elif entry.is_dir():
            subdir_tree = build_file_tree(entry.path)
            for subpath, mtime in subdir_tree.items():
                file_tree[os.path.join(entry.name, subpath)] = mtime

    return file_tree


def merge_backup(folder_to_backup, backup_location, verbose=False, dry_run=False):
    """
    Merge a folder to be backed up with a backup location, handling file
    conflicts by keeping the newest file and moving the older version to a
    '.oldversion' subfolder. Identical files in both locations will result in
    the deletion of the file in the folder to be backed up.

    Args:
        folder_to_backup (str): The path of the folder to be backed up.
        backup_location (str): The path of the backup location.
        verbose (bool, optional): If True, displays log messages to the console.
                                  Default is False.
        dry_run (bool, optional): If True, only displays the log messages of what
                                  would be done without actually executing the
                                  operations. Default is False.
    """

    # Configure logging settings
    log_file_path = os.path.join(backup_location, "backup_merger.log")
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    log_level = logging.INFO if verbose else logging.WARNING

    logging.basicConfig(filename=log_file_path, level=log_level, format=log_format, filemode="w")

    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(log_format))

    if verbose:
        logging.getLogger().addHandler(console_handler)

    folder_to_backup_tree = build_file_tree(folder_to_backup)
    backup_location_tree = build_file_tree(backup_location)

    for rel_path, source_mtime in folder_to_backup_tree.items():
        source_file_path = os.path.join(folder_to_backup, rel_path)
        dest_file_path = os.path.join(backup_location, rel_path)

        if rel_path in backup_location_tree:
            dest_mtime = backup_location_tree[rel_path]

            if filecmp.cmp(source_file_path, dest_file_path, shallow=False):
                logging.info(f"Files are the same, deleting {source_file_path}")
                if not dry_run:
                    os.remove(source_file_path)
            else:
                old_versions_dir = os.path.join(os.path.dirname(dest_file_path), ".oldversion")
                if not dry_run:
                    Path(old_versions_dir).mkdir(exist_ok=True)

                if source_mtime > dest_mtime:
                    old_version_datetime = datetime.fromtimestamp(dest_mtime).strftime(
                        "%Y%m%d_%H%M%S"
                    )
                    old_version_filename = f"{os.path.splitext(os.path.basename(rel_path))[0]}_{old_version_datetime}{os.path.splitext(os.path.basename(rel_path))[1]}"
                    old_version_path = os.path.join(old_versions_dir, old_version_filename)
                    logging.info(f"Moving {dest_file_path} to {old_version_path}")
                    logging.info(f"Copying {source_file_path} to {dest_file_path}")
                    if not dry_run:
                        shutil.move(dest_file_path, old_version_path)
                        shutil.copy2(source_file_path, dest_file_path)
                elif source_mtime < dest_mtime:
                    old_version_datetime = datetime.fromtimestamp(source_mtime).strftime(
                        "%Y%m%d_%H%M%S"
                    )
                    old_version_filename = f"{os.path.splitext(os.path.basename(rel_path))[0]}_{old_version_datetime}{os.path.splitext(os.path.basename(rel_path))[1]}"
                    old_version_path = os.path.join(old_versions_dir, old_version_filename)
                    logging.info(f"Moving {source_file_path} to {old_version_path}")
                    if not dry_run:
                        shutil.move(source_file_path, old_version_path)
        else:
            logging.info(f"Copying {source_file_path} to {dest_file_path}")
            if not dry_run:
                Path(os.path.dirname(dest_file_path)).mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_file_path, dest_file_path)


def create_test_file(path, content, modified_time=None):
    with open(path, "w") as f:
        f.write(content)

    if modified_time:
        os.utime(path, (modified_time.timestamp(), modified_time.timestamp()))


def create_test_files_and_folders():
    folder_to_backup = "folder_to_backup"
    backup_location = "backup_location"

    # Remove existing folders if they exist
    if os.path.exists(folder_to_backup):
        shutil.rmtree(folder_to_backup)

    if os.path.exists(backup_location):
        shutil.rmtree(backup_location)

    # Create folder_to_backup structure
    Path(folder_to_backup).mkdir(exist_ok=True)
    Path(os.path.join(folder_to_backup, "subdir1")).mkdir(exist_ok=True)

    current_time = datetime.now()
    create_test_file(os.path.join(folder_to_backup, "file1.txt"), "File1 content\n", current_time)
    create_test_file(os.path.join(folder_to_backup, "file2.txt"), "File2 content\n", current_time)
    create_test_file(os.path.join(folder_to_backup, "file3.txt"), "File3 content\n", current_time)
    create_test_file(
        os.path.join(folder_to_backup, "subdir1", "file4.txt"), "File4 content\n", current_time
    )
    create_test_file(
        os.path.join(folder_to_backup, "subdir1", "file5.txt"), "File5 content\n", current_time
    )

    # Create backup_location structure
    backup_location = "backup_location"
    Path(backup_location).mkdir(exist_ok=True)
    Path(os.path.join(backup_location, "subdir1")).mkdir(exist_ok=True)

    create_test_file(
        os.path.join(backup_location, "file1.txt"),
        "File1 older content\n",
        current_time - timedelta(days=1),
    )
    create_test_file(os.path.join(backup_location, "file2.txt"), "File2 content\n", current_time)
    create_test_file(
        os.path.join(backup_location, "subdir1", "file4.txt"),
        "File4 newer content\n",
        current_time + timedelta(days=1),
    )
    create_test_file(
        os.path.join(backup_location, "subdir1", "file6.txt"), "File6 content\n", current_time
    )


if __name__ == "__main__":
    create_test_files_and_folders()
    merge_backup("folder_to_backup", "backup_location", verbose=True, dry_run=False)

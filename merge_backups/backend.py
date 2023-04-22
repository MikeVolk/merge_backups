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
    """
    Build a file tree dictionary with relative paths as keys and modification times as values.

    :param root: Path to the root directory
    :return: Dictionary containing the file tree with relative paths and their modification times
    """
    file_tree = {}

    for entry in os.scandir(root):
        if entry.is_file():
            # Calculate the relative path and store the file's modification time
            rel_path = os.path.relpath(entry.path, root)
            file_tree[rel_path] = entry.stat().st_mtime
        elif entry.is_dir():
            # Recursively build the file tree for the subdirectory
            subdir_tree = build_file_tree(entry.path)
            # Merge the subdirectory tree with the main file tree
            for subpath, mtime in subdir_tree.items():
                file_tree[os.path.join(entry.name, subpath)] = mtime

    return file_tree


def is_unique_version(file_path, old_versions_dir):
    """
    Check if a file is unique compared to all other versions in the .oldversion folder.

    Args:
        file_path (str): The path of the file to compare.
        old_versions_dir (str): The path of the .oldversion folder.

    Returns:
        bool: True if the file is unique, False if it's identical to any of the existing versions.
    """
    for old_version_file in os.listdir(old_versions_dir):
        old_version_path = os.path.join(old_versions_dir, old_version_file)
        if filecmp.cmp(file_path, old_version_path, shallow=False):
            return False
    return True


def merge_backup(folder_to_backup, backup_location, verbose=False, dry_run=False):
    """
    Merge the contents of a folder to a backup location, resolving conflicts by
    keeping the newest file and moving the older version to a .oldversion
    subfolder. Identical files will be deleted from the folder to be backed up.
    Log messages are generated based on the verbose option, and a dry_run option
    allows simulation of the process without actually copying or deleting files.

    Args:
        folder_to_backup (str): The path of the folder to be backed up.
        backup_location (str): The path of the backup location.
        verbose (bool, optional): If True, displays log messages to the console.
                                  Default is False.
        dry_run (bool, optional): If True, only displays the log messages of what
                                  would be done without actually executing the
                                  operations. Default is False.
    """
    start_time = time.process_time_ns()

    # Configure logging settings
    log_file_path = os.path.join(backup_location, "backup_merger.log")
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    log_level = logging.INFO if verbose else logging.WARNING

    logging.basicConfig(filename=log_file_path, level=log_level, format=log_format, filemode="w")
    logging.info("------------------------------------------------------------")
    logging.info(f"Starting backup merge from {folder_to_backup} to {backup_location}")
    logging.info("------------------------------------------------------------")

    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(log_format))

    if verbose:
        logging.getLogger().addHandler(console_handler)

    # Initialize count variables
    count_newer = 0
    count_different = 0
    count_deleted = 0
    count_moved = 0

    # Build the file trees for both folder_to_backup and backup_location
    # This creates a dictionary with relative file paths as keys and
    # their modification times as values
    folder_to_backup_tree = build_file_tree(folder_to_backup)
    backup_location_tree = build_file_tree(backup_location)

    # Iterate through the source file tree
    for rel_path, source_mtime in folder_to_backup_tree.items():
        # Construct the absolute file paths for the source and destination files
        source_file_path = os.path.join(folder_to_backup, rel_path)
        dest_file_path = os.path.join(backup_location, rel_path)

        # Check if the file exists in the destination file tree
        if rel_path in backup_location_tree:
            logging.info(f"Found file {rel_path} in backup location")
            # Get the modification time of the destination file
            dest_mtime = backup_location_tree[rel_path]

            # Compare the content of the source and destination files.
            # If the content is the same, delete the source file.
            if filecmp.cmp(source_file_path, dest_file_path, shallow=False):
                logging.info(f" SAME, deleting {source_file_path}")
                if not dry_run:
                    os.remove(source_file_path)
                count_different += 1
            else:
                # If the content is different, determine which file is newer
                # and move the older file to the '.oldversion' subfolder.

                # Create the '.oldversion' subfolder if it doesn't exist
                old_versions_dir = os.path.join(os.path.dirname(dest_file_path), ".oldversion")
                if not dry_run:
                    Path(old_versions_dir).mkdir(exist_ok=True)

                # If the source file is newer, move the destination file to
                # '.oldversion' and copy the source file to the destination.
                if source_mtime > dest_mtime:
                    old_version_datetime = datetime.fromtimestamp(dest_mtime).strftime(
                        "%Y%m%d_%H%M%S"
                    )
                    old_version_filename = f"{os.path.splitext(os.path.basename(rel_path))[0]}_{old_version_datetime}{os.path.splitext(os.path.basename(rel_path))[1]}"
                    old_version_path = os.path.join(old_versions_dir, old_version_filename)

                    # Check if the file is unique compared to all other versions in the .oldversion folder
                    if is_unique_version(dest_file_path, old_versions_dir):
                        logging.info(
                            f" NEWER: {source_file_path} is newer than destination file {dest_file_path}"
                        )
                        logging.info(f"  Moving {dest_file_path} to {old_version_path}")
                        logging.info(f"  Moving {source_file_path} to {dest_file_path}")
                        if not dry_run:
                            shutil.move(dest_file_path, old_version_path)
                            shutil.move(source_file_path, dest_file_path)
                        count_newer += 1
                    else:
                        logging.info(
                            f" NOT UNIQUE: {dest_file_path} is identical to an existing version in {old_versions_dir}"
                        )
                        logging.info(f"  Deleting {source_file_path}")
                        if not dry_run:
                            os.remove(source_file_path)
                        count_deleted += 1

                # If the destination file is newer, move the source file to
                # '.oldversion'.
                elif source_mtime < dest_mtime:
                    old_version_datetime = datetime.fromtimestamp(source_mtime).strftime(
                        "%Y%m%d_%H%M%S"
                    )
                    old_version_filename = f"{os.path.splitext(os.path.basename(rel_path))[0]}_{old_version_datetime}{os.path.splitext(os.path.basename(rel_path))[1]}"
                    old_version_path = os.path.join(old_versions_dir, old_version_filename)
                    logging.info(
                        f" OLDER: {source_file_path} is older than destination file {dest_file_path}"
                    )
                    logging.info(f" Moving {source_file_path} to {old_version_path}")
                    if not dry_run:
                        shutil.move(source_file_path, old_version_path)
                    count_moved += 1
        # If the file does not exist in the destination file tree,
        # simply move the file from the source to the destination.
        else:
            logging.info(f"Moving {source_file_path} to {dest_file_path}")
            if not dry_run:
                # Create the destination folder if it doesn't exist
                dest_folder_path = os.path.dirname(dest_file_path)
                Path(dest_folder_path).mkdir(parents=True, exist_ok=True)

                # Copy the file from the source to the destination
                shutil.move(source_file_path, dest_file_path)

    logging.info(
        f"FINISHED comparing {len(folder_to_backup_tree.items())} files from {folder_to_backup} to {backup_location}"
    )
    logging.info(f"Newer files: {count_newer}")
    logging.info(f"Different versions: {count_different}")
    logging.info(f"Deleted files: {count_deleted}")
    logging.info(f"Moved files: {count_moved}")

    if not dry_run:
        # Remove the folder_to_backup after successful merge
        shutil.rmtree(folder_to_backup)
        logging.info(f"Deleted {folder_to_backup}")

    logging.info(f"Time elapsed: {(time.process_time_ns() - start_time)/1e9:.5f}s")
    logging.info("------------------------------------------------------------")


def create_test_file(path, content, modified_time=None):
    with open(path, "w") as f:
        f.write(content)

    if modified_time:
        os.utime(path, (modified_time.timestamp(), modified_time.timestamp()))


def create_test_files_and_folders(
    folder_to_backup="folder_to_backup",
    backup_location="backup_location",
):
    # Remove existing folders if they exist
    if os.path.exists(folder_to_backup):
        shutil.rmtree(folder_to_backup)

    if os.path.exists(backup_location):
        shutil.rmtree(backup_location)

    # Create folder_to_backup structure
    Path(folder_to_backup).mkdir(exist_ok=True)
    Path(os.path.join(folder_to_backup, "subdir1")).mkdir(exist_ok=True)

    # Create backup_location structure
    Path(backup_location).mkdir(exist_ok=True)
    Path(os.path.join(backup_location, "subdir1")).mkdir(exist_ok=True)

    current_time = datetime.now()
    one_day_ago = current_time - timedelta(days=1)
    one_day_later = current_time + timedelta(days=1)

    create_test_file(os.path.join(folder_to_backup, "file1.txt"), "File1 content\n", current_time)
    create_test_file(os.path.join(folder_to_backup, "file2.txt"), "File2 content\n", current_time)
    create_test_file(os.path.join(folder_to_backup, "file3.txt"), "File3 content\n", current_time)
    create_test_file(
        os.path.join(folder_to_backup, "subdir1", "file4.txt"), "File4 content\n", current_time
    )
    create_test_file(
        os.path.join(folder_to_backup, "subdir1", "file5.txt"), "File5 content\n", current_time
    )

    create_test_file(
        os.path.join(backup_location, "file1.txt"), "File1 older content\n", one_day_ago
    )
    create_test_file(os.path.join(backup_location, "file2.txt"), "File2 content\n", current_time)
    create_test_file(
        os.path.join(backup_location, "subdir1", "file4.txt"),
        "File4 newer content\n",
        one_day_later,
    )
    create_test_file(
        os.path.join(backup_location, "subdir1", "file6.txt"), "File6 content\n", current_time
    )

    return current_time, one_day_ago, one_day_later


if __name__ == "__main__":
    # create_test_files_and_folders()
    merge_backup(
        r"/Users/mike/Documents/_proposals",
        r"/Users/mike/Documents/science/_proposals",
        verbose=True,
        dry_run=False,
    )

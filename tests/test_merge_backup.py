import os
from datetime import datetime
from pathlib import Path

from merge_backups.backend import create_test_files_and_folders, merge_backup
from pprint import pprint


def test_merge_backup():
    # Set up the folder structure and files
    current_time, one_day_ago, one_day_later = create_test_files_and_folders()

    # Call the merge_backup function
    merge_backup("folder_to_backup", "backup_location")

    # Define the expected folder structure and files after the merge
    expected_files = {
        "file1.txt",
        "file2.txt",
        "file3.txt",
        os.path.join("subdir1", "file4.txt"),
        os.path.join("subdir1", "file5.txt"),
        os.path.join("subdir1", "file6.txt"),
        os.path.join(".oldversion", f"file1_{one_day_ago.strftime('%Y%m%d_%H%M%S')}.txt"),
        os.path.join(
            "subdir1", ".oldversion", f"file4_{current_time.strftime('%Y%m%d_%H%M%S')}.txt"
        ),
    }

    # Verify that the files in the backup_location match the expected files
    backup_location_files = {
        str(path.relative_to("backup_location"))
        for path in Path("backup_location").rglob("*")
        if path.is_file()
    }
    # pprint(backup_location_files)
    # pprint(expected_files)
    assert (
        backup_location_files == expected_files
    ), f"Expected files do not match the actual files: {backup_location_files}"

    # Verify that the folder_to_backup has been deleted
    assert not os.path.exists("folder_to_backup"), "The folder_to_backup has not been deleted"


if __name__ == "__main__":
    test_merge_backup()

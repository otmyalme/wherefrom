"""
Create and delete the test environment.

This module is responsible for high-level concerns pertaining to the file structure of the
test environment. The actual creation and deletion of individual files and directories is
handled by `tests.tools.environment.items`.
"""

from datetime import datetime
from pathlib import Path
import plistlib

from tests.tools import Sentinel
from tests.tools.environment.items import (
    create_file, create_directory, create_looping_symlink, delete_directory,
)


# CREATE #################################################################################

def create_test_environment(environment_path: Path) -> None:
    """Create a set of files with interesting “where from” values at the given path."""
    environment_path.mkdir()
    create_simple_files(environment_path)
    create_files_with_unexpected_values(environment_path)
    create_files_that_cause_errors(environment_path)
    create_symlink_loops(environment_path)


def create_simple_files(environment_path: Path) -> None:
    """Create some files whose “where from” value can be read without any issues."""
    directory = create_directory(environment_path, "simple")
    create_file(directory, "one-item.html", ONE_URL)
    create_file(directory, "two-items.png", TWO_URLS)
    create_directory(directory, "directory-with-where-from-value", ONE_URL)


def create_files_with_unexpected_values(environment_path: Path) -> None:
    """Create a set of files with unexpected “where from” values."""
    directory = create_directory(environment_path, "unexpected")
    for name, value in UNEXPECTED_VALUES:
        create_file(directory, name, value)  # type: ignore [arg-type]


def create_files_that_cause_errors(environment_path: Path) -> None:
    """Create a set of files that cause errors if there “where from” value is read."""
    errors = create_directory(environment_path, "errors")
    # A file with no “where from” value
    create_file(errors, "no-value.html", Sentinel.NO_VALUE)
    # A file with no read permission
    create_file(errors, "not-readable.html", ONE_URL).chmod(0o200)
    # A file in a directory with no read or search permission
    not_readable = create_directory(errors, "not-readable")
    create_file(not_readable, "one-item.html", ONE_URL)
    not_readable.chmod(0o200)


def create_symlink_loops(environment_path: Path) -> None:
    """
    Create a set of directories that contain symlinks that would cause an endless loop
    if followed indiscriminately.
    """
    loops = create_directory(environment_path, "loops")
    # A directory that (indirectly) contains a symlink to itself
    parent_loop = create_directory(loops, "parent-loop")
    intermediate = create_directory(parent_loop, "intermediate")
    create_looping_symlink(intermediate, parent_loop)


# VALUES

ONE_URL = ["http://nowhere.test/index.html"]
TWO_URLS = ["http://nowhere.test/banner.png", *ONE_URL]

UNEXPECTED_VALUES = [
    ("str.txt", "This is a string"),
    ("bytes.txt", b"This is a bytes object"),
    ("bytearray.txt", bytearray.fromhex("e29d93")),
    ("int.txt", 23),
    ("float.txt", 23.5),
    ("bool.txt", True),
    ("datetime.txt", datetime(2023, 5, 23, 23, 23, 23)),  # noqa: DTZ001
    ("uid.txt", plistlib.UID(23)),
    ("none.txt", None),
    ("list.txt", ["foo", 23, b"ar", [1, 2, 3]]),
    ("dict.txt", {"foo": 23, "bar": [1, 2, 3]}),
]


# DELETE #################################################################################

def delete_test_environment(path: Path) -> None:
    """
    Delete the test environment.

    This function will recursively delete the contents of the given directory, but only
    if it appears safe to do so. The function will delete `.DS_Store` files, symlinks
    named “loop.forever”, empty files, and PNG files whose contents consist of a single
    white pixel, but will raise an `AssertionError` if it encounters any other files.

    If a file has its contents changed after the check whether it appears safe to delete
    it and its actual deletion, the file will still be deleted, however.
    """
    if path.is_dir():
        delete_directory(path)

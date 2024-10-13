"""
Create and delete the test environment.

This module is responsible for high-level concerns pertaining to the file structure of the
test environment. The actual creation and deletion of individual files and directories is
handled by `tests.tools.environment.items`.
"""

from pathlib import Path

from tests.tools import Sentinel
from tests.tools.environment.items import (
    create_file, create_directory, create_symlink, create_looping_symlink,
    delete_directory, WhereFromValue,
)
from tests.parse_tests import UNEXPECTED_WHERE_FROM_VALUE_TEST_CASES


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
    create_file(directory, "one-item\N{HEAVY EXCLAMATION MARK SYMBOL}.html", ONE_URL)
    create_directory(directory, "directory-with-where-from-value", ONE_URL)
    subdirectory = create_directory(directory, "subdirectory")
    create_file(subdirectory, "one-item.html", ONE_URL)
    sub_subdirectory = create_directory(subdirectory, "sub-subdirectory")
    create_file(sub_subdirectory, "one-item.html", ONE_URL)


def create_files_with_unexpected_values(environment_path: Path) -> None:
    """Create a set of files with unexpected “where from” values."""
    directory = create_directory(environment_path, "unexpected")
    # Take the list of files to create from the definition of the test cases.
    for name, value in UNEXPECTED_WHERE_FROM_VALUE_TEST_CASES:
        create_file(directory, name, value)


def create_files_that_cause_errors(environment_path: Path) -> None:
    """Create a set of files that cause errors if there “where from” value is read."""
    errors = create_directory(environment_path, "errors")
    create_too_many_symlinks(errors)
    # Two files with no “where from” value
    create_file(errors, "no-value.html", Sentinel.NO_VALUE)
    create_file(errors, "no-value-\N{CROSS MARK}.html", Sentinel.NO_VALUE)
    # A file with no read permission
    create_file(errors, "not-readable.html", ONE_URL).chmod(0o200)
    # A file in a directory with no read or search permission
    not_readable = create_directory(errors, "not-readable")
    create_file(not_readable, "one-item.html", ONE_URL)
    not_readable.chmod(0o200)


def create_too_many_symlinks(errors_path: Path) -> None:
    """Create a chain of 33 symlinks, which is more than macOS is willing to follow."""
    parent = create_directory(errors_path, "too-many-symlinks")
    target = create_file(parent, "target.html", ONE_URL)
    for n in range(33):
        target = create_symlink(parent, f"{n + 1}", target)


def create_symlink_loops(environment_path: Path) -> None:
    """
    Create a set of directories that contain symlinks that would cause an endless loop
    if followed indiscriminately.
    """
    loops = create_directory(environment_path, "loops")
    # A symlink that points to itself
    self_loop = loops / "self-loop"
    create_symlink(self_loop.parent, self_loop.name, self_loop)
    # A directory that (indirectly) contains a symlink to itself
    parent_loop = create_directory(loops, "parent-loop")
    intermediate = create_directory(parent_loop, "intermediate")
    create_looping_symlink(intermediate, parent_loop)


# VALUES

ONE_URL: list[WhereFromValue] = ["http://nowhere.test/index.html"]
TWO_URLS: list[WhereFromValue] = ["http://nowhere.test/banner.png", *ONE_URL]


# DELETE #################################################################################

def delete_test_environment(path: Path) -> None:
    """
    Delete the test environment.

    This function will recursively delete the contents of the given directory, but only
    if it appears safe to do so. The function will delete `.DS_Store` files, empty files,
    PNG files whose contents consist of a single white pixel, and symlinks that are named
    “loop.forever”, are broken, or point to themselves or a target that is safe to delete.

    If any other file is encountered, the function raises `AssertionError`.

    If a file has its contents changed after the check whether it appears safe to delete
    it and its actual deletion, the file will still be deleted, however.
    """
    if path.is_dir():
        delete_directory(path)

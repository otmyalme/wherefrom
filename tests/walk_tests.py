"""
Test the `wherefrom.walk` module.
"""

from pathlib import Path

import pytest

from wherefrom.walk import walk_directory_trees, WalkState
from wherefrom.exceptions.file import MissingFile, NoReadPermission, TooManySymlinks

from tests.tools.environment.structure import ONE_URL, TWO_URLS


# TESTS ##################################################################################

def test_walk_directory_trees__simple(environment: Path):
    """Does walking a simple directory tree gather all the “where from” values?"""
    path = environment / "simple"
    results, errors = walk_directory_trees(path)
    assert results == get_expected_simple_results(environment)
    assert not errors


def test_walk_directory_trees__errors(environment: Path):
    """Are errors properly handled?"""
    path = environment / "errors"
    results, errors = walk_directory_trees(path)
    assert results == []
    assert errors == [
        NoReadPermission(
            path / "not-readable.html", 13, "EACCES", "read the “where from” value of",
        ),
        NoReadPermission(
            path / "not-readable", 13, "EACCES", "collect the contents of", "directory",
        ),
        TooManySymlinks(path / "too-many-symlinks" / "33", 62, "ELOOP", "process"),
    ]


@pytest.mark.timeout(0.1)
def test_walk_directory_trees__loops(environment: Path):
    """Does walking a directory tree with looping symlinks terminate?"""
    path = environment / "loops"
    results, errors = walk_directory_trees(path)
    # These asserts are incidental. The main thing to test is whether the call terminates.
    assert not results
    assert errors == [TooManySymlinks(path / "self-loop", 62, "ELOOP", "process")]


@pytest.mark.timeout(0.1)
def test_walk_directory_trees__multiple(environment: Path):
    """
    Does walking multiple directory trees work? Even if the base paths include files and
    symlinks to both files and directories?
    """
    paths = [
        environment / "simple",
        environment / "loops",
        environment / "errors" / "not-readable.html",
        environment / "one-item-link",
        environment / "simple-link",
    ]
    expected_results = [
        *get_expected_simple_results(environment, "simple"),
        (environment / "one-item-link", ONE_URL),
        *get_expected_simple_results(environment, "simple-link"),
    ]
    actual_results, errors = walk_directory_trees(*paths)
    assert actual_results == expected_results
    assert errors == [
        TooManySymlinks(environment / "loops" / "self-loop", 62, "ELOOP", "process"),
        NoReadPermission(
            environment / "errors" / "not-readable.html", 13, "EACCES",
            "read the “where from” value of",
        ),
    ]


def test_walk_directory_trees__none():
    """Does walking an empty list of directory trees do nothing?"""
    results, errors = walk_directory_trees()
    assert results == []
    assert errors == []


def test_walk_state__handle_exception__missing_file():
    """Does `WalkState` ignore `MissingFile` exceptions?"""
    base_path = Path("/Users/someone/somewhere")
    missing_file_path = base_path / "no-such-file.txt"
    state = WalkState((base_path,))
    state.handle_exception(MissingFile(missing_file_path, 2, "ENOENT", "gettext"))
    assert not state._exceptions


# EXPECTED RESULTS #######################################################################

def get_expected_simple_results(environment: Path, directory_name: str = "simple"):
    """Get the expected results of reading the simple files’ “where from” values."""
    path = environment / directory_name
    return [
        (path / "one-item.html", ONE_URL),
        (path / "one-item\N{HEAVY EXCLAMATION MARK SYMBOL}.html", ONE_URL),
        (path / "two-items.png", TWO_URLS),
        (path / "subdirectory" / "one-item.html", ONE_URL),
        (path / "subdirectory" / "sub-subdirectory" / "one-item.html", ONE_URL),
    ]

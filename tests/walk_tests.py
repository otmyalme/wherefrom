"""
Test the `wherefrom.walk` module.
"""

import os
from pathlib import Path
from unittest.mock import MagicMock, call

import pytest

from wherefrom.walk import walk_directory_trees, _safe_is_real_directory
from wherefrom.readexceptions import NoReadPermission, TooManySymlinks

from tests.tools.environment.structure import ONE_URL, TWO_URLS


def test_walk_directory_trees__simple(environment: Path):
    """Does walking a simple directory tree gather all the “where from” values?"""
    path = environment / "simple"
    results, errors = walk_directory_trees([path])
    assert results == get_expected_simple_results(environment)
    assert not errors


@pytest.mark.timeout(0.1)
def test_walk_directory_trees__loops(environment: Path):
    """Does walking a directory tree with looping symlinks terminate?"""
    path = environment / "loops"
    results, errors = walk_directory_trees([path])
    # These asserts are incidental. The main thing to test is whether the call terminates.
    assert not results
    assert errors == [TooManySymlinks(path / "self-loop", 62, "ELOOP")]


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
    actual_results, errors = walk_directory_trees(paths)
    assert actual_results == expected_results
    assert errors == [
        TooManySymlinks(environment / "loops" / "self-loop", 62, "ELOOP"),
        NoReadPermission(environment / "errors" / "not-readable.html", 13, "EACCES"),
    ]


def test_walk_directory_trees__none():
    """Does walking an empty list of directory trees work?"""
    results, errors = walk_directory_trees([])
    assert results == []
    assert errors == []


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


# PRIVATE FUNCTIONS ######################################################################

def test__safe_is_real_directory__error():
    """Does `_safe_is_real_directory()` return False if there is an `OSError`?"""
    # This requires mocking. `os.DirEntry` cannot be instantiated or subclassed.
    fake_dir_entry = MagicMock(spec_set=os.DirEntry)
    fake_dir_entry.is_dir = MagicMock(side_effect=OSError())
    assert not _safe_is_real_directory(fake_dir_entry)
    assert fake_dir_entry.mock_calls == [call.is_dir(follow_symlinks=False)]

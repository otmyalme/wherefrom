"""
Test the `wherefrom.walk` module.
"""

import os
from pathlib import Path
from unittest.mock import MagicMock, call

import pytest

from wherefrom.walk import walk_directory_tree, _safe_is_real_directory
from wherefrom.readexceptions import TooManySymlinks

from tests.tools.environment.structure import ONE_URL, TWO_URLS


def test_walk_directory__simple(environment: Path):
    """Does walking a simple directory tree gather all the “where from” values?"""
    path = environment / "simple"
    results, errors = walk_directory_tree(path)
    assert results == [
        (path / "one-item.html", ONE_URL),
        (path / "one-item\N{HEAVY EXCLAMATION MARK SYMBOL}.html", ONE_URL),
        (path / "two-items.png", TWO_URLS),
        (path / "subdirectory" / "one-item.html", ONE_URL),
        (path / "subdirectory" / "sub-subdirectory" / "one-item.html", ONE_URL),
    ]
    assert not errors


@pytest.mark.timeout(0.1)
def test_walk_directory__loops(environment: Path):
    """Does walking a directory tree with looping symlinks terminate?"""
    path = environment / "loops"
    results, errors = walk_directory_tree(path)
    # These asserts are incidental. The main thing to test is whether the call terminates.
    assert not results
    assert errors == [TooManySymlinks(path / "self-loop", 62, "ELOOP")]


# PRIVATE FUNCTIONS ######################################################################

def test__safe_is_real_directory__error():
    """Does `_safe_is_real_directory()` return False if there is an `OSError`?"""
    # This requires mocking. `os.DirEntry` cannot be instantiated or subclassed.
    fake_dir_entry = MagicMock(spec_set=os.DirEntry)
    fake_dir_entry.is_dir = MagicMock(side_effect=OSError())
    assert not _safe_is_real_directory(fake_dir_entry)
    assert fake_dir_entry.mock_calls == [call.is_dir(follow_symlinks=False)]

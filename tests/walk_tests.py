"""
Test the `wherefrom.walk` module.
"""

from pathlib import Path

import pytest

from wherefrom.walk import (
    walk_directory_trees, WalkState, _process_directory, _process_where_from_candidate,
)
from wherefrom.exceptions.file import (
    NoReadPermission, TooManySymlinks, ConcurrentlyReplacedDirectory,
)

from tests.tools.environment.structure import ONE_URL, TWO_URLS


# LOW-LEVEL TESTS ########################################################################

def test__process_directory__missing(environment):
    """Does `_process_directory()` ignore missing files?"""
    base_path = environment / "simple"
    problem_path = base_path / "no-such-file.html"
    state = WalkState((base_path,))
    _process_directory(problem_path, state)
    results, exceptions = state.get_result()
    assert results == []
    assert exceptions == []


def test__process_directory__not_readable(environment):
    """Does `_process_directory()` handle directories it cannot read?"""
    base_path = environment / "errors"
    problem_path = base_path / "not-readable"
    state = WalkState((base_path,))
    _process_directory(problem_path, state)
    results, exceptions = state.get_result()
    assert results == []
    assert len(exceptions) == 1
    exception = exceptions[0]
    assert isinstance(exception, NoReadPermission)
    assert exception.path == problem_path
    assert exception.error_number == 13
    assert exception.error_name == "EACCES"
    assert exception.operation_verb == "collect the contents of"
    assert exception.file_type == "directory"
    assert str(exception) == (
        f"Could not collect the contents of “{problem_path}”: You don’t have permission "
        "to read the directory"
    )


def test__process_directory__not_a_directory(environment):
    """Does `_process_directory()` handle directories becoming non-directories?"""
    base_path = environment / "simple"
    problem_path = base_path / "one-item.html"
    state = WalkState((base_path,))
    _process_directory(problem_path, state)
    results, exceptions = state.get_result()
    assert results == []
    assert len(exceptions) == 1
    exception = exceptions[0]
    assert isinstance(exception, ConcurrentlyReplacedDirectory)
    assert exception.path == problem_path
    assert exception.error_number == 20
    assert exception.error_name == "ENOTDIR"
    assert exception.operation_verb == "collect the contents of"
    assert exception.file_type == "directory"
    assert str(exception) == (
        f"Could not collect the contents of “{problem_path}”: Expected a directory, but "
        "found another type of file system object, possibly because the directory was "
        "replaced with the new object while the application was running"
    )


def test__process_directory__not_a_directory_and_not_readable(environment):
    """What happens if a directory becomes a non-readable non-directory?"""
    base_path = environment / "errors"
    problem_path = base_path / "not-readable.html"
    state = WalkState((base_path,))
    _process_directory(problem_path, state)
    results, exceptions = state.get_result()
    assert results == []
    assert len(exceptions) == 1
    exception = exceptions[0]
    assert isinstance(exception, ConcurrentlyReplacedDirectory)


def test__process_where_from_candidate__missing(environment):
    """Does `_process_where_from_candidate()` ignore missing files?"""
    base_path = environment / "simple"
    problem_path = base_path / "no-such-file.html"
    state = WalkState((base_path,))
    _process_where_from_candidate(problem_path, state)
    results, exceptions = state.get_result()
    assert results == []
    assert exceptions == []


def test__process_where_from_candidate__not_readable(environment):
    """Does `_process_where_from_candidate()` handle directories it cannot read?"""
    base_path = environment / "errors"
    problem_path = base_path / "not-readable.html"
    state = WalkState((base_path,))
    _process_where_from_candidate(problem_path, state)
    results, exceptions = state.get_result()
    assert results == []
    assert len(exceptions) == 1
    exception = exceptions[0]
    assert isinstance(exception, NoReadPermission)
    assert exception.path == problem_path
    assert exception.error_number == 13
    assert exception.error_name == "EACCES"
    assert exception.operation_verb == "read the “where from” value of"
    assert exception.file_type == "file"
    assert str(exception) == (
        f"Could not read the “where from” value of “{problem_path}”: You don’t have "
        "permission to read the file"
    )


# HIGH-LEVEL TESTS #######################################################################

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

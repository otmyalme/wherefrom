"""
Recursively gather the “where from” values of all files in a directory tree.

This module implements its own logic for walking a directory rather than using `os.walk()`
or `Path.walk()`. This will be useful if a future version of the application needs to
implement logic for following symbolic links to directories that employs a strategy other
than “don’t” and “endless loop”.
"""

from collections import deque
from dataclasses import dataclass, field
import os
from pathlib import Path

from wherefrom.read import read_binary_where_from_value
from wherefrom.parse import parse_binary_where_from_value
from wherefrom.exceptions import WhereFromValueError
from wherefrom.readexceptions import MissingFile, NoWhereFromValue


# TYPES ##################################################################################

type PathAndWhereFromValue = tuple[Path, list[str]]
type PathsAndWhereFromValues = list[PathAndWhereFromValue]
type WalkErrors = list[WhereFromValueError]
type WalkResults = tuple[PathsAndWhereFromValues, WalkErrors]


# PUBLIC FUNCTIONS #######################################################################

def walk_directory_tree(base_path: Path) -> WalkResults:
    """
    Recursively gather the “where from” values of all files system objects other than
    directories in a directory tree rooted at the given path.

    The function ignores errors causes by file system objects that don’t have a “where
    from” value or disappear before the value can be read. All other errors are gathered
    into a list of exception classes that is returned as part of the function’s results.
    (Unlike the “where from” values, the errors are not returned as tuples that contain
    the path, but `WhereFromValueError` instances have a `path` attribute.)
    """
    state = WalkState(base_path)
    _process_pending_directories(state)
    return (state.paths_and_values, state.exceptions)


# STATE ##################################################################################

@dataclass
class WalkState:
    """Store the state and results of a walk operation."""

    base_path: Path
    pending_directory_paths: deque[Path] = field(default_factory=deque)
    paths_and_values: PathsAndWhereFromValues = field(default_factory=list)
    exceptions: WalkErrors = field(default_factory=list)

    def __post_init__(self) -> None:
        """Add the base path to `pending_directory_paths`."""
        self.pending_directory_paths.append(self.base_path)

    def add_value(self, path: Path, where_from_value: list[str]) -> None:
        """Add a path and “where from” value to the walk results."""
        self.paths_and_values.append((path, where_from_value))

    def add_exception(self, exception: WhereFromValueError) -> None:
        """Add an exception to the walk results."""
        self.exceptions.append(exception)


# PROCESSING #############################################################################

def _process_pending_directories(state: WalkState) -> None:
    """
    Process all pending directories of the given state. This will probably involve adding
    more pending directories to the state, but these are processed as well, leaving no
    pending directories.
    """
    while state.pending_directory_paths:
        _process_directory(state.pending_directory_paths.popleft(), state)


def _process_directory(path: Path, state: WalkState) -> None:
    """
    Add any subdirectories in the given directory to the pending directory paths of the
    given state. Add the “where from” value of all other file system object (or the error
    raised when attempting to read it, if relevant) to the state’s result.
    """
    subdirectory_paths, candidate_paths = _gather_directory_contents(path)
    _sort_sibling_paths(subdirectory_paths)
    _sort_sibling_paths(candidate_paths)
    state.pending_directory_paths.extend(subdirectory_paths)
    for file_path in candidate_paths:
        _process_where_from_candidate(file_path, state)


def _gather_directory_contents(path: Path) -> tuple[list[Path], list[Path]]:
    """
    Return lists of the subdirectories and other file system objects in the given path.
    Symbolic links to directories count as “other”.
    """
    subdirectory_paths = []
    other_paths = []
    for entry in os.scandir(path):
        entry_path = Path(entry.path)
        if _safe_is_real_directory(entry):
            subdirectory_paths.append(entry_path)
        else:
            other_paths.append(entry_path)
    return subdirectory_paths, other_paths


def _process_where_from_candidate(path: Path, state: WalkState) -> None:
    """
    Attempt to read the “where from” value of the file system object at the given path
    and add the result to the given state. Ignore errors due to missing values or files.
    Add other errors to the given state.
    """
    try:
        binary_value = read_binary_where_from_value(path)
        value = parse_binary_where_from_value(binary_value, path)
    except (NoWhereFromValue, MissingFile):
        pass
    except WhereFromValueError as e:
        state.add_exception(e)
    else:
        state.add_value(path, value)


# UTILITY FUNCTIONS ######################################################################

def _safe_is_real_directory(entry: os.DirEntry[str]) -> bool:
    """
    Check whether the given `DirEntry` is a directory (but not a symbolic link to one).
    This usually doesn’t require a system call, but if it does and there is an error,
    the function returns False.
    """
    try:
        # If this could run on Windows, it should call `is_junction()`, too.
        return entry.is_dir(follow_symlinks=False)
    except OSError:
        return False


def _sort_sibling_paths(paths: list[Path]) -> None:
    """
    Sort the given paths, in place, by their last component. (The function assumes that
    all other path components match between all given paths since otherwise, the order
    wouldn’t make much sense, but it doesn’t verify that assumption.)

    Currently, this function simply sorts paths in ASCIIbetical order.
    """
    paths.sort(key=lambda path: path.name)

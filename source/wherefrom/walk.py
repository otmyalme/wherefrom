"""
Recursively gather the “where from” values of all files in a directory tree.

This module implements its own logic for walking a directory rather than using `os.walk()`
or `Path.walk()`. This will be useful if a future version of the application needs to
implement logic for following symbolic links to directories that employs a strategy other
than “don’t” and “endless loop”.
"""

from collections import deque
from collections.abc import Iterator
from dataclasses import dataclass, field
import os
from pathlib import Path

from wherefrom.read import read_binary_where_from_value
from wherefrom.parse import parse_binary_where_from_value
from wherefrom.exceptions.file import FileError, MissingFile
from wherefrom.exceptions.read import NoWhereFromValue
from wherefrom.exceptions.registry import get_exception_from_os_error, register_operation


# TYPES ##################################################################################

type PathAndWhereFromValue = tuple[Path, list[str]]
type PathsAndWhereFromValues = list[PathAndWhereFromValue]
type WalkErrors = list[FileError]
type WalkResults = tuple[PathsAndWhereFromValues, WalkErrors]


# PUBLIC FUNCTIONS #######################################################################

def walk_directory_trees(*base_paths: Path) -> WalkResults:
    """
    Recursively gather the “where from” values of all files system objects other than
    directories in the directory trees rooted at the given base paths.

    If a symbolic link to a directory is found in a base path, the link isn’t followed;
    the function attempts to read its “where from” value, instead. However, if a base path
    itself is a symbolic link to a directory, it *is* followed.

    If a given base path points to a file system object other than a directory or a
    symbolic link to a directory, its “where from” value is gathered as if it had been
    found in a directory.

    The function ignores errors causes by file system objects that don’t have a “where
    from” value or disappear before the value can be read. All other errors are gathered
    into a list of exception classes that is returned as part of the function’s results.
    (Unlike the “where from” values, the errors are not returned as tuples that contain
    the path, but `WhereFromValueError` instances have a `path` attribute.)

    The recursion into subdirectories doesn’t involve recursive function calls.
    """
    state = WalkState(base_paths)
    _process_base_paths(state)
    return state.get_result()


# REGISTRATION ###########################################################################

register_operation("readdir", "collect the contents of")
register_operation("stat", "process")


# STATE ##################################################################################

@dataclass
class WalkState:
    """Store the state and results of a walk operation."""

    base_paths: tuple[Path, ...]
    pending_directory_paths: deque[Path] = field(default_factory=deque)

    # The following attributes should only be accessed by the class’s methods.
    _paths_and_values: PathsAndWhereFromValues = field(default_factory=list)
    _exceptions: WalkErrors = field(default_factory=list)


    def add_value(self, path: Path, where_from_value: list[str]) -> None:
        """Add the given path and “where from” value to the walk results."""
        self._paths_and_values.append((path, where_from_value))

    def handle_exception(self, exception: FileError) -> None:
        """
        Add the given exception to the walk results, but ignore `MissingFile` exceptions.
        """
        if not isinstance(exception, MissingFile):
            self._exceptions.append(exception)

    def get_result(self) -> WalkResults:
        """Get the results of the walk."""
        return (self._paths_and_values, self._exceptions)


# PROCESSING #############################################################################

def _process_base_paths(state: WalkState) -> None:
    """Recursively process all base paths of the given state."""
    for base_path in state.base_paths:
        _process_base_path(base_path, state)


def _process_base_path(base_path: Path, state: WalkState) -> None:
    """Recursively process the given base path of the given state."""
    if base_path.is_dir():  # Includes symlinks to directories
        _process_directory_tree(base_path, state)
    else:
        _process_where_from_candidate(base_path, state)


def _process_directory_tree(path: Path, state: WalkState) -> None:
    """Recursively process the given directory."""
    state.pending_directory_paths.append(path)
    while state.pending_directory_paths:
        _process_directory(state.pending_directory_paths.popleft(), state)


def _process_directory(path: Path, state: WalkState) -> None:
    """
    Process the given directory, but do not recurse into subdirectories.

    Add the subdirectories of the given directory to the pending directory paths of
    the given state. Add the “where from” values of all other file system objects (or
    any relevant exceptions raised when attempting to read them) to the state’s result.
    """
    subdirectory_paths: list[Path] = []
    candidate_paths: list[Path] = []
    for entry in _directory_entries(path, state):
        _classify_directory_entry(entry, subdirectory_paths, candidate_paths, state)
    _sort_sibling_paths(subdirectory_paths)
    _sort_sibling_paths(candidate_paths)
    state.pending_directory_paths.extend(subdirectory_paths)
    for file_path in candidate_paths:
        _process_where_from_candidate(file_path, state)


def _directory_entries(path: Path, state: WalkState) -> Iterator[os.DirEntry[str]]:
    """Yield a `DirEntry` object for each file system object in the given directory."""
    try:
        yield from os.scandir(path)
    except OSError as e:
        state.handle_exception(get_exception_from_os_error(e, "readdir", "directory"))


def _classify_directory_entry(
    entry: os.DirEntry[str],
    subdirectory_paths: list[Path],
    candidate_paths: list[Path],
    state: WalkState,
) -> None:
    """
    Add the path of the given `DirEntry` object to the appropriate list, if any.

    If the `DirEntry` is for a directory (but not a symlink to a directory), add it to
    `subdirectory_paths`. If it’s a file or a symlink to one, add it to `candidate_paths`.
    Otherwise, do nothing.
    """
    entry_path = Path(entry.path)
    try:
        # If this could run on Windows, it should call `is_junction()`, too.
        if entry.is_dir(follow_symlinks=False):
            subdirectory_paths.append(entry_path)
        elif entry.is_file():
            candidate_paths.append(entry_path)
        else:
            pass  # Ignore other file system objects
    except OSError as e:
        state.handle_exception(get_exception_from_os_error(e, "stat"))


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
    except FileError as e:
        state.handle_exception(e)
    else:
        state.add_value(path, value)


# UTILITY FUNCTIONS ######################################################################

def _sort_sibling_paths(paths: list[Path]) -> None:
    """
    Sort the given paths, in place, by their last component. (The function assumes that
    all other path components match between all given paths since otherwise, the order
    wouldn’t make much sense, but it doesn’t verify that assumption.)

    Currently, this function simply sorts paths in ASCIIbetical order.
    """
    paths.sort(key=lambda path: path.name)

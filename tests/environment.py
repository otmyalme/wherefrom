"""
Create a set of files with interesting “where from” values, for use by the test suite.

This module provides the `create_test_environment()` and `delete_test_environment()`
functions, which are used by the `environment` fixture in `tests.conftest`. See its
docstring for details.

The functions makes every effort to ensure they don’t overwrite or delete any important
files; files that are written to are opened for exclusive creation, and files are only
deleted if they are either empty, or are PNG files consisting of a single white pixel.
The logic used to implement these safeguards is subject to race conditions, however.

(Note that Git doesn’t store files’ extended attributes, so it wouldn’t be possible to
just manually create the files once and keep them in the repository.)
"""

from datetime import datetime
from pathlib import Path
import plistlib
import subprocess
from typing import Literal

from wherefrom.read import WHERE_FROM_ATTRIBUTE_NAME, WhereFromValue

from tests.tools import Sentinel


# CREATE #################################################################################

def create_test_environment(environment_path: Path) -> None:
    """Create a set of files with interesting “where from” values at the given path."""
    environment_path.mkdir()

    # Files whose “where from” value can be read without any issues
    simple = _create_directory(environment_path, "simple", ["http://nowhere.test/"])
    _create_file(simple, "one-item.html", ["http://nowhere.test/index.html"])
    _create_file(simple, "two-items.png",
        ["http://nowhere.test/banner.png", "http://nowhere.test/index.html"])

    # Files that cause errors when read
    errors = _create_directory(environment_path, "errors")
    _create_file(errors, "no-value.png", Sentinel.NO_VALUE)
    _create_file(errors, "not-readable.html", ["http://nowhere.test/"]).chmod(0o200)
    not_readable = _create_directory(errors, "not-readable")
    _create_file(not_readable, "one-item.html", ["http://nowhere.test/"])
    not_readable.chmod(0o200)

    endless_loop = _create_directory(errors, "endless-loop")
    soon1 = _create_directory(endless_loop, "soon")
    soon2 = _create_directory(soon1, "really-soon")
    _create_symlink(soon2, LOOPING_SYMLINK_NAME, endless_loop)

    # Files whose “where from” value is of an unusual type
    weird_types_path = _create_directory(environment_path, "weird-types")
    _create_file(weird_types_path, "str.png", "This is a string")
    _create_file(weird_types_path, "bytes.png", b"This is a bytes object")
    _create_file(weird_types_path, "bytearray.png", bytearray.fromhex("e29d93"))
    _create_file(weird_types_path, "int.png", 23)
    _create_file(weird_types_path, "float.png", 23.5)
    _create_file(weird_types_path, "bool.png", where_from_value=True)
    _create_file(weird_types_path, "datetime.png", SAMPLE_DATETIME)
    _create_file(weird_types_path, "uid.png", plistlib.UID(23))
    _create_file(weird_types_path, "none.png", None)
    _create_file(weird_types_path, "list.png", ["foo", 23, b"ar", [1, 2, 3]])
    _create_file(weird_types_path, "dict.png", {"foo": 23, "bar": [1, 2, 3]})


def _create_directory(
    parent_path: Path,
    name: str,
    where_from_value: WhereFromValue | Literal[Sentinel.NO_VALUE] = Sentinel.NO_VALUE,
) -> Path:
    """Create a directory with the given name at the given path and return its path."""
    path = parent_path / name
    path.mkdir()
    _set_where_from_value(path, where_from_value)
    return path


def _create_file(
    parent_path: Path,
    name: str,
    where_from_value: WhereFromValue | Literal[Sentinel.NO_VALUE],
) -> Path:
    """
    Create a file with the given name at the given path and return its path.

    The file’s “where from” attribute is set to the given value using `xattr`.

    If `name` ends with “.png”, an actual PNG file consisting of a single white pixel is
    created, so that VS Code doesn’t display an error message when the developer views it.
    The file is opened for exclusive creation, so that an existing file isn’t overwritten.

    If `name` has any other extension, the file is touched.
    """
    path = parent_path / name

    if path.suffix == ".png":
        _create_png_file(path)
    else:
        path.touch()

    _set_where_from_value(path, where_from_value)

    return path


def _create_png_file(path: Path) -> None:
    """Create a PNG file consisting of a single white pixel at the given path."""
    with path.open("xb") as file:  # Open for exclusive creation to avoid overwriting
        file.write(TINY_PNG_BYTES)


def _create_symlink(parent_path: Path, name: str, target: Path) -> Path:
    """Create a symbolic link to the given target."""
    path = parent_path / name
    path.symlink_to(target)
    return path


def _set_where_from_value(
    path: Path,
    value: WhereFromValue | Literal[Sentinel.NO_VALUE],
) -> None:
    """Set the “where from” attribute of the file at the given path to the given value."""
    if value is not Sentinel.NO_VALUE:
        fmt = plistlib.FMT_BINARY
        binary_value = plistlib.dumps(value, fmt=fmt)  # type: ignore [arg-type]
        hexadecimal_value = binary_value.hex()
        # Use `xattr` to set the value rather than using `ctypes` in the tests, too.
        # “-wx” means “write a value that’s provided in hexadecimal”.
        command = ("xattr", "-wx", WHERE_FROM_ATTRIBUTE_NAME, hexadecimal_value, path)
        subprocess.run(command, check=True)


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
        _delete_directory(path)


def _delete_directory(path: Path) -> None:
    """Recursively delete the directory at the given path, if it appears safe to do so."""
    if path.stat().st_mode & 0o777 == 0o200:
        path.chmod(0o700)  # Make any unreadable directories that were created readable
    for child_path in path.iterdir():
        _delete_item(child_path)
    path.rmdir()  # This would fail if the path still had contents


def _delete_item(path: Path) -> None:
    """Delete the file or directory at the given path, it it appears safe to do so."""
    if path.is_dir() and not path.is_symlink():
        _delete_directory(path)
    else:
        _delete_file(path)  # The function will check whether `path` is actually a file


def _delete_file(path: Path) -> None:
    """Delete the file at the given path, if it appears safe to do so."""
    if _is_safe_to_delete(path):
        path.unlink()
    else:
        message = f"There’s an unexpected file in the test environment: “{path}”"
        raise AssertionError(message)


def _is_safe_to_delete(path: Path) -> bool:
    """Check whether it appears safe to delete the file at the given path."""
    if path.is_symlink():
        return path.name == LOOPING_SYMLINK_NAME
    elif path.is_file():  # Make sure `path` isn’t a mount point, or something
        is_ds_store = (path.name == ".DS_Store")
        is_empty = (path.stat().st_size == 0)
        is_tiny_png = (path.suffix == ".png" and path.read_bytes() == TINY_PNG_BYTES)
        return is_ds_store or is_empty or is_tiny_png
    else:  # pragma: no cover
        return False


# MISCELLANEOUS ##########################################################################

# A PNG file consisting of a single white pixel, encoded as a string of hexadecimal
# digits. Used so that the PNGs created as test files are actually valid.
TINY_PNG_HEX = (
    "89 50 4E 47 0D 0A 1A 0A"  # Signature
    "00 00 00 0D 49 48 44 52 00 00 00 01 00 00 00 01 08 02 00 00 00 90 77 53 DE"  # Header
    "00 00 00 0C 49 44 41 54 08 5B 63 F8 FF FF 3F 00 05 FE 02 FE A1 37 FE BF"  # Data
    "00 00 00 00 49 45 4E 44 AE 42 60 82"  # End
)

# The same PNG as a bytes object.
TINY_PNG_BYTES = bytes.fromhex(TINY_PNG_HEX)

# A sample datetime object. This doesn’t have a time zone because it’s passed to
# `plistlib.dumps`, which explodes if given datetimes with time zones.
SAMPLE_DATETIME = datetime(2023, 5, 23, 23, 23, 23)  # noqa: DTZ001  # See above

# The name given to symlinks that would cause endless loops if indiscriminately followed.
LOOPING_SYMLINK_NAME = "loop.forever"

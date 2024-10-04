"""
Provide utility functions for `tests.tool.environment.structure`.

This module is responsible for low-level concerns such as the actual creation and deletion
of individual files and directories. Deciding which files should actually be created is
the handled by `tests.tools.environment.structure`.
"""

from pathlib import Path
import plistlib
import subprocess
from typing import Literal

from tests.tools import Sentinel
from wherefrom.read import WHERE_FROM_ATTRIBUTE_NAME, WhereFromValue


# CREATE #################################################################################

def create_directory(
    parent_path: Path,
    name: str,
    where_from_value: WhereFromValue | Literal[Sentinel.NO_VALUE] = Sentinel.NO_VALUE,
) -> Path:
    """Create a directory with the given name at the given path and return its path."""
    path = parent_path / name
    path.mkdir()
    set_where_from_value(path, where_from_value)
    return path


def create_file(
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
    create_png_file(path) if path.suffix == ".png" else path.touch()
    set_where_from_value(path, where_from_value)
    return path


def create_png_file(path: Path) -> None:
    """Create a PNG file consisting of a single white pixel at the given path."""
    with path.open("xb") as file:  # Open for exclusive creation to avoid overwriting
        file.write(TINY_PNG_BYTES)


def create_looping_symlink(parent_path: Path, target: Path) -> Path:
    """
    Create a symbolic link to the given target with a special name that indicates that
    it’s part of a loop, and that it can be deleted by `delete_test_environment()`. It’s
    the responsibility of the caller to ensure that the symlink is part of a loop.
    """
    path = parent_path / LOOPING_SYMLINK_NAME
    path.symlink_to(target)
    return path


def set_where_from_value(
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

def delete_directory(path: Path) -> None:
    """Recursively delete the directory at the given path, if it appears safe to do so."""
    if path.stat().st_mode & 0o777 == 0o200:
        path.chmod(0o700)  # Make any unreadable directories that were created readable
    for child_path in path.iterdir():
        delete_item(child_path)
    path.rmdir()  # This would fail if the path still had contents


def delete_item(path: Path) -> None:
    """Delete the file or directory at the given path, it it appears safe to do so."""
    if path.is_dir() and not path.is_symlink():
        delete_directory(path)
    else:
        delete_file(path)  # The function will check whether `path` is actually a file


def delete_file(path: Path) -> None:
    """Delete the file at the given path, if it appears safe to do so."""
    if is_safe_to_delete(path):
        path.unlink()
    else:
        message = f"There’s an unexpected file in the test environment: “{path}”"
        raise AssertionError(message)


def is_safe_to_delete(path: Path) -> bool:
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


# SPECIAL FILE NAMES #####################################################################

# The name given to symlinks that would cause endless loops if followed indiscriminately.
LOOPING_SYMLINK_NAME = "loop.forever"


# FILE CONTENTS ##########################################################################

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
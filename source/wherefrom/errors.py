"""
Provides the exception classes used by the application.

The exception hierarchy is structured as follows:

    WhereFromException
     └─ ReadWhereFromValueError
         └─ CannotReadWhereFromValue
             ├─ NoSuchFile
             ├─ FileHasNoWhereFromValue
             ├─ UnsupportedFileSystem
             ├─ UnsupportedFileSystemObject
             └─ WhereFromValueLengthMismatch
"""

from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

from wherefrom.tools import multiline_string_as_one_line


# BASE CLASS #############################################################################

class WhereFromException(Exception):
    """
    The base class for all exceptions raised by the application.

    Automatically turns all subclasses into dataclasses, and subclasses should have their
    arguments defined as fields, so that they can be accessed in a reasonable manner.

    Also, automatically constructs the exception message, by `format()`ing `MESSAGE` with
    the object’s attributes. If `MESSAGE_PREFIX` is nonempty, it is first prepended to
    `MESSAGE` using “: ” as a separator. This allows trees of the exception hierarchy to
    define a common “⟨problem⟩: ⟨cause⟩” structure.
    """
    MESSAGE_PREFIX: ClassVar[str] = ""
    MESSAGE: ClassVar[str] = "No error message has been provided"

    def __init_subclass__(cls) -> None:
        """Automatically turn subclasses into dataclasses and fix message whitespace."""
        dataclass(cls)
        cls.MESSAGE_PREFIX = multiline_string_as_one_line(cls.MESSAGE_PREFIX)
        cls.MESSAGE = multiline_string_as_one_line(cls.MESSAGE)

    def __str__(self) -> str:
        """Construct the exception message from `MESSAGE` and `MESSAGE_PREFIX`."""
        if self.MESSAGE_PREFIX:
            template = f"{self.MESSAGE_PREFIX.rstrip(": ")}: {self.MESSAGE}"
        else:
            template = self.MESSAGE
        return template.format(**vars(self))


# ERRORS READING THE “WHERE FROM” VALUE ##################################################

# Base Classes ---------------------------------------------------------------------------

class ReadWhereFromValueError(WhereFromException):
    """Raised if an error occurs while reading or parsing a file’s “where from” value."""
    path: Path


class CannotReadWhereFromValue(ReadWhereFromValueError):
    """
    Raised if an error occurs while reading a file’s “where from” value. For expected
    errors, a subclass of this exception class is raised instead.
    """
    MESSAGE_PREFIX = "Could not read the “were from” value of “{path}”"
    MESSAGE = "An unexpected error ocurred (error code {error_code})"
    error_code: int
    error_name: str


# Common Errors --------------------------------------------------------------------------

class NoSuchFile(CannotReadWhereFromValue, FileNotFoundError):
    """
    Raised when reading the “where from” value of a file that does not exist.
    The corresponding `getxattr()` error name is `ENOENT`.
    """
    MESSAGE = "The file doesn’t exist"


class FileHasNoWhereFromValue(CannotReadWhereFromValue, KeyError):
    """
    Raised when reading the “where from” value of a file that doesn’t have one.
    The corresponding `getxattr()` error name is `ENOATTR`.
    """
    MESSAGE = "The file doesn’t have the value set"


# Lack of Support ------------------------------------------------------------------------

class UnsupportedFileSystem(CannotReadWhereFromValue):
    """
    Raised if the file system doesn’t support extended file attributes.

    This hasn’t, so far, been tested on an actual file. Experiments involving FAT and
    ExFAT disk images created by macOS and the internal memory of an ancient digital
    camera found that all support extended file attributes.

    The corresponding `getxattr()` error name is `ENOTSUP`.
    """
    MESSAGE = "The file system doesn’t support extended file attributes"


class UnsupportedFileSystemObject(CannotReadWhereFromValue):
    """
    Raised when reading the “where from” attribute of a file system object that doesn’t
    support the attribute (or extended attributes in general). `/dev/null` qualifies, but
    it’s not clear what the exact rules are.

    The corresponding `getxattr()` error names are `EPERM` and `EISDIR`.
    """
    MESSAGE = "That type of file system object doesn’t support the “where from” attribute"


# Internal Errors ------------------------------------------------------------------------

class WhereFromValueLengthMismatch(CannotReadWhereFromValue):
    """
    Raised if the buffer passed to `_read_where_from_value()` is too small to hold the
    “where from” value. A different process may have changed the file’s “where from”
    value in the time between the call to `_read_where_from_value_length()` and the call
    to `_read_where_from_value_length()`, or there may be a bug in this application, or
    maybe even in `getxattr()`.

    The corresponding `getxattr()` error name is `ERANGE`.
    """
    MESSAGE = """
        Either the value has changed while it was being read, or there has been an
        unexpected internal error
    """
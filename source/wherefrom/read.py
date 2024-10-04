"""
Read the value of the “where from” extended file attribute.

The attribute is read by using `ctypes` to call the C function `getxattr()` from the
`libc` library provided as part of macOS. Documentation for that function is provided
by `man getxattr`.
"""

import ctypes
import ctypes.util
from datetime import datetime
from pathlib import Path
import plistlib

from wherefrom.errors import (
    CannotReadWhereFromValue, FileHasNoWhereFromValue, NoSuchFile, FileNotReadable,
    UnsupportedFileSystem, UnsupportedFileSystemObject, UnsupportedFileName,
    WhereFromValueLengthMismatch,
)


# The full name of the “where from” attribute, as a string and a bytes object.
WHERE_FROM_ATTRIBUTE_NAME = "com.apple.metadata:kMDItemWhereFroms"
WHERE_FROM_ATTRIBUTE_NAME_BYTES = WHERE_FROM_ATTRIBUTE_NAME.encode("ascii")

# The name of the C library that provides the necessary functionality for reading the
# “where from“ attribute.
LIBRARY_NAME = "libc"

# The type of all possible “where from” values. `typeshed` annotates the return value of
# the standard library function used to parse the binary values as `Any`, but reading the
# source code and some experimentation resulted in the following type.
#
# In practice, values will usually be of type `list[str]`, however.
#
# (The type includes a redundant `list[str]` because mypy is being weird.)
type WhereFromValue = (str | bytes | bytearray | int | float | bool | datetime | None |
    plistlib.UID | list[str] | list["WhereFromValue"] | dict[str, "WhereFromValue"])


class WhereFromAttributeReader:
    """Read the value of the “where from” extended file attribute."""
    # This is a class so that there’s somewhere to put `library` that isn’t a global
    # variable.

    # The C library that provides the necessary functionality for reading the “where from“
    # attribute.
    library: ctypes.CDLL


    def __init__(self) -> None:
        # Load the C library by its name.
        self.library = ctypes.CDLL(ctypes.util.find_library(LIBRARY_NAME), use_errno=True)


    def read_where_from_value(self, path: Path) -> WhereFromValue:
        """
        Read the “where from” value of the given object and return it as a Python object.

        The returned value is most likely a list of strings, but values of other types
        can be returned if the file’s “where from” attribute has been set in an unusual
        manner. Checking for these cases is the responsibility of the caller.

        The function raises `ReadWhereFromValueError` (or a subclass thereof) if the value
        cannot be read or cannot be parsed. This includes cases where the file simply
        doesn’t have a “where from” value. In those cases, the `FileHasNoWhereFromValue`
        subclass is raised.
        """
        bytes_path = bytes(path)
        attribute_length = self._read_where_from_value_length(bytes_path)
        binary_value = self._read_where_from_value(bytes_path, attribute_length)
        return self._parse_binary_where_from_value(binary_value)


    def _read_where_from_value_length(self, path: bytes) -> int:
        """
        Read the length of the “where from” attribute in bytes. This is required to call
        `_read_where_from_value()`.
        """
        return self._call_getxattr(path)


    def _read_where_from_value(self, path: bytes, length: int) -> bytes:
        """
        Read the value of the “where from” attribute of the given file. `length` is the
        length of the attribute’s value in bytes, which should be obtained by calling
        `_read_where_from_value_length()`.
        """
        buffer = ctypes.create_string_buffer(length)
        self._call_getxattr(path, buffer)
        return buffer.raw


    def _call_getxattr(self, path: bytes, buffer: "_Buffer | None" = None) -> int:
        """
        Call the `getxattr()` C function. Returns the length of the “where from” attribute
        in bytes. If `buffer` is given, the attribute’s value is written to it.

        To retrieve the attribute value, this method should be called twice: first without
        a buffer, to determine the necessary length for the buffer, and then with a buffer
        of the appropriate length.
        """
        result = self.library.getxattr(
            path,
            WHERE_FROM_ATTRIBUTE_NAME_BYTES,
            buffer,
            buffer._length_ if buffer else 0,  # the number of bytes to write to `buffer`
            0,  # an offset within the attribute; it’s not clear what that is used for
            0,  # options; can be used to avoid following symbolic links
        )
        if result < 0:
            raise self._get_reading_exception(path, ctypes.get_errno())
        else:
            return result  # type: ignore [no-any-return]  # `getxattr()` does return int


    def _parse_binary_where_from_value(self, binary_value: bytes) -> WhereFromValue:
        """Convert the given binary “where from” value into a Python object."""
        value = plistlib.loads(binary_value, fmt=plistlib.FMT_BINARY)
        return value  # type: ignore [no-any-return]  # I’ve read the source code


    def _get_reading_exception(
        self,
        path: bytes,
        error_code: int,
    ) -> CannotReadWhereFromValue:
        """Get an exception to throw for `getxattr()` errors with the given code."""
        proper_path = Path(path.decode("utf8", errors="replace"))
        default = DEFAULT_ERROR_INFORMATION
        error_name, exception_class = ERROR_INFORMATION.get(error_code, default)
        return exception_class(proper_path, error_code, error_name)


# A dict that maps error codes from `getxattr()` to their name and the appropriate
# exception to throw.
#
# See https://github.com/apple-open-source/macos/blob/master/xnu/bsd/sys/errno.h for
# the mapping of error codes to names.
ERROR_INFORMATION = {
    # Undocumented codes that have been determined by experimentation
     2: ("ENOENT", NoSuchFile),
    # Documented codes in the order they appear on the `getxattr` manpage
    93: ("ENOATTR", FileHasNoWhereFromValue),
    45: ("ENOTSUP", UnsupportedFileSystem),
    34: ("ERANGE", WhereFromValueLengthMismatch),
     1: ("EPERM", UnsupportedFileSystemObject),
    22: ("EINVAL", CannotReadWhereFromValue),  # Cannot happen; see below
    21: ("EISDIR", UnsupportedFileSystemObject),  # Probably cannot happen; see below
    20: ("ENOTDIR", NoSuchFile),
    63: ("ENAMETOOLONG", UnsupportedFileName),
    13: ("EACCES", FileNotReadable),
}

# `EINVAL` indicates that the attribute name is invalid, or that unsupported options have
# been passed to `getxattr()`. That shouldn’t be possible, since the application only
# uses a single attribute name, and doesn’t use any options. Accordingly, there is no
# specific `CannotReadWhereFromValue` subclass for this case.
#
# `EISDIR` is, according to the manpage, similar to `EPERM`, and is used if the path isn’t
# a regular file, but the attribute in question can only be used for files. It’s not clear
# whether that can actually happen; the name suggests the error would occur if the path is
# a directory, but reading the “where from” value of a directory works just fine (on an
# APFS volume, at least).


# The error information to use if the error code is missing from `ERROR_INFORMATION`.
DEFAULT_ERROR_INFORMATION = ("UNKNOWN", CannotReadWhereFromValue)


# PRIVATE UTILITY ########################################################################

# The type of the C string buffer passed to `_call_getxattr()`.
type _Buffer = ctypes.Array[ctypes.c_char]

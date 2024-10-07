"""
Read the binary value of the “where from” extended file attribute.

The attribute is read by using `ctypes` to call the C function `getxattr()` from the
`libc` library provided as part of macOS. Documentation for that function is provided
by `man getxattr`.
"""

from collections.abc import Callable
import ctypes
import ctypes.util
import os
from pathlib import Path

from wherefrom.readexceptions import *


# PUBLIC FUNCTIONS #######################################################################

def read_binary_where_from_value(path: Path) -> bytes:
    """
    Read the binary “where from” value of the given file.

    The function raises `WhereFromValueReadingError` (or a subclass thereof) if the value
    cannot be read. This includes cases where the file simply doesn’t have a “where
    from” value. In those cases, the `NoWhereFromValue` subclass is raised.
    """
    path_bytes = bytes(path)
    attribute_length = _read_where_from_value_length(path_bytes)
    return _read_where_from_value(path_bytes, attribute_length)


# PUBLIC DATA ############################################################################

# The full name of the “where from” attribute.
WHERE_FROM_ATTRIBUTE_NAME = "com.apple.metadata:kMDItemWhereFroms"


# READING THE VALUE ######################################################################

# The type of the C string buffer passed to `_call_getxattr()`.
type Buffer = ctypes.Array[ctypes.c_char]


def _read_where_from_value_length(path: bytes) -> int:
    """
    Read the length of the “where from” attribute in bytes. This is required to call
    `_read_where_from_value()`.
    """
    return _call_getxattr(path)


def _read_where_from_value(path: bytes, length: int) -> bytes:
    """
    Read the value of the “where from” attribute of the given file. `length` is the
    length of the attribute’s value in bytes, which should be obtained by calling
    `_read_where_from_value_length()`.
    """
    buffer = ctypes.create_string_buffer(length)
    _call_getxattr(path, buffer)
    return buffer.raw


# CALLING THE EXTERNAL C FUNCTION ########################################################

# The full name of the “where from” attribute as a bytes object, for optimization.
WHERE_FROM_ATTRIBUTE_NAME_BYTES = WHERE_FROM_ATTRIBUTE_NAME.encode("ascii")


def _call_getxattr(path: bytes, buffer: Buffer | None = None) -> int:
    """
    Call the `getxattr()` C function. Returns the length of the “where from” attribute
    in bytes. If `buffer` is given, the attribute’s value is written to it.

    To retrieve the attribute value, this method should be called twice: first without
    a buffer, to determine the necessary length for the buffer, and then with a buffer
    of the appropriate length.
    """
    function = external_getxattr_function or _load_external_getxattr_function()
    result = function(
        path,
        WHERE_FROM_ATTRIBUTE_NAME_BYTES,
        buffer,
        buffer._length_ if buffer else 0,  # the number of bytes to write to `buffer`
        0,  # an offset within the attribute; it’s not clear what that is used for
        0,  # options; can be used to avoid following symbolic links
    )
    if result < 0:
        raise _get_reading_exception(path, ctypes.get_errno())
    else:
        return result


# LOADING THE EXTERNAL C LIBRARY #########################################################

# The type of the external C function used to read “where from” values.
type GetXAttrFunction = Callable[[bytes, bytes, Buffer | None, int, int, int], int]

# The name of the external C library that provides that function.
EXTERNAL_C_LIBRARY_NAME = "libc"

# The name of that function.
EXTERNAL_GETXATTR_FUNCTION_NAME = "getxattr"

# The function itself.
external_getxattr_function: GetXAttrFunction | None = None


def _load_external_getxattr_function() -> GetXAttrFunction:
    """Load the external C function that reads the “where from” value."""
    global external_getxattr_function
    if not external_getxattr_function:
        try:
            library_name = EXTERNAL_C_LIBRARY_NAME
            # `path_name = None` would work, too (at least on my machine)
            path_name = ctypes.util.find_library(library_name)
            library = ctypes.CDLL(path_name, use_errno=True)
        except OSError as e:
            raise MissingExternalLibrary(library_name) from e
        else:
            function_name = EXTERNAL_GETXATTR_FUNCTION_NAME
            try:
                external_getxattr_function = getattr(library, function_name)
            except AttributeError as e:
                raise MissingExternalLibraryFunction(library_name, function_name) from e
    return external_getxattr_function


# HANDLING ERRORS ########################################################################

def _get_reading_exception(path: bytes, error_code: int) -> WhereFromValueReadingError:
    """Get an exception to throw for `getxattr()` errors with the given code."""
    proper_path = Path(os.fsdecode(path))
    default = DEFAULT_ERROR_INFORMATION
    error_name, exception_class = ERROR_INFORMATION.get(error_code, default)
    return exception_class(proper_path, error_code, error_name)


# A dict that maps error codes from `getxattr()` to their name and the appropriate
# exception to throw.
#
# See https://github.com/apple-open-source/macos/blob/master/xnu/bsd/sys/errno.h for
# the mapping of error codes to names.
#
# See the docstrings of the exception classes for details about the errors.
ERROR_INFORMATION = {
    # Undocumented codes
     2: ("ENOENT", MissingFile),
    # Documented codes in the order they appear on the `getxattr` manpage
    93: ("ENOATTR", NoWhereFromValue),
    45: ("ENOTSUP", UnsupportedFileSystem),
    34: ("ERANGE", WhereFromValueLengthMismatch),
     1: ("EPERM", UnsupportedFileSystemObject),
    22: ("EINVAL", UnexpectedErrorReadingWhereFromValue),  # Cannot happen; see below
    21: ("EISDIR", UnsupportedFileSystemObject),  # Probably cannot happen; see below
    20: ("ENOTDIR", MissingFile),
    63: ("ENAMETOOLONG", UnsupportedPath),
    13: ("EACCES", NoReadPermission),
    62: ("ELOOP", TooManySymlinks),
    14: ("EFAULT", UnexpectedErrorReadingWhereFromValue),  # Probably cannot happen
     5: ("EIO", IOErrorReadingWhereFromValue),
}

# `EINVAL` indicates that the attribute name is invalid, or that unsupported options have
# been passed to `getxattr()`. That shouldn’t be possible, since the application only
# uses a single attribute name, and doesn’t use any options.
#
# `EISDIR` is, according to the manpage, similar to `EPERM`, and is used if the path isn’t
# a regular file, but the attribute in question can only be used for files. It’s not clear
# whether that can actually happen; the name suggests the error would occur if the path is
# a directory, but reading the “where from” value of a directory works just fine (on an
# APFS volume, at least).
#
# `EFAULT` indicates that the path or attribute name passed to `getxattr()` points to an
# invalid memory address. That would indicate a bug in `ctypes`.


# The error information to use if the error code is missing from `ERROR_INFORMATION`.
DEFAULT_ERROR_INFORMATION = ("UNKNOWN", UnknownErrorReadingWhereFromValue)

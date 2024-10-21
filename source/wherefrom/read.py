"""
Read the binary value of the “where from” extended file attribute.

The value is read by using Python’s `ctypes` module to call the C function `getxattr()`
from the `libc` library provided as part of macOS. Documentation for that function is
available through `man getxattr`.
"""

from collections.abc import Callable
import ctypes
import ctypes.util
import os
from pathlib import Path
from typing import cast

from wherefrom.exceptions.read import (
    MissingExternalLibrary, MissingExternalLibraryFunction,
)
from wherefrom.exceptions.registry import (
    get_exception_by_error_number, register_operation,
)


# PUBLIC FUNCTIONS #######################################################################

def read_binary_where_from_value(path: Path) -> bytes:
    """
    Read the binary “where from” value of the given file.

    Raises a `MissingExternalDependencyError` subclass if the function cannot read any
    file’s “where from” values because of a missing external dependency.

    Raises a `LowLevelFileError` subclass if the function cannot read the given file’s
    “where from” value, even if that’s because the file doesn’t have one. (The subclass
    it raises in that case is `NoWhereFromValue`.)

    Note that the exception raised need not be a `WhereFromValueReadingError`.
    """
    path_bytes = os.fsencode(path)
    attribute_length = _read_binary_where_from_value_length(path_bytes)
    return _read_binary_where_from_value(path_bytes, attribute_length)


# PUBLIC DATA ############################################################################

# The full name of the “where from” attribute.
WHERE_FROM_ATTRIBUTE_NAME = "com.apple.metadata:kMDItemWhereFroms"


# REGISTRATION ###########################################################################

register_operation("getxattr", "read the “where from” value of")


# READING THE VALUE ######################################################################

# The type of the C string buffer passed to `_call_getxattr()`.
type Buffer = ctypes.Array[ctypes.c_char]


def _read_binary_where_from_value_length(path: bytes) -> int:
    """
    Read the length of the “where from” attribute in bytes. This is required to call
    `_read_binary_where_from_value()`.
    """
    return _call_getxattr(path)


def _read_binary_where_from_value(path: bytes, length: int) -> bytes:
    """
    Read the value of the “where from” attribute of the given file. `length` is the
    length of the attribute’s value in bytes, which should be obtained by calling
    `_read_binary_where_from_value_length()`.
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
    getxattr = external_getxattr_function or _load_external_getxattr_function()
    result = getxattr(
        path,
        WHERE_FROM_ATTRIBUTE_NAME_BYTES,
        buffer,
        buffer._length_ if buffer else 0,  # The number of bytes to write to `buffer`
        0,  # An offset within the attribute; it’s not clear what that is used for
        0,  # Options; can be used to avoid following symbolic links
    )
    if result < 0:
        raise get_exception_by_error_number(ctypes.get_errno(), "getxattr", path)
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
        library = _load_external_c_library()
        external_getxattr_function = _get_external_getxattr_function(library)
    return external_getxattr_function


def _load_external_c_library() -> ctypes.CDLL:
    """Load the external C library."""
    # `path_str = None` would work, too (at least on my machine).
    path_str = ctypes.util.find_library(EXTERNAL_C_LIBRARY_NAME)
    try:
        return ctypes.CDLL(path_str, use_errno=True)
    except OSError:
        raise MissingExternalLibrary(EXTERNAL_C_LIBRARY_NAME) from None


def _get_external_getxattr_function(library: ctypes.CDLL) -> GetXAttrFunction:
    """Get the external `getxattr()` function from the library. Check its presence."""
    try:
        return cast(GetXAttrFunction, getattr(library, EXTERNAL_GETXATTR_FUNCTION_NAME))
    except AttributeError:
        names = (EXTERNAL_C_LIBRARY_NAME, EXTERNAL_GETXATTR_FUNCTION_NAME)
        raise MissingExternalLibraryFunction(*names) from None

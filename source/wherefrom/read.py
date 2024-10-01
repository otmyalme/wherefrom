"""
Read the value of the “where from” extended file attribute.

The attribute is read by using `ctypes` to call the C function `getxattr()` from the
`libc` library provided as part of macOS. Documentation for that function is provided
by `man getxattr`.
"""

import ctypes
import ctypes.util
from pathlib import Path
import plistlib


# The full name of the “where from” attribute, as a string and a bytes object.
WHERE_FROM_ATTRIBUTE_NAME = "com.apple.metadata:kMDItemWhereFroms"
WHERE_FROM_ATTRIBUTE_NAME_BYTES = WHERE_FROM_ATTRIBUTE_NAME.encode("ascii")

# The name of the C library that provides the necessary functionality for reading the
# “where from“ attribute.
LIBRARY_NAME = "libc"


class WhereFromAttributeReader:
    """Read the value of the “where from” extended file attribute."""
    # This is a class just so that there’s a place to put `library` that isn’t a global
    # variable.

    # The C library that provides the necessary functionality for reading the “where from“
    # attribute.
    library: ctypes.CDLL


    def __init__(self) -> None:
        # Load the C library by its name.
        self.library = ctypes.CDLL(ctypes.util.find_library(LIBRARY_NAME))


    def read_where_from_value(self, path: Path) -> object:
        """
        Read the “where from” value of the given object and return it as a Python object.

        The returned value is most likely a list of strings, but values of other types
        can be returned if the file’s “where from” attribute has been set in an unusual
        manner. Checking for these cases is the responsibility of the caller.
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
        return result  # type: ignore [no-any-return]  # `getxattr()` does return int


    def _parse_binary_where_from_value(self, binary_value: bytes) -> object:
        """Convert the given binary “where from” value into a Python object."""
        return plistlib.loads(binary_value, fmt=plistlib.FMT_BINARY)


# The type of the C string buffer passed to `_call_getxattr()`.
type _Buffer = ctypes.Array[ctypes.c_char]

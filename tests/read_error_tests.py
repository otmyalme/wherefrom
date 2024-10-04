"""
Test the error conditions that can occur in the `wherefrom.read` module.
"""

from datetime import datetime
from pathlib import Path
from plistlib import UID
from typing import cast

import pytest

from wherefrom.read import WhereFromAttributeReader
from wherefrom.errors import (
    MalformedWhereFromValue, CannotReadWhereFromValue,
    FileHasNoWhereFromValue, NoSuchFile, FileNotReadable,
    TooManySymlinks, UnsupportedFileName,
    UnsupportedFileSystem, UnsupportedFileSystemObject,
    WhereFromValueLengthMismatch, IOErrorReadingWhereFromValue,
)


# TESTS USING THE TEST ENVIRONMENT #######################################################

# Errors that can be provoked using actual files (or the absence of an actual file) are
# tested using the test environment created by the `environment` fixture.

ERROR_TEST_PARAMETERS = (
    "file_name", "exception_class", "error_code", "error_name", "message_tail",
)
ERROR_TESTS = [
    (
        "errors/no-value.html", FileHasNoWhereFromValue, 93, "ENOATTR",
        "The file doesn’t have the value set",
    ),
    (
        "errors/no-such-file.png", NoSuchFile, 2, "ENOENT",
        "The file doesn’t exist",
    ),
    (
        "errors/no-value.html/impossible.png", NoSuchFile, 20, "ENOTDIR",
        "The file doesn’t exist",
    ),
    (
        "errors/not-readable.html", FileNotReadable, 13, "EACCES",
        "You don’t have permission to access the file",
    ),
    (
        "errors/not-readable/one-item.html", FileNotReadable, 13, "EACCES",
        "You don’t have permission to access the file",
    ),
    (
        "errors/too-many-symlinks/33", TooManySymlinks, 62, "ELOOP",
        "Had to traverse too many symbolic links",
    ),
    (
        "loops/self-loop/impossible.html", TooManySymlinks, 62, "ELOOP",
        "Had to traverse too many symbolic links",
    ),
    (
        f"l{'o' * 256}ng-name.png", UnsupportedFileName, 63, "ENAMETOOLONG",
        "The length of the file’s name or that of it’s path exceeds the system limits",
    ),
]

@pytest.mark.parametrize(ERROR_TEST_PARAMETERS, ERROR_TESTS)
def test_read_where_from_value__errors(
    environment: Path,
    file_name: str,
    exception_class: type[Exception],
    error_code: int,
    error_name: str,
    message_tail: str,
):
    """Does the function raise appropriate exceptions if something goes wrong?"""
    path = environment / file_name
    with pytest.raises(exception_class) as exception_information:
        WhereFromAttributeReader().read_where_from_value(path)
    exception = cast(CannotReadWhereFromValue, exception_information.value)
    assert exception.error_code == error_code
    assert exception.error_name == error_name
    expected_message = f"Could not read the “were from” value of “{path}”: {message_tail}"
    assert str(exception) == expected_message



# Unexpected Values ----------------------------------------------------------------------

UNEXPECTED_VALUES = [
    ("str.txt", "This is a string"),
    ("bytes.txt", b"This is a bytes object"),
    ("bytearray.txt", bytearray.fromhex("e29d93")),
    ("int.txt", 23),
    ("float.txt", 23.5),
    ("bool.txt", True),
    ("datetime.txt", datetime(2023, 5, 23, 23, 23, 23)),  # noqa: DTZ001  # Yes, no TZ
    ("uid.txt", UID(23)),
    ("none.txt", None),
    ("list.txt", ["foo", 23, b"ar", [1, 2, 3]]),
    ("dict.txt", {"foo": 23, "bar": [1, 2, 3]}),
]

@pytest.mark.parametrize(("file_name", "value"), UNEXPECTED_VALUES)
def test_get_where_from_value__unexpected_values(environment, file_name, value):
    """Are “where from” values of unexpected types read correctly?"""
    path = environment / "unexpected" / file_name
    with pytest.raises(MalformedWhereFromValue) as exception_information:
        WhereFromAttributeReader().read_where_from_value(path)
    exception = exception_information.value
    assert exception.path == path
    assert exception.value == value
    assert (str(exception)) == f"Encountered a malformed “where from” value in “{path}”"


# TESTS USING SYSTEM FILES ###############################################################

# `EPERM` can be provoked by reading the “where from” attribute of `/dev/null`.

def test_read_where_from_value__unsupported_file_system_object():
    """Does the function raise `UnsupportedFileSystemObject` when it’s supposed to?"""
    with pytest.raises(UnsupportedFileSystemObject) as exception_information:
        WhereFromAttributeReader().read_where_from_value(Path("/dev/null"))
    expected_message = (
        "Could not read the “were from” value of “/dev/null”: That type of file system "
        "object doesn’t support the “where from” attribute"
    )
    assert exception_information.value.error_code == 1
    assert exception_information.value.error_name == "EPERM"
    assert str(exception_information.value) == expected_message


# TESTS FOR INTERNAL ERRORS ##############################################################

# `ERANGE` can be provoked by misusing functionality provided by the application.

def test_private_read_where_from_value__buffer_too_small(environment: Path):
    """Does `_read_where_from_value()` handle `ERANGE`?"""
    path = environment / "simple" / "one-item.html"
    with pytest.raises(WhereFromValueLengthMismatch) as exception_information:
        WhereFromAttributeReader()._read_where_from_value(bytes(path), 7)
    expected_message = (
        f"Could not read the “were from” value of “{path}”: Either the value has changed "
        "while it was being read, or there has been an unexpected internal error"
    )
    assert exception_information.value.error_code == 34
    assert exception_information.value.error_name == "ERANGE"
    assert str(exception_information.value) == expected_message


# SIMULATED TESTS ########################################################################

# `getxattr()` errors that cannot be provoked using a real file are tested by calling
# `_get_reading_exception()` with the appropriate error code and checking whether it
# would create the appropriate exception.

ERROR_CODE_TEST_PARAMETERS = (
    "error_code", "exception_class", "error_name", "message_tail",
)
ERROR_CODE_TESTS = [
    (
        -1, CannotReadWhereFromValue, "UNKNOWN",
        "An unexpected error ocurred (error code -1)",
    ),
    (
        45, UnsupportedFileSystem, "ENOTSUP",
        "The file system doesn’t support extended file attributes",
    ),
    (
        22, CannotReadWhereFromValue, "EINVAL",
        "An unexpected error ocurred (error code 22)",
    ),
    (
        21, UnsupportedFileSystemObject, "EISDIR",
        "That type of file system object doesn’t support the “where from” attribute",
    ),
    (
        14, CannotReadWhereFromValue, "EFAULT",
        "An unexpected error ocurred (error code 14)",
    ),
    (
         5, IOErrorReadingWhereFromValue, "EIO",
         "An I/O error occurred",
    ),
]

@pytest.mark.parametrize(ERROR_CODE_TEST_PARAMETERS, ERROR_CODE_TESTS)
def test_private_get_reading_exception(
    error_code: int,
    exception_class: type[Exception],
    error_name: str,
    message_tail: str,
):
    """Does `_get_reading_exception()` return an appropriate exception instance?"""
    path = Path("/Users/no-one/nowhere/simulated-file.png")
    path_bytes = bytes(path)
    exception = WhereFromAttributeReader()._get_reading_exception(path_bytes, error_code)
    assert isinstance(exception, exception_class)
    assert exception.error_code == error_code
    assert exception.error_name == error_name
    expected_message = f"Could not read the “were from” value of “{path}”: {message_tail}"
    assert str(exception) == expected_message

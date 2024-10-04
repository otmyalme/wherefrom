"""
Test errors that can occur when using `getxattr()` to read a “where from” value.
"""

from pathlib import Path

import pytest

from wherefrom.read import WhereFromAttributeReader
from wherefrom.errors import (
    CannotReadWhereFromValue, FileHasNoWhereFromValue, NoSuchFile, FileNotReadable,
    TooManySymlinks, UnsupportedPath, UnsupportedFileSystem, UnsupportedFileSystemObject,
    WhereFromValueLengthMismatch, IOErrorReadingWhereFromValue,
)


# INDIVIDUAL TESTS #######################################################################

def test_read_where_from_value__unsupported_file_system_object():
    """
    Does the function raise `UnsupportedFileSystemObject` when it’s supposed to?
    This can be provoked by reading the “where from” attribute of `/dev/null`.
    """
    path = Path("/dev/null")
    with pytest.raises(UnsupportedFileSystemObject) as exception_information:
        WhereFromAttributeReader().read_where_from_value(path)
    exception = exception_information.value
    assert exception.path == path
    assert exception.error_code == 1
    assert exception.error_name == "EPERM"
    assert str(exception) == (
        "Could not read the “were from” value of “/dev/null”: That type of file system "
        "object doesn’t support the “where from” attribute"
    )


def test_private_read_where_from_value__buffer_too_small(environment: Path):
    """Does `_read_where_from_value()` handle a buffer that’s too small for the value?"""
    path = environment / "simple" / "one-item.html"
    with pytest.raises(WhereFromValueLengthMismatch) as exception_information:
        WhereFromAttributeReader()._read_where_from_value(bytes(path), 7)
    exception = exception_information.value
    assert exception.path == path
    assert exception.error_code == 34
    assert exception.error_name == "ERANGE"
    assert str(exception) == (
        f"Could not read the “were from” value of “{path}”: Either the value has changed "
        "while it was being read, or there has been an unexpected internal error"
    )


# PARAMETRIZED TEST CASES ################################################################

FILE_TEST_CASE_PARAMETERS = (
    "file_name", "exception_class", "error_code", "error_name", "message_tail",
)

# While reading the file with the given name, is an exception of the given type raised?
# Does it have the given error code, error name, and message tail?
FILE_TEST_CASES = [
    # The file has no “where from” value
    (
        "errors/no-value.html", FileHasNoWhereFromValue, 93, "ENOATTR",
        "The file doesn’t have the value set",
    ),
    # The file doesn’t exist
    (
        "errors/no-such-file.png", NoSuchFile, 2, "ENOENT",
        "The file doesn’t exist",
    ),
    (
        "errors/no-value.html/impossible.png", NoSuchFile, 20, "ENOTDIR",
        "The file doesn’t exist",
    ),
    # The file cannot be read
    (
        "errors/not-readable.html", FileNotReadable, 13, "EACCES",
        "You don’t have permission to access the file",
    ),
    (
        "errors/not-readable/one-item.html", FileNotReadable, 13, "EACCES",
        "You don’t have permission to access the file",
    ),
    # There are too many symlinks to follow
    (
        "errors/too-many-symlinks/33", TooManySymlinks, 62, "ELOOP",
        "Had to traverse too many symbolic links",
    ),
    (
        "loops/self-loop/impossible.html", TooManySymlinks, 62, "ELOOP",
        "Had to traverse too many symbolic links",
    ),
    # The path violates the macOS size restrictions
    (
        f"l{'o' * 256}ng-name.png", UnsupportedPath, 63, "ENAMETOOLONG",
        "The length of the file’s name or that of it’s path exceeds the system limits",
    ),
]


ERROR_CODE_TEST_PARAMETERS = (
    "exception_class", "error_code", "error_name", "message_tail",
)

# Would the application raise the given exception class if `getxattr()` were to signal
# an error with the given code? Would it use the given error name and message tail?
ERROR_CODE_TESTS = [
    # Error codes that raise a custom exception class
    (
        UnsupportedFileSystem, 45, "ENOTSUP",
        "The file system doesn’t support extended file attributes",
    ),
    (
        UnsupportedFileSystemObject, 21, "EISDIR",
        "That type of file system object doesn’t support the “where from” attribute",
    ),
    (
        IOErrorReadingWhereFromValue, 5, "EIO",
        "An I/O error occurred",
    ),
    # Errors codes that raise `CannotReadWhereFromValue`
    (
        CannotReadWhereFromValue, 22, "EINVAL",
        "An unexpected error ocurred (error code 22)",
    ),
    (
        CannotReadWhereFromValue, 14, "EFAULT",
        "An unexpected error ocurred (error code 14)",
    ),
    (
        CannotReadWhereFromValue, -1, "UNKNOWN",
        "An unexpected error ocurred (error code -1)",
    ),
]


@pytest.mark.parametrize(FILE_TEST_CASE_PARAMETERS, FILE_TEST_CASES)
def test_read_where_from_value__errors(
    environment: Path,
    file_name: str,
    exception_class: type[CannotReadWhereFromValue],
    error_code: int,
    error_name: str,
    message_tail: str,
):
    """Do the test cases that read the “where from” value of an actual files pass?"""
    path = environment / file_name
    with pytest.raises(exception_class) as exception_information:
        WhereFromAttributeReader().read_where_from_value(path)
    exception = exception_information.value
    assert exception.path == path
    assert exception.error_code == error_code
    assert exception.error_name == error_name
    assert str(exception) == (
        f"Could not read the “were from” value of “{path}”: {message_tail}"
    )


@pytest.mark.parametrize(ERROR_CODE_TEST_PARAMETERS, ERROR_CODE_TESTS)
def test_private_get_reading_exception(
    exception_class: type[CannotReadWhereFromValue],
    error_code: int,
    error_name: str,
    message_tail: str,
):
    """Do the test cases that simulate an error with a given error code pass?"""
    path = Path("/Users/no-one/nowhere/simulated-file.png")
    path_bytes = bytes(path)
    exception = WhereFromAttributeReader()._get_reading_exception(path_bytes, error_code)
    assert isinstance(exception, exception_class)
    assert exception.path == path
    assert exception.error_code == error_code
    assert exception.error_name == error_name
    assert str(exception) == (
        f"Could not read the “were from” value of “{path}”: {message_tail}"
    )

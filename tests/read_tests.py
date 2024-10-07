"""
Test the happy paths of the `wherefrom.read` module.

Errors are tested by `tests.read_error_tests`, not by this module.
"""

import ctypes.util
from pathlib import Path

import pytest

import wherefrom.read
from wherefrom.read import (
    read_binary_where_from_value, _read_where_from_value_length, _read_where_from_value,
    _get_reading_exception, _load_external_getxattr_function,
)
from wherefrom.readexceptions import *


# LOADING THE EXTERNAL C FUNCTION ########################################################

def test__load_external_getxattr_function__repeatedly():
    """Do repeated `_load_external_getxattr_function()` calls return the same object?"""
    assert _load_external_getxattr_function() is _load_external_getxattr_function()


def test__load_external_getxattr_function__no_libc(monkeypatch):
    """Is the appropriate exception raised if `libc` cannot be found?"""
    monkeypatch.setattr(wherefrom.read, "external_getxattr_function", None)
    monkeypatch.setattr(ctypes.util, "find_library", lambda _: "/no/such/path")
    with pytest.raises(MissingExternalLibrary) as exception_information:
        _load_external_getxattr_function()
    exception = exception_information.value
    assert exception.library_name == "libc"
    assert str(exception) == "Could not load the external library “libc”"


def test__load_external_getxattr_function__no_getxattr_function(monkeypatch):
    """Is the appropriate exception raised if the `getxattr()` function is missing?"""
    monkeypatch.setattr(wherefrom.read, "external_getxattr_function", None)
    monkeypatch.setattr(wherefrom.read, "EXTERNAL_GETXATTR_FUNCTION_NAME", "no_such_name")
    with pytest.raises(MissingExternalLibraryFunction) as exception_information:
        _load_external_getxattr_function()
    exception = exception_information.value
    assert exception.library_name == "libc"
    assert exception.function_name == "no_such_name"
    assert str(exception) == (
        "The external library “libc” doesn’t have a function named “no_such_name”"
    )


# PRIVATE FUNCTIONS ######################################################################

def test__read_where_from_value_length(environment: Path):
    """Does `_read_where_from_value_length()` return the expected length?"""
    path = environment / "simple" / "one-item.html"
    length = _read_where_from_value_length(bytes(path))
    assert length == 77


def test__read_where_from_value__happy(environment: Path):
    """Does `_read_where_from_value()` return the expected binary value?"""
    path = environment / "simple" / "one-item.html"
    binary_value = _read_where_from_value(bytes(path), 77)
    assert binary_value.startswith(b"bplist00")
    assert b"http://nowhere.test/index.html" in binary_value


def test__read_where_from_value__buffer_too_small(environment: Path):
    """Does `_read_where_from_value()` handle a buffer that’s too small for the value?"""
    path = environment / "simple" / "one-item.html"
    with pytest.raises(WhereFromValueLengthMismatch) as exception_information:
        _read_where_from_value(bytes(path), 7)
    exception = exception_information.value
    assert exception.path == path
    assert exception.error_code == 34
    assert exception.error_name == "ERANGE"
    assert str(exception) == (
        f"Could not read the “were from” value of “{path}”: Either the value has changed "
        "while it was being read, or there has been an unexpected internal error"
    )


# HAPPY PATHS ############################################################################

# `read_binary_where_from_value()` receives further testing as an inevitable but welcome
# part of the tests for the `wherefrom.parse` module.

def test_read_where_from_value__happy(environment: Path):
    """Does `read_binary_where_from_value()` return the expected binary value?"""
    path = environment / "simple" / "one-item.html"
    binary_value = read_binary_where_from_value(path)
    assert binary_value.startswith(b"bplist00")
    assert b"http://nowhere.test/index.html" in binary_value


def test_read_where_from_value__directory(environment: Path):
    """What if the file is actually a directory?"""
    path = environment / "simple" / "directory-with-where-from-value"
    binary_value = read_binary_where_from_value(path)
    assert binary_value.startswith(b"bplist00")
    assert b"http://nowhere.test/index.html" in binary_value


def test_read_where_from_value__unicode_name(environment: Path):
    """What if the file’s name contains Unicode?"""
    path = environment / "simple" / "unicode-name\N{HEAVY EXCLAMATION MARK SYMBOL}.html"
    binary_value = read_binary_where_from_value(path)
    assert binary_value.startswith(b"bplist00")
    assert b"http://nowhere.test/index.html" in binary_value


# ERROR CONDITIONS › INDIVIDUAL TESTS ####################################################

def test_read_where_from_value__unsupported_file_system_object():
    """
    Does the function raise `UnsupportedFileSystemObject` when it’s supposed to?
    This can be provoked by trying to read the “where from” attribute of `/dev/null`.
    """
    path = Path("/dev/null")
    with pytest.raises(UnsupportedFileSystemObject) as exception_information:
        read_binary_where_from_value(path)
    exception = exception_information.value
    assert exception.path == path
    assert exception.error_code == 1
    assert exception.error_name == "EPERM"
    assert str(exception) == (
        "Could not read the “were from” value of “/dev/null”: That type of file system "
        "object doesn’t support the “where from” attribute"
    )


# ERROR CONDITIONS › PARAMETRIZED TESTS › PARAMETER DEFINITIONS ##########################

FILE_TEST_CASE_PARAMETERS = (
    "file_name", "exception_class", "error_code", "error_name", "message_tail",
)

# While reading the file with the given name, is an exception of the given type raised?
# Does it have the given error code, error name, and message tail?
FILE_TEST_CASES = [
    # The file has no “where from” value
    (
        "errors/no-value.html", NoWhereFromValue, 93, "ENOATTR",
        "The file doesn’t have the value set",
    ),
    (
        "errors/no-value-\N{CROSS MARK}.html", NoWhereFromValue, 93, "ENOATTR",
        "The file doesn’t have the value set",
    ),
    # The file doesn’t exist
    (
        "errors/no-such-file.png", MissingFile, 2, "ENOENT",
        "The file doesn’t exist",
    ),
    (
        "errors/no-value.html/impossible.png", MissingFile, 20, "ENOTDIR",
        "The file doesn’t exist",
    ),
    # The file cannot be read
    (
        "errors/not-readable.html", NoReadPermission, 13, "EACCES",
        "You don’t have permission to access the file",
    ),
    (
        "errors/not-readable/one-item.html", NoReadPermission, 13, "EACCES",
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
    # Expected errors
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
    # Unexpected Errors
    (
        UnexpectedErrorReadingWhereFromValue, 22, "EINVAL",
        "An unexpected error ocurred (EINVAL)",
    ),
    (
        UnexpectedErrorReadingWhereFromValue, 14, "EFAULT",
        "An unexpected error ocurred (EFAULT)",
    ),
    (
        UnknownErrorReadingWhereFromValue, -1, "UNKNOWN",
        "An unknown error ocurred (error code -1)",
    ),
]


# ERROR CONDITIONS › PARAMETRIZED TESTS › TEST FUNCTIONS #################################

@pytest.mark.parametrize(FILE_TEST_CASE_PARAMETERS, FILE_TEST_CASES)
def test_read_where_from_value__errors(
    environment: Path,
    file_name: str,
    exception_class: type[WhereFromValueReadingError],
    error_code: int,
    error_name: str,
    message_tail: str,
):
    """Do the test cases that read the “where from” value of an actual files pass?"""
    path = environment / file_name
    with pytest.raises(exception_class) as exception_information:
        read_binary_where_from_value(path)
    exception = exception_information.value
    assert exception.path == path
    assert exception.error_code == error_code
    assert exception.error_name == error_name
    assert str(exception) == (
        f"Could not read the “were from” value of “{path}”: {message_tail}"
    )


@pytest.mark.parametrize(ERROR_CODE_TEST_PARAMETERS, ERROR_CODE_TESTS)
def test_private_get_reading_exception(
    exception_class: type[WhereFromValueReadingError],
    error_code: int,
    error_name: str,
    message_tail: str,
):
    """Do the test cases that simulate an error with a given error code pass?"""
    path = Path("/Users/no-one/nowhere/simulated-file.png")
    path_bytes = bytes(path)
    exception = _get_reading_exception(path_bytes, error_code)
    assert isinstance(exception, exception_class)
    assert exception.path == path
    assert exception.error_code == error_code
    assert exception.error_name == error_name
    assert str(exception) == (
        f"Could not read the “were from” value of “{path}”: {message_tail}"
    )

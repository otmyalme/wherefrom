"""
Test the error conditions that can occur in the `wherefrom.read` module.
"""

from pathlib import Path

import pytest

from wherefrom.read import WhereFromAttributeReader
from wherefrom.errors import (
    NoSuchFile, FileHasNoWhereFromValue, UnsupportedFileSystem,
    WhereFromValueLengthMismatch, UnsupportedFileSystemObject,
)


# TESTS USING THE TEST ENVIRONMENT #######################################################

# Errors that can be provoked using actual files (or the absence of an actual file) are
# tested using the test environment created by the `environment` fixture.

ERROR_TEST_PARAMETERS = ("file_name", "exception_class", "message_tail")
ERROR_TESTS = [
    ("no-value.png", FileHasNoWhereFromValue, "The file doesn’t have the value set"),
    ("no-such-file.png", NoSuchFile, "The file doesn’t exist"),
]

@pytest.mark.parametrize(ERROR_TEST_PARAMETERS, ERROR_TESTS)
def test_read_where_from_value__errors(
    environment: Path,
    file_name: str,
    exception_class: type[Exception],
    message_tail: str,
):
    """Does the function raise appropriate exceptions if something goes wrong?"""
    path = environment / file_name
    with pytest.raises(exception_class) as exception_information:
        WhereFromAttributeReader().read_where_from_value(path)
    expected_message = f"Could not read the “were from” value of “{path}”: {message_tail}"
    assert str(exception_information.value) == expected_message


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
    assert str(exception_information.value) == expected_message


# SIMULATED TESTS ########################################################################

# `getxattr()` errors that cannot be provoked using a real file are tested by calling
# `_get_reading_exception()` with the appropriate error code and checking whether it
# would create the appropriate exception.

ERROR_CODE_TEST_PARAMETERS = ("error_code", "exception_class", "message_tail")
ERROR_CODE_TESTS = [
    (
        45,
        UnsupportedFileSystem,
        "The file system doesn’t support extended file attributes",
    ),
]

@pytest.mark.parametrize(ERROR_CODE_TEST_PARAMETERS, ERROR_CODE_TESTS)
def test_private_get_reading_exception(
    error_code: int,
    exception_class: type[Exception],
    message_tail: str,
):
    """Does `_get_reading_exception()` return an appropriate exception instance?"""
    path = Path("/Users/no-one/nowhere/simulated-file.png")
    path_bytes = bytes(path)
    exception = WhereFromAttributeReader()._get_reading_exception(path_bytes, error_code)
    assert isinstance(exception, exception_class)
    expected_message = f"Could not read the “were from” value of “{path}”: {message_tail}"
    assert str(exception) == expected_message

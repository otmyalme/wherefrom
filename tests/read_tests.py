"""
Test the `wherefrom.read` module.
"""

from datetime import datetime
from pathlib import Path
from plistlib import UID

import pytest

from wherefrom.read import WhereFromAttributeReader, FileHasNoWhereFromValue, NoSuchFile


# READING THE VALUE ######################################################################

# Simple Tests ---------------------------------------------------------------------------

def test_read_where_from_value__one_item(environment: Path):
    """Is a “where from” value consisting of one string read correctly?"""
    path = environment / "simple" / "one-item.html"
    value = WhereFromAttributeReader().read_where_from_value(path)
    assert value == ["http://nowhere.test/index.html"]


def test_read_where_from_value__two_items(environment: Path):
    """What about two strings?"""
    path = environment / "simple" / "two-items.png"
    value = WhereFromAttributeReader().read_where_from_value(path)
    assert value == ["http://nowhere.test/banner.png", "http://nowhere.test/index.html"]


# Weird Values ---------------------------------------------------------------------------

WEIRD_TYPE_TESTS = [
    ("str.png", "This is a string"),
    ("bytes.png", b"This is a bytes object"),
    ("bytearray.png", bytearray.fromhex("e29d93")),
    ("int.png", 23),
    ("float.png", 23.5),
    ("bool.png", True),
    ("datetime.png", datetime(2023, 5, 23, 23, 23, 23)),  # noqa: DTZ001  # Yes, no TZ
    ("uid.png", UID(23)),
    ("none.png", None),
    ("list.png", ["foo", 23, b"ar", [1, 2, 3]]),
    ("dict.png", {"foo": 23, "bar": [1, 2, 3]}),
]


@pytest.mark.parametrize(("file_name", "expected"), WEIRD_TYPE_TESTS)
def test_get_where_from_value__weird_types(environment, file_name, expected):
    """Just out of curiosity: Are various weird “where from” values actually possible?"""
    path = environment / "weird-types" / file_name
    actual = WhereFromAttributeReader().read_where_from_value(path)
    if isinstance(expected, bool):
        assert actual is expected
    else:
        assert actual == expected


# Errors ---------------------------------------------------------------------------------

ERROR_TESTS = [
    ("no-value.png", FileHasNoWhereFromValue, "The file doesn’t have the value set"),
    ("no-such-file.png", NoSuchFile, "The file doesn’t exist"),
]


@pytest.mark.parametrize(("file_name", "exception", "message_tail"), ERROR_TESTS)
def test_read_where_from_value__errors(
    environment: Path,
    file_name: str,
    exception: type[Exception],
    message_tail: str,
):
    """Does the function raise appropriate exceptions if something goes wrong?"""
    path = environment / file_name
    with pytest.raises(exception) as exception_information:
        WhereFromAttributeReader().read_where_from_value(path)
    expected_message = f"Could not read the “were from” value of “{path}”: {message_tail}"
    assert str(exception_information.value) == expected_message


# PRIVATE METHODS ########################################################################

def test_private_read_where_from_value_length(environment: Path):
    """Does `_read_where_from_value_length()` return the expected length?"""
    path = environment / "simple" / "one-item.html"
    length = WhereFromAttributeReader()._read_where_from_value_length(bytes(path))
    assert length == 77


def test_private_read_where_from_value(environment: Path):
    """Does `_read_where_from_value()` return the expected binary value?"""
    path = environment / "simple" / "one-item.html"
    binary_value = WhereFromAttributeReader()._read_where_from_value(bytes(path), 77)
    assert binary_value.startswith(b"bplist00")
    assert b"http://nowhere.test/index.html" in binary_value

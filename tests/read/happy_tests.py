"""
Test the happy paths of the `wherefrom.read` module.

Errors are tested by `tests.read_error_tests`, not by this module.
"""

from pathlib import Path

from wherefrom.read import WhereFromAttributeReader


# READING THE VALUE ######################################################################

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


def test_read_where_from_value__directory(environment: Path):
    """What if the file is actually a directory?"""
    path = environment / "simple" / "directory-with-where-from-value"
    value = WhereFromAttributeReader().read_where_from_value(path)
    assert value == ["http://nowhere.test/index.html"]


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

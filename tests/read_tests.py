"""Test the `wherefrom.read` module."""

from pathlib import Path

from wherefrom.read import WhereFromAttributeReader


# PRIVATE METHODS ########################################################################

def test_read_where_from_attribute_length(environment: Path):
    """Does `_read_where_from_attribute_length()` return the expected length?"""
    path = environment / "simple" / "one-item.html"
    length = WhereFromAttributeReader()._read_where_from_attribute_length(bytes(path))
    assert length == 77


def test_read_where_from_attribute(environment: Path):
    """Does `_read_where_from_attribute()` return the expected binary value?"""
    path = environment / "simple" / "one-item.html"
    binary_value = WhereFromAttributeReader()._read_where_from_attribute(bytes(path), 77)
    assert binary_value.startswith(b"bplist00")
    assert b"http://nowhere.test/index.html" in binary_value

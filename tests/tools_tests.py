"""
Test the `wherefrom.tools` module.
"""

from pathlib import Path

from wherefrom.tools import (
    as_path_object, multiline_string_as_one_line, is_nonempty_list_of_strings,
)


def test_as_path_object():
    """Does `as_path_object() do what it’s supposed to?"""
    expected = Path("/Users/someone/somewhere")
    assert as_path_object(b"/Users/someone/somewhere") == expected
    assert as_path_object("/Users/someone/somewhere") == expected
    assert as_path_object(expected) is expected


MULTILINE_STRING = """
    This string is broken
    across three different lines
    for no good reason.
"""

def test_multiline_string_as_one_line():
    """Does `multiline_string_as_one_line()` do what it’s supposed to?"""
    assert multiline_string_as_one_line("Single line!") == "Single line!"
    assert multiline_string_as_one_line(MULTILINE_STRING) == (
        "This string is broken across three different lines for no good reason.")


def test_is_nonempty_list_of_strings():
    """Does `is_nonempty_list_of_strings()` do what it’s supposed to?"""
    assert is_nonempty_list_of_strings(["test"])
    assert is_nonempty_list_of_strings(["test", "test", "test"])
    assert not is_nonempty_list_of_strings([])
    assert not is_nonempty_list_of_strings(["test", b"test", "test"])
    assert not is_nonempty_list_of_strings(["test", 7357, "test"])
    assert not is_nonempty_list_of_strings(("test", "test", "test"))
    assert not is_nonempty_list_of_strings(object())

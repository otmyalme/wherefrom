"""
Test the `wherefrom.parse` module, and parts of the `wherefrom.read` module.

The tests in this module read the “where from” values from actual files in the test
environment rather than call `parse_binary_where_from_value()` with binary values that
cannot readily be understood by human readers. As a result, they inevitably test the
happy paths of the `read_binary_where_from_value()` as well, which is probably a good
thing, since the actual tests for that module cannot really do much other than check
that the binary values contain a couple of recognizable substrings.
"""

from datetime import datetime
from pathlib import Path
from plistlib import UID
import pytest

from wherefrom.read import read_binary_where_from_value
from wherefrom.parse import parse_binary_where_from_value, UnexpectedWhereFromValue

from tests.tools.environment.items import WhereFromValue


# HAPPY TESTS ############################################################################

def test_parse_binary_where_from_value__one_item(environment: Path):
    """Is a “where from” value consisting of one string read correctly?"""
    path = environment / "simple" / "one-item.html"
    binary_value = read_binary_where_from_value(path)
    value = parse_binary_where_from_value(binary_value, path)
    assert value == ["http://nowhere.test/index.html"]


def test_parse_binary_where_from_value__two_items(environment: Path):
    """What about two strings?"""
    path = environment / "simple" / "two-items.png"
    binary_value = read_binary_where_from_value(path)
    value = parse_binary_where_from_value(binary_value, path)
    assert value == ["http://nowhere.test/banner.png", "http://nowhere.test/index.html"]


# UNEXPECTED VALUES ######################################################################

# A datetime value used as the “where from” value of one test file. There’s no time zone,
# because that’s how the value is returned from `plistlib`.
DATETIME_VALUE = datetime(2023, 5, 23, 23, 23, 23)  # noqa: DTZ001  # See above

# Does the file with the given name have the given unexpected “where from” value?
UNEXPECTED_WHERE_FROM_VALUE_TEST_CASES: list[tuple[str, WhereFromValue]] = [
    ("list-empty.txt", []),
    ("none.txt", None),
    ("bool-true.txt", True),
    ("bool-false.txt", False),
    ("int.txt", 23),
    ("float.txt", 23.5),
    ("datetime.txt", DATETIME_VALUE),
    ("bytes.txt", b"This is a bytes object"),
    ("str.txt", "This is a string"),
    ("uid.txt", UID(23)),
    ("list-mixed.txt", ["foo", 23, b"ar", [1, 2, 3]]),
    ("dict.txt", {"foo": 23, "bar": [1, 2, 3]}),
]

@pytest.mark.parametrize(("file_name", "value"), UNEXPECTED_WHERE_FROM_VALUE_TEST_CASES)
def test_parse_binary_where_from_value__unexpected_values(environment, file_name, value):
    """Do the test cases that check unexpected “where from” values pass?"""
    path = environment / "unexpected" / file_name
    binary_value = read_binary_where_from_value(path)
    with pytest.raises(UnexpectedWhereFromValue) as exception_information:
        parse_binary_where_from_value(binary_value, path)
    exception = exception_information.value
    assert exception.path == path
    assert exception.value == value
    assert type(exception.value) is type(value)
    assert str(exception) == (
        f"Encountered an unexpected “where from” value in “{path}”"
    )

"""
Tests errors that can occur when a “where from” value doesn’t have the expected form.
"""

from datetime import datetime
from plistlib import UID
import pytest

from tests.tools.environment.items import WhereFromValue
from wherefrom.read import WhereFromAttributeReader
from wherefrom.errors import UnexpectedWhereFromValue


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
def test_get_where_from_value__unexpected_values(environment, file_name, value):
    """Do the test cases that read unexpected “where from” values pass?"""
    path = environment / "unexpected" / file_name
    with pytest.raises(UnexpectedWhereFromValue) as exception_information:
        WhereFromAttributeReader().read_where_from_value(path)
    exception = exception_information.value
    assert exception.path == path
    assert exception.value == value
    assert type(exception.value) is type(value)
    assert (str(exception)) == f"Encountered an unexpected “where from” value in “{path}”"

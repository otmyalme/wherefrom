"""
Parse the binary value of the “where from” extended file attribute.

The value is parsed using the `plistlib` library, which is part of Python.
"""

from pathlib import Path
import plistlib

from wherefrom.tools import is_nonempty_list_of_strings
from wherefrom.exceptions import WhereFromValueError


# PUBLIC FUNCTIONS #######################################################################

def parse_binary_where_from_value(binary_value: bytes, path: Path) -> list[str]:
    """
    Parse the given binary “where from” value.

    Raises `MalformedWhereFromValue` if the value cannot be parsed as a macOS property
    list, and raises `UnexpectedWhereFromValue` if the parsed value is something other
    than a list of one or more strings.

    A path needs to be provided so that it can be included in the exceptions.
    """
    value = _parse_binary_where_from_value(binary_value, path)
    if is_nonempty_list_of_strings(value):
        return value
    else:
        raise UnexpectedWhereFromValue(path, value)


# PARSING THE VALUE ######################################################################

def _parse_binary_where_from_value(binary_value: bytes, path: Path) -> object:
    """Convert the given binary “where from” value into a Python object."""
    try:
        return plistlib.loads(binary_value, fmt=plistlib.FMT_BINARY)
    except plistlib.InvalidFileException:
        raise MalformedWhereFromValue(path, binary_value) from None


# EXCEPTION CLASSES ######################################################################

class WhereFromValueValueError(WhereFromValueError):
    """
    The base class of exceptions that are raised if there is something wrong with the
    “where from” value itself.
    """


class MalformedWhereFromValue(WhereFromValueValueError, ValueError):
    """
    Raised if a “where from” value cannot be parsed. This probably cannot actually happen
    if the value came from a file.
    """
    MESSAGE = "Encountered a malformed “where from” value in “{path}”"
    binary_value: bytes


class UnexpectedWhereFromValue(WhereFromValueValueError, ValueError):
    """
    Raised if a “where from” value is something other than a list of one or more strings.
    """
    MESSAGE = "Encountered an unexpected “where from” value in “{path}”"
    value: object

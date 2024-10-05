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

    Raises `UnexpectedWhereFromValue` if the parsed value is something other than a list
    of one or more strings.
    """
    value = _parse_binary_where_from_value(binary_value)
    if is_nonempty_list_of_strings(value):
        return value
    else:
        raise UnexpectedWhereFromValue(path, value)


# PARSING THE VALUE ######################################################################

def _parse_binary_where_from_value(binary_value: bytes) -> object:
    """Convert the given binary “where from” value into a Python object."""
    return plistlib.loads(binary_value, fmt=plistlib.FMT_BINARY)


# EXCEPTION CLASSES ######################################################################

class UnexpectedWhereFromValue(WhereFromValueError):
    """
    Raised if a “where from” value is something other than a list of one or more strings.
    """
    MESSAGE = "Encountered an unexpected “where from” value in “{path}”"
    value: object

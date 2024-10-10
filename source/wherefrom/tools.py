"""
Provide assorted utility functions that are useful for the application.
"""

import re
from typing import TypeGuard


LINE_BREAK_PATTERN = re.compile(r"\s*\n\s*")

def multiline_string_as_one_line(string: str) -> str:
    """
    Replace line breaks and all surrounding whitespace in the given string with a single
    space, and remove all leading and trailing whitespace.

    This may be useful to remove extraneous whitespace from a triple-quoted string, but
    the function doesn’t retain additional indentation or paragraph breaks like the one
    above, and it doesn’t handle bulleted lists or any other special formatting that may
    be used in a triple-quoted string.
    """
    return LINE_BREAK_PATTERN.sub(" ", string.strip())


def is_nonempty_list_of_strings(value: object) -> TypeGuard[list[str]]:
    """Check whether the given object is a list of strings with at least one element."""
    return is_list_of_strings(value) and bool(value)


def is_list_of_strings(value: object) -> TypeGuard[list[str]]:
    """Check whether the given object is a list of strings."""
    return isinstance(value, list) and all(isinstance(element, str) for element in value)

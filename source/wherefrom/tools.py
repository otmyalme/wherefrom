"""
Provide assorted utility functions that are useful for the application.
"""

import re


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

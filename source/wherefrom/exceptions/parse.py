"""
Define the exceptions raised by `wherefrom.parse`.
"""

from wherefrom.exceptions.file import FileError


class WhereFromValueValueError(FileError):
    """
    The base class of exceptions that are raised if there’s something wrong with the
    “where from” value itself.
    """


class MalformedWhereFromValue(WhereFromValueValueError, ValueError):
    """
    Raised if a “where from” value cannot be parsed. This probably cannot actually happen
    if the value came from a file.
    """
    MESSAGE = "The “where from” value of “{path}” is malformed"
    binary_value: bytes


class UnexpectedWhereFromValue(WhereFromValueValueError, ValueError):
    """
    Raised if a “where from” value is something other than a list of one or more strings.
    """
    MESSAGE = "The “where from” value of “{path}” doesn’t have the expected form"
    value: object

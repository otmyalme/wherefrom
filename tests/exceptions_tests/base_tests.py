"""
Test the `wherefrom.exceptions.base` module.
"""

from dataclasses import is_dataclass
import re

import wherefrom.exceptions.base as module
from wherefrom.exceptions.base import WhereFromException


# SUBCLASSES FOR USE IN THE TESTS ########################################################

class ExampleException(WhereFromException):
    """An example `WhereFromException` subclass for use in the tests."""
    MESSAGE = "An example error occurred: “{example_attribute}”"
    example_attribute: str


class ExampleExceptionWithPrefix(WhereFromException):
    """Another example subclass that uses a prefix."""
    # `MESSAGE_PREFIX` and `MESSAGE` are broken across multiple lines for testing purposes
    MESSAGE_PREFIX = """
        Prefix
        ({a})
    """
    MESSAGE = """
        Message
        ({b})
    """
    a: int
    b: int


class ExampleExceptionWithPrefixSubclass(ExampleExceptionWithPrefix):
    """An example subclass that inherits attributes and a prefix from the previous one."""
    MESSAGE = "Message ({b}+{c})"
    c: int


# THE TESTS ##############################################################################

def test_where_from_exception__subclasses_are_dataclasses():
    """Are subclasses of `WhereFromException` dataclasses?"""
    assert is_dataclass(ExampleException)
    assert is_dataclass(ExampleExceptionWithPrefixSubclass)


def test_where_from_exception__attribute_access():
    """Does attribute access work as expected?"""
    assert ExampleException("test").example_attribute == "test"
    inherited = ExampleExceptionWithPrefixSubclass(1, 2, 3)
    assert inherited.a == 1
    assert inherited.b == 2
    assert inherited.c == 3


def test_where_from_exception__string_representation():
    """Does the exception’s string representation get constructed as expected?"""
    assert str(ExampleException("test")) == "An example error occurred: “test”"
    assert str(ExampleExceptionWithPrefix(1, 2)) == "Prefix (1): Message (2)"
    assert str(ExampleExceptionWithPrefixSubclass(1, 2, 3)) == "Prefix (1): Message (2+3)"


def test_all_exceptions_in_hierarchy():
    """Is the exception hierarchy in `wherefrom.exceptions.base`’s docstring complete?"""
    pending = [WhereFromException]
    while pending:
        cls = pending.pop()
        if not cls.__module__.startswith("tests."):
            pattern = re.compile(rf"\b{cls.__name__}\b")
            assert pattern.search(module.__doc__)
            pending.extend(cls.__subclasses__())

"""
Provides the base class for the application’s exceptions.

The application’s exception hierarchy is structured as follows:

    WhereFromException
     └─ ReadWhereFromValueError
         └─ CannotReadWhereFromValue
             └─ NoSuchFile
"""

from dataclasses import dataclass
import re
from typing import ClassVar


class WhereFromException(Exception):
    """
    The base class for all exceptions raised by the application.

    Automatically turns all subclasses into dataclasses, and subclasses should have their
    arguments defined as fields, so that they can be accessed in a reasonable manner.

    Also, automatically constructs the exception message, by `format()`ing `MESSAGE` with
    the object’s attributes. If `MESSAGE_PREFIX` is nonempty, it is first prepended to
    `MESSAGE` using “: ” as a separator. This allows trees of the exception hierarchy to
    define a common “⟨problem⟩: ⟨cause⟩” structure.
    """
    MESSAGE_PREFIX: ClassVar[str] = ""
    MESSAGE: ClassVar[str] = "No error message has been provided"

    def __init_subclass__(cls) -> None:
        """Automatically turn subclasses into dataclasses and fix message whitespace."""
        dataclass(cls)
        cls.MESSAGE_PREFIX = clean_exception_message(cls.MESSAGE_PREFIX)
        cls.MESSAGE = clean_exception_message(cls.MESSAGE)

    def __str__(self) -> str:
        """Construct the exception message from `MESSAGE` and `MESSAGE_PREFIX`."""
        if self.MESSAGE_PREFIX:
            template = f"{self.MESSAGE_PREFIX.rstrip(": ")}: {self.MESSAGE}"
        else:
            template = self.MESSAGE
        return template.format(**vars(self))


# UTILITY FUNCTIONS ######################################################################

LINE_BREAK_PATTERN = re.compile(r" *\n *")


def clean_exception_message(message: str) -> str:
    """
    Replace newlines in the given string and any surrounding spaces into a single space.
    """
    return LINE_BREAK_PATTERN.sub(" ", message.strip())

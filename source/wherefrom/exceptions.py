"""
Provides base classes for the exceptions used by the application.

The application’s exception hierarchy is structured as follows:

    WhereFromException
     ├─ MissingExternalDependencyError
     │   ├─ MissingExternalLibrary
     │   └─ MissingExternalLibraryFunction
     └─ WhereFromValueError
         ├─ WhereFromValueReadingError
         │   ├─ NoWhereFromValue
         │   ├─ MissingFile
         │   ├─ NoReadPermission
         │   ├─ TooManySymlinks
         │   ├─ UnsupportedPath
         │   ├─ UnsupportedFileSystem
         │   ├─ UnsupportedFileSystemObject
         │   ├─ WhereFromValueLengthMismatch
         │   ├─ IOErrorReadingWhereFromValue
         │   └─ UnexpectedErrorReadingWhereFromValue
         │       └─ UnknownErrorReadingWhereFromValue
         └─ WhereFromValueValueError
             ├─ MalformedWhereFromValue
             └─ UnexpectedWhereFromValue
"""

from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

from wherefrom.tools import multiline_string_as_one_line


# BASE CLASS #############################################################################

class WhereFromException(Exception):
    """
    The base class for all exceptions raised by the application.

    Automatically turns all subclasses into dataclasses, so that error information can be
    accessed in a reasonable manner. Subclasses must define their arguments as fields.

    Also, automatically constructs the exception message, by `format()`ing `MESSAGE` with
    the object’s attributes. If `MESSAGE_PREFIX` is nonempty, it is first prepended to
    `MESSAGE` using “: ” as a separator. This allows subtrees of the exception hierarchy
    to define a common “⟨problem⟩: ⟨cause⟩” structure.

    Whitespace in `MESSAGE` and `MESSAGE_PREFIX` is automatically normalized: Line breaks
    and all surrounding whitespace is replaced with a single space, and all leading and
    trailing whitespace is removed. Multi-line exception messages aren’t supported.
    """
    MESSAGE_PREFIX: ClassVar[str] = ""
    MESSAGE: ClassVar[str] = "No error message has been provided"

    def __init_subclass__(cls) -> None:
        """Automatically turn subclasses into dataclasses and fix message whitespace."""
        dataclass(cls)
        cls.MESSAGE_PREFIX = multiline_string_as_one_line(cls.MESSAGE_PREFIX)
        cls.MESSAGE = multiline_string_as_one_line(cls.MESSAGE)

    def __str__(self) -> str:
        """Construct the exception message from `MESSAGE` and `MESSAGE_PREFIX`."""
        if self.MESSAGE_PREFIX:
            template = f"{self.MESSAGE_PREFIX.rstrip(": ")}: {self.MESSAGE}"
        else:
            template = self.MESSAGE
        return template.format(**vars(self))


# BASE CLASSES FOR SUB-HIERARCHIES #######################################################

class WhereFromValueError(WhereFromException):
    """A base class for exceptions related to a file’s “where from” value."""
    path: Path

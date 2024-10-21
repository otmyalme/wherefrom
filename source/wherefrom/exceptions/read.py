"""
Define the exceptions specific to reading the “where from” value.

Exceptions for issues that could apply to any file operation (such as the lack of read
permissions) are defined in `wherefrom.exceptions.file`.

As in that module, the exception classes have decorators that register the class for
one or more error codes.

Information regarding the error codes `getxattr()` uses was taken from its manpage.
"""

from wherefrom.exceptions.base import WhereFromException
from wherefrom.exceptions.file import LowLevelFileError
from wherefrom.exceptions.registry import register_for


# GETXATTR() ERRORS ######################################################################

class WhereFromValueReadingError(LowLevelFileError):
    """
    The base class for exceptions that are raised if an error occurs while reading a
    file’s binary “where from” value.
    """


@register_for("ENOATTR", operations=["getxattr"])
class NoWhereFromValue(WhereFromValueReadingError, KeyError):
    """Raised when reading the “where from” value of a file that doesn’t have one."""
    MESSAGE = "The {file_type} doesn’t have the value set"


@register_for("ENOTSUP", operations=["getxattr"])
class UnsupportedFileSystem(WhereFromValueReadingError):
    """
    Raised when reading the “where from” value of a file on a file system that doesn’t
    support extended file attributes.

    This hasn’t, so far, been tested on an actual file. Experiments involving FAT and
    ExFAT disk images created by macOS and the internal memory of an ancient digital
    camera found that all support extended file attributes.
    """
    MESSAGE = "The file system doesn’t support extended file attributes"


@register_for("EPERM", operations=["getxattr"])
@register_for("EISDIR", operations=["getxattr"])
class UnsupportedFileSystemObject(WhereFromValueReadingError):
    """
    Raised when reading the “where from” value of a file system object that doesn’t
    support the attribute (or extended attributes in general). `/dev/null` qualifies,
    but it’s not clear what the exact rules are.

    Even though this exception class is registered for `EISDIR`, `getxattr()` is able to
    read the “where from” value of directories (on an APFS volume, at least). According to
    its manpage, the error code is used if “the attribute in question is only applicable
    to files”, but attempting to read the “where from” value of, say, `/dev/null` results
    in `EPERM`, which indicates that “the named attribute is not permitted for this type
    of object”.

    It’s not clear whether there actually are circumstances under which reading a file
    system object’s “where from” value may fail with `EISDIR`, but the exception is
    nevertheless registered for that eventually, just in case.
    """
    MESSAGE = "That type of file system object doesn’t support the attribute"


@register_for("ERANGE", operations=["getxattr"])
class WhereFromValueLengthMismatch(WhereFromValueReadingError):
    """
    Raised if the buffer passed to `_read_binary_where_from_value()` is too small to hold
    the given file’s “where from” value.

    This should only be possible if another process changes the “where from” value between
    the call to `wherefrom.read._read_binary_where_from_value_length()` and the call to
    `_read_binary_where_from_value()`.
    """
    MESSAGE = "The value may have changed while it was being read"


# MISSING C FUNCTIONALITY ################################################################

class MissingExternalDependencyError(WhereFromException):
    """
    The base class for exceptions that are raised if an external dependency can’t be
    found.
    """


class MissingExternalLibrary(MissingExternalDependencyError):
    """
    Raised if the external C library needed to read files’ “where from” values can’t be
    loaded.
    """
    MESSAGE = "Could not load the external library “{library_name}”"
    library_name: str


class MissingExternalLibraryFunction(MissingExternalDependencyError):
    """
    Raised if loading the external C library needed to read files’ “where from” values
    loads a library that doesn’t include the required function.
    """
    MESSAGE = """
        The external library “{library_name}” doesn’t have a function named
        “{function_name}”
    """
    library_name: str
    function_name: str

"""
Define exception classes for file operations.

Exception classes (other than base classes) have decorators that register the class for
one or more error codes, or for one or more error codes encountered during one or more
specific operations. This allows exceptions to be automatically picked and instantiated
based on an error number, an operation name, and a path. See the documentation of the
`wherefrom.exceptions.registry` module for details.
"""

from pathlib import Path
from typing import ClassVar

from wherefrom.exceptions.base import WhereFromException
from wherefrom.exceptions.registry import register_for


# BASE CLASSES ###########################################################################

class FileError(WhereFromException):
    """
    The base class for exceptions that are related to a single file system object.

    This isn’t restricted to OS-level issues (see `LowLevelFileError`, below, for that).
    The exceptions that can occur while parsing a file’s “where from” value also inherit
    from this class.
    """
    ignore_while_walking: ClassVar[bool] = False
    path: Path


class LowLevelFileError(FileError):
    """
    The base class for exceptions that represent OS-level issues with file system objects.

    `operation_verb` is a short description of the operation that failed, and is used to
    construct the error message. It need not necessarily be a verb, as long as it fits
    in the message structure.

    `file_type` is used in the error message used by some subclasses, so that “The file
    doesn’t exist” can become “The directory doesn’t exist” if the file system object is
    known to be a directory. For operations that aren’t limited to a single type, always
    using the “file” default will do.
    """
    MESSAGE_PREFIX = "Could not {operation_verb} “{path}”"
    error_number: int
    error_name: str
    operation_verb: str = "process"
    file_type: str = "file"


# COMMON ERRORS ##########################################################################

@register_for("ENOENT")
@register_for("ENOTDIR", operations=["stat", "getxattr"])
class MissingFile(LowLevelFileError):
    """
    Raised if a file system object that’s supposed to exist doesn’t, in fact, exist.

    `ENOTDIR` is usually used to indicate that an operation that can only be performed
    on directories (such as `readdir`) has been attempted on a file system object other
    than a directory, but it can also indicate that a component of a file system object’s
    path isn’t a directory (as in “file.txt/impossible.txt”, if “file.txt” is a file).
    Since that implies that the file system object the path points to doesn’t exist, this
    exception is used if an operation that works on non-directories fails with that error.
    """
    MESSAGE = "The {file_type} doesn’t exist"
    ignore_while_walking = True


@register_for("EACCES")
class NoReadPermission(LowLevelFileError):
    """
    Raised if a file system object that’s supposed to be readable (or searchable) isn’t.
    """
    MESSAGE = "You don’t have permission to read the {file_type}"


# BAD FILE STRUCTURES ####################################################################

@register_for("ELOOP")
class TooManySymlinks(LowLevelFileError):
    """
    Raised if too many symbolic links were encountered when resolving a path.

    macOS traverses a maximum of 32 symlinks during path resolution.

    Although the error is named `ELOOP`, it doesn’t necessarily indicate that the symlinks
    form a loop.
    """
    MESSAGE = "There were too many symbolic links to traverse"


@register_for("ENAMETOOLONG")
class OverlongPath(LowLevelFileError):
    """
    Raised if a path violates the system’s length limits.

    macOS limits paths to 1024 bytes and individual path components to 255 bytes.

    It’s most likely not actually be possible for a file that causes this exception to
    exist, so this could perhaps be handled using `MissingFile`, but the error receives
    an exception class of its own just in case such a file can, in fact, exist under some
    circumstances (on a mounted file system with different limits, perhaps).

    (`getxattr()` also uses `ENAMETOOLONG` if the name of the extended file attribute to
    read exceeds 127 characters, but this application uses a single fixed attribute, so
    there should be no chance of misdiagnosing the error code.)
    """
    MESSAGE = """
        The length of the {file_type}’s path or of one of its components exceeds the
        system limits
    """


# ERRORS CAUSED BY CONCURRENT MODIFICATIONS ##############################################

@register_for("ENOTDIR", operations=["readdir"])
class ConcurrentlyReplacedDirectory(LowLevelFileError):
    """
    Raised if a file-system object that should be a directory but isn’t one is encountered
    while walking a directory tree.

    This should only be possible if the object used to be a directory, but either it or
    one if its path components has been replaced by another type of file system object
    between the time it was first encountered and the `readdir()` system call.
    """
    MESSAGE = (
        "Expected a directory, but found another type of file system object, possibly "
        "because the directory was replaced with the new object while the application "
        "was running"
    )


# INTERNAL ERRORS ########################################################################

@register_for("EIO")
class FileIOError(LowLevelFileError):
    """Raised if there was an I/O error while accessing the file system."""
    MESSAGE = "An I/O error occurred"


# UNEXPECTED ERRORS ######################################################################

class UnexpectedFileErrorError(LowLevelFileError):
    """
    The base class for exceptions that are raised if an unexpected error occurs while
    accessing the file system.
    """
    MESSAGE = "An unexpected error ocurred ({error_name})"


@register_for("EBADF", operations=["readdir"])
@register_for("EFAULT", operations=["stat", "getxattr"])
@register_for("EINVAL", operations=["getxattr"])
@register_for("EOVERFLOW", operations=["stat"])
class SupposedlyImpossibleFileError(UnexpectedFileErrorError):
    """
    Raised if a file operation fails with an error code that is documented but wasn’t
    thought to be possible in the specific circumstances under which the file operation
    is performed.
    """
    # `getxattr()` uses `EFAULT` to indicates that the path or attribute name points to
    # an invalid memory address. That would indicate a bug in `ctypes`.
    #
    # It uses `EINVAL` to indicate that the given attribute name is invalid, or that
    # an unsupported option has been specified. That shouldn’t be possible, since the
    # application only uses a single attribute name, and doesn’t use any options.
    #
    # Similarly, a `EFAULT` or `EOVERFLOW` from `stat()` or a `EBADF` from `readdir()`
    # would indicate a bug in the Python standard library.


@register_for("UNEXPECTED")
class UnexpectedFileError(UnexpectedFileErrorError):
    """Raised if a file operation fails with an unexpected but known error number."""


@register_for("UNKNOWN")
class UnknownFileError(UnexpectedFileErrorError):
    """
    Raised if a file operation fails with an error number that cannot be mapped to an
    error name.
    """
    MESSAGE = "An unknown error ocurred ({error_number})"

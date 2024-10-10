"""
Define the exceptions raised by `wherefrom.read`.
"""

from wherefrom.exceptions import WhereFromException, WhereFromValueError


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


# GETXATTR() ERRORS › BASE CLASS #########################################################

class WhereFromValueReadingError(WhereFromValueError):
    """
    The base class for exceptions that are raised if an error occurs while reading a
    file’s binary “where from” value.
    """
    MESSAGE_PREFIX = "Could not read the “were from” value of “{path}”"
    error_code: int
    error_name: str


# GETXATTR() ERRORS › NORMAL ERRORS ######################################################

class NoWhereFromValue(WhereFromValueReadingError, KeyError):
    """
    Raised when reading the “where from” value of a file that doesn’t have one.
    The corresponding `getxattr()` error name is `ENOATTR`.
    """
    MESSAGE = "The file doesn’t have the value set"


class MissingFile(WhereFromValueReadingError, FileNotFoundError):
    """
    Raised when reading the “where from” value of a file that doesn’t exist.
    The corresponding `getxattr()` error names are `ENOENT` and `ENOTDIR`.
    """
    MESSAGE = "The file doesn’t exist"


class NoReadPermission(WhereFromValueReadingError, PermissionError):
    """
    Raised when reading the “where from” value of a file that can’t be read.
    The corresponding `getxattr()` error name is `EACCES`.
    """
    MESSAGE = "You don’t have permission to access the file"


# GETXATTR() ERRORS › BAD FILE STRUCTURES ################################################

class TooManySymlinks(WhereFromValueReadingError):
    """
    Raised if more than 32 symlinks were encountered while reading a file’s “where from”
    value. This may or may not be due to a loop.

    The corresponding `getxattr()` error name is `ELOOP`.
    """
    MESSAGE = "Had to traverse too many symbolic links"


class UnsupportedPath(WhereFromValueReadingError):
    """
    Raised when reading the “where from” value of a file whose path exceeds the system’s
    length limits.

    macOS limits paths to 1024 bytes and individual path components to 255 bytes.

    It’s most likely not actually be possible for a file that causes this exception to
    exist, so this could perhaps be handled using `MissingFile`, but the error receives
    an exception class of its own just in case such a file can, in fact, exist under some
    circumstances (on a mounted file system with different limits, perhaps).

    The corresponding `getxattr()` error name is `ENAMETOOLONG`.

    (`getxattr()` uses the same error code if the name of the extended file attribute to
    read exceeds 127 characters, but this application uses a single fixed attribute, so
    there should be no chance of misdiagnosing the error code.)
    """
    MESSAGE = """
        The length of the file’s path or of one of its components exceeds the system
        limits
    """


# GETXATTR() ERRORS › LACK OF SUPPORT ####################################################

class UnsupportedFileSystem(WhereFromValueReadingError):
    """
    Raised when reading the “where from” value of a file on a file system that doesn’t
    support extended file attributes.

    This hasn’t, so far, been tested on an actual file. Experiments involving FAT and
    ExFAT disk images created by macOS and the internal memory of an ancient digital
    camera found that all support extended file attributes.

    The corresponding `getxattr()` error name is `ENOTSUP`.
    """
    MESSAGE = "The file system doesn’t support extended file attributes"


class UnsupportedFileSystemObject(WhereFromValueReadingError):
    """
    Raised when reading the “where from” value of a file system object that doesn’t
    support the attribute (or extended attributes in general). `/dev/null` qualifies,
    but it’s not clear what the exact rules are.

    The corresponding `getxattr()` error names are `EPERM` and `EISDIR`. (Directories
    *do* support the attribute, however, notwithstanding the second error name.)
    """
    MESSAGE = "That type of file system object doesn’t support the attribute"


# GETXATTR() ERRORS › INTERNAL ERRORS ####################################################

class WhereFromValueLengthMismatch(WhereFromValueReadingError):
    """
    Raised if the buffer passed to `_read_binary_where_from_value()` is too small to hold
    the given file’s “where from” value. A different process may have changed the “where
    from” value in the time between the call to `_read_binary_where_from_value_length()`
    and the call to `_read_binary_where_from_value()`.

    The corresponding `getxattr()` error name is `ERANGE`.
    """
    MESSAGE = "The value may have changed while it was being read"


class IOErrorReadingWhereFromValue(WhereFromValueReadingError, IOError):
    """
    Raised if `getxattr()` encountered an I/O error while reading a file’s “where from”
    value. The corresponding `getxattr()` error name is `EIO`.
    """
    MESSAGE = "An I/O error occurred"


# GETXATTR() ERRORS › UNEXPECTED ERROR ###################################################

class UnexpectedErrorReadingWhereFromValue(WhereFromValueReadingError):
    """
    Raised if an unexpected error occurs while reading a file’s “where from” value.

    The class itself is raised for errors that are documented on `getxattr()`’s manpage,
    but are thought to be impossible given the way the application uses the function.
    If `getxattr()` signals an error that isn’t documented on the manpage, the subclass
    `UnknownErrorReadingWhereFromValue` is raised, instead.
    """
    MESSAGE = "An unexpected error ocurred ({error_name})"


class UnknownErrorReadingWhereFromValue(UnexpectedErrorReadingWhereFromValue):
    """
    Raised if an error with an error code that isn’t documented on `getxattr()`’s manpage
    occurs while reading a file’s “where from” value.
    """
    MESSAGE = "An unknown error ocurred (error code {error_code})"

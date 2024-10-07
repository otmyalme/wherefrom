"""
Define the exceptions raised by `wherefrom.read`.
"""

from wherefrom.exceptions import WhereFromException, WhereFromValueError


# MISSING C FUNCTIONALITY ################################################################

class MissingExternalDependencyError(WhereFromException):
    """
    The base class for exceptions that are raised if an external dependency is missing.
    """


class MissingExternalLibrary(MissingExternalDependencyError):
    """
    Raised if the external C library needed to read the “where from” value can’t be found.
    """
    MESSAGE = "Could not load the external library “{library_name}”"
    library_name: str


class MissingExternalLibraryFunction(MissingExternalDependencyError):
    """
    Raised if the external C library doesn’t have the function required to read “where
    from” values.
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
    file’s binary “where from” value. In case of an unexpected error, the class itself
    is raised.
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
    Raised when reading the “where from” value of a file that does not exist.
    The corresponding `getxattr()` error names are `ENOENT` and `ENOTDIR`.
    """
    MESSAGE = "The file doesn’t exist"


class NoReadPermission(WhereFromValueReadingError, PermissionError):
    """
    Raised when reading the “where from” value of a file that cannot be read.
    The corresponding `getxattr()` error name is `EACCES`.
    """
    MESSAGE = "You don’t have permission to access the file"


# GETXATTR() ERRORS › BAD FILE STRUCTURES ################################################

class TooManySymlinks(WhereFromValueReadingError):
    """
    Raised if more than 32 symlinks were encountered while reading the “where from” value.
    This may or may not be due to a loop.

    The corresponding `getxattr()` error name is `ELOOP`.
    """
    MESSAGE = "Had to traverse too many symbolic links"


class UnsupportedPath(WhereFromValueReadingError):
    """
    Raised when reading the “where from” value of a file whose name or path is too long.

    macOS limits file names to 255 bytes and paths to 1024 bytes, and this exception is
    raised when a file’s name or path exceeds these limits.

    It might not actually be possible for such a file to exist, so this could perhaps just
    be handled using `MissingFile`, but the error receives a exception class of its own in
    case it is in fact possible for such a file to exist under some circumstances (on a
    mounted file system with different limits, maybe).

    The corresponding `getxattr()` error name is `ENAMETOOLONG`.

    (`getxattr()` uses the same error code if the name of the extended file attribute to
    read exceeds 127 characters, but this application uses a single fixed attribute, so
    there should be no chance of misdiagnosing the error code.)
    """
    MESSAGE = """
        The length of the file’s name or that of it’s path exceeds the system limits
    """


# GETXATTR() ERRORS › LACK OF SUPPORT ####################################################

class UnsupportedFileSystem(WhereFromValueReadingError):
    """
    Raised if the file system doesn’t support extended file attributes.

    This hasn’t, so far, been tested on an actual file. Experiments involving FAT and
    ExFAT disk images created by macOS and the internal memory of an ancient digital
    camera found that all support extended file attributes.

    The corresponding `getxattr()` error name is `ENOTSUP`.
    """
    MESSAGE = "The file system doesn’t support extended file attributes"


class UnsupportedFileSystemObject(WhereFromValueReadingError):
    """
    Raised when reading the “where from” attribute of a file system object that doesn’t
    support the attribute (or extended attributes in general). `/dev/null` qualifies, but
    it’s not clear what the exact rules are.

    The corresponding `getxattr()` error names are `EPERM` and `EISDIR`.
    """
    MESSAGE = "That type of file system object doesn’t support the “where from” attribute"


# GETXATTR() ERRORS › INTERNAL ERRORS ####################################################

class WhereFromValueLengthMismatch(WhereFromValueReadingError):
    """
    Raised if the buffer passed to `_read_where_from_value()` is too small to hold the
    “where from” value. A different process may have changed the file’s “where from”
    value in the time between the call to `_read_where_from_value_length()` and the call
    to `_read_where_from_value_length()`, or there may be a bug in this application, or
    maybe even in `getxattr()`.

    The corresponding `getxattr()` error name is `ERANGE`.
    """
    MESSAGE = """
        Either the value has changed while it was being read, or there has been an
        unexpected internal error
    """


class IOErrorReadingWhereFromValue(WhereFromValueReadingError, IOError):
    """
    Raised if `getxattr()` encountered an I/O error while reading a file’s “where from”
    value. The corresponding `getxattr()` error name is `EIO`.
    """
    MESSAGE = "An I/O error occurred"


# GETXATTR() ERRORS › UNEXPECTED ERROR ###################################################

class UnexpectedErrorReadingWhereFromValue(WhereFromValueReadingError):
    """
    Raised if an error that shouldn’t be possible occurs while reading the “where from”
    value.
    """
    MESSAGE = "An unexpected error ocurred ({error_name})"


class UnknownErrorReadingWhereFromValue(UnexpectedErrorReadingWhereFromValue):
    """
    Raised if an error with an error code that isn’t documented on `getxattr()`’s manpage
    occurs while reading the “where from” value.
    """
    MESSAGE = "An unknown error ocurred (error code {error_code})"

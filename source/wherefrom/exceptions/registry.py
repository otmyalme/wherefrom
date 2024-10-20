"""
Create exceptions for failed system calls.

A subclass of `LowLevelFileError` can be registered for a given error code by decorating
it with `register_for()`. Then, calling `get_exception_by_error_code()` with that error
code (or `get_exception_from_os_error()` with an `OSError` with that error code) returns
an instance of that exception class.

Error codes alone might not provide sufficient context to decide what exactly went wrong,
however: `getxattr()` signals `EPERM` to indicate that a given file system object doesn’t
support extended file attributes, for example, but it may be unwise to assume that’s the
issue without checking whether the error did, in fact, come from `getxattr()`, even if
the application doesn’t use any other system calls that document signalling `EPERM`.

To provide the necessary context, the `get_exception_*()` functions require the caller to
specify an “operation” – generally the name of the system call that signalled the error.

Exceptions can be registered for a specific list of operations or for all operations that
don’t have a more specific exception registered for them, and the `get_exception_*()`
functions pick the appropriate exception class for operation they were called with.

Also, modules that use this module’s functionality can call `register_operation()` to
associate a description for a given operation, which will then be used in the exception
message, so that it can, for example, specifically explain that the application “Couldn’t
collect the contents of” a given directory. See that functions docstring for details.
"""

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from wherefrom.tools import as_path_object
from wherefrom.exceptions.base import WhereFromException

if TYPE_CHECKING:
    from wherefrom.exceptions.file import LowLevelFileError


# TYPES ##################################################################################

# Some type definitions, for readability.
type LowLevelFileErrorSubclass = type["LowLevelFileError"]
type LowLevelFileErrorSubclassDecorator = Callable[
    [LowLevelFileErrorSubclass], LowLevelFileErrorSubclass,
]


# LOOKUP #################################################################################

def get_exception_by_error_code(
    error_code: int,
    operation: str,
    path: Path | str | bytes,
    file_type: str = "file",
) -> "LowLevelFileError":
    """
    Get an appropriate `LowLevelFileError` instance for the given error code.

    Note that the exception is *returned*, not raised.

    `operation` indicates what the application was doing when the error occurred. This is
    required because different exception classes may be registered for a given error code
    for different operations. It is also used to construct the returned exception’s error
    message; see `register_operation()` for details.

    `file_type` is used in the error message used by some `LowLevelFileError` subclasses,
    so that “The file doesn’t exist” can become “The directory doesn’t exist” if the file
    system object is known to be a directory. For operations that aren’t limited to a
    single type of file system object, always using the “file” default will do.
    """
    path = as_path_object(path)
    error_name = _ERROR_NAMES.get(error_code, UNKNOWN_ERROR_NAME)
    exception_class = (
           _EXCEPTION_CLASSES.get((error_code, operation))
        or _EXCEPTION_CLASSES.get((error_code, ALL_OPERATIONS))
        or _EXCEPTION_CLASSES[UNKNOWN_ERROR_CODE, ALL_OPERATIONS]
    )
    operation_verb = _OPERATION_VERBS.get(operation, DEFAULT_OPERATION_VERB)
    return exception_class(path, error_code, error_name, operation_verb, file_type)


def get_exception_from_os_error(
    cause: OSError,
    operation: str,
    file_type: str = "file",
) -> "LowLevelFileError":
    """
    Get an appropriate `LowLevelFileError` instance for the given `OSError`.

    This functions like `get_exception_by_error_code()`, but the error code and path are
    taken from the given `OSError`.
    """
    path = cause.filename or "UNKNOWN"
    return get_exception_by_error_code(cause.errno, operation, path, file_type)


# REGISTRATION ###########################################################################

def register_operation(operation_name: str, verb: str) -> None:
    """
    Register a descriptive verb for an operation.

    By default, the exceptions returned by `get_exception_by_error_code()` have an error
    message that starts with “Could not process”, followed by the path. The message would
    be clearer if the word “process” would be replaced with a more specific description;
    “collect the contents of” for errors during a `readdir` system call, for example.

    To that end, this function can be called to register such a description for a given
    operation; calling `register_operation("readdir", "collect the contents of")` would
    ensure that that description is used for all exceptions that specify the operation
    "readdir".

    It is an error to register a description if a different description has already been
    registered, but registering the same description multiple times is allowed.
    """
    _check_no_operation_verb_registered(operation_name, verb)
    _OPERATION_VERBS[operation_name] = verb


# The operation name used to register an exception or operation description for all
# operations that don’t have a more specific exception or description registered.
ALL_OPERATIONS = "ALL"


def register_for(
    error_code: int,
    error_name: str,
    operations: str | list[str] = ALL_OPERATIONS,
) -> LowLevelFileErrorSubclassDecorator:
    """
    Decorate a subclass of `LowLevelFileError` to indicate an error code it handles.

    That is, if such an exception class is decorated with `@register_for(2, "ENOENT")`,
    `get_exception_by_error_code()` will return an instance of that exception class if
    it is called with the error code 2.

    If `operations` is set to a string or list of strings, the decorated exception class
    is only used if `get_exception_by_error_code()` is called with those operations.

    Different exception classes can be registered for a given error code if at most one
    such class doesn’t specify any operations and all other such classes specify lists of
    error codes that do not overlap. In that case, the class that was registered without
    an operation is only used for operations that was not used to register another class.

    The error name must be consistent for each registration for a given error code.
    """
    operations = [operations] if isinstance(operations, str) else operations

    def decorator(cls: LowLevelFileErrorSubclass) -> LowLevelFileErrorSubclass:
        for operation in operations:
            _check_no_error_name_registered(error_code, error_name)
            _check_no_exception_class_registered(error_code, operation, cls)
            _ERROR_NAMES[error_code] = error_name
            _EXCEPTION_CLASSES[error_code, operation] = cls
        return cls

    return decorator


def register_as_default(
    operations: str | list[str] = ALL_OPERATIONS,
) -> LowLevelFileErrorSubclassDecorator:
    """
    Decorate a subclass of `LowLevelFileError` to indicate that it handles unknown errors.
    """
    return register_for(UNKNOWN_ERROR_CODE, UNKNOWN_ERROR_NAME, operations)


# EXCEPTION CLASSES ######################################################################

class ExistingRegistration(WhereFromException):
    """
    The base class for exceptions that are raised when conflicting error information
    is registered.
    """


class ExistingOperationRegistration(ExistingRegistration):
    """Raised if two different descriptions are registered for an operation."""

    MESSAGE = """
        Cannot register the verb “{proposed_verb}” for the operation “{operation}”:
        The verb “{existing_verb}” has already been registered for that operation
    """
    operation: str
    proposed_verb: str
    existing_verb: str


class ExistingErrorNameRegistration(ExistingRegistration):
    """Raised if two different names are registered for an error code."""

    MESSAGE = """
        Cannot register the name “{proposed_error_name}” for the error code {error_code}:
        The name “{existing_error_name}” has already been registered for that code
    """
    error_code: int
    proposed_error_name: str
    existing_error_name: str


class ExistingExceptionClassRegistration(ExistingRegistration):
    """Raised if two exceptions are registered for one error code and operation."""

    MESSAGE = """
        Cannot register the exception class “{proposed_exception_class.__name__}”
        for the error code {error_code} and the operation “{operation}”: The class
        “{existing_exception_class.__name__}” has already been registered for that code
        and operation
    """
    error_code: int
    operation: str
    proposed_exception_class: LowLevelFileErrorSubclass
    existing_exception_class: LowLevelFileErrorSubclass


# SPECIAL VALUES #########################################################################

# The error name used used for unknown error codes.
UNKNOWN_ERROR_NAME = "UNKNOWN"

# A dummy error code that’s used to store the exception classes registered for unknown
# errors. (The actual error code is used when creating instances of the exception class.)
UNKNOWN_ERROR_CODE = -int.from_bytes(UNKNOWN_ERROR_NAME.encode("ascii"))

# The operation description that is used if no other description has been registered.
DEFAULT_OPERATION_VERB = "process"


# REGISTRIES #############################################################################

# Maps error codes to the corresponding error names.
_ERROR_NAMES: dict[int, str] = {}

# Maps tuples of error codes and operation names to the matching `LowLevelFileError`
# subclass. The error code `UNKNOWN_ERROR_CODE` is used for exceptions that handle
# unknown errors.
_EXCEPTION_CLASSES: dict[tuple[int, str], LowLevelFileErrorSubclass] = {}

# Maps operation names to a descriptive verb for that operation.
_OPERATION_VERBS: dict[str, str] = {}


# UTILITY FUNCTIONS ######################################################################

def _check_no_operation_verb_registered(operation_name: str, proposed_verb: str) -> None:
    """Raise an exception if there’s already a different verb for the given operation."""
    existing_verb = _OPERATION_VERBS.get(operation_name)
    if existing_verb and existing_verb != proposed_verb:
        raise ExistingOperationRegistration(operation_name, proposed_verb, existing_verb)


def _check_no_error_name_registered(error_code: int, proposed_name: str) -> None:
    """Raise an exception if there’s already a different name for the given error code."""
    existing_name = _ERROR_NAMES.get(error_code)
    if existing_name and existing_name != proposed_name:
        raise ExistingErrorNameRegistration(error_code, proposed_name, existing_name)


def _check_no_exception_class_registered(
    error_code: int,
    operation: str,
    proposed_class: LowLevelFileErrorSubclass,
) -> None:
    """
    Raise an exception if there’s already an exception class for the given error code and
    operation.
    """
    key = (error_code, operation)
    if existing_class := _EXCEPTION_CLASSES.get(key):
        raise ExistingExceptionClassRegistration(*key, proposed_class, existing_class)

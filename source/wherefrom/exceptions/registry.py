"""
Create exceptions for failed system calls.

System calls signal errors using error codes, which have a name (such as `EIO` for I/O
errors) and a number (5, in the case of `EIO`). This module provides functionality for
mapping these codes to exception classes.

A subclass of `LowLevelFileError` can be registered for a given error code by decorating
it with `register_for()`, which takes the error code’s name as an argument. Then, calling
`get_exception_by_error_number()` with the matching error number returns an instance of
that exception class.

Error codes alone might not provide sufficient context to decide what exactly went wrong,
however: `getxattr()` signals `EPERM` to indicate that a given file system object doesn’t
support extended file attributes, for example, but it may be unwise to assume that’s the
issue without checking whether the error did, in fact, come from `getxattr()`, even though
this application doesn’t use any other system calls that document signalling `EPERM`.

To provide the necessary context, `get_exception_by_error_number()` requires the caller to
specify an “operation” – generally the name of the system call that signalled the error.

Exceptions can be registered for a specific list of operations, or for all operations that
don’t have a more specific exception registered, and the `get_exception_by_error_number()`
function picks the appropriate exception class for operation they were called with.

Also, modules that use this module’s functionality can call `register_operation()` to
associate a description for a given operation, which will then be used in the exception
message, so that it can, for example, specifically explain that the application “Couldn’t
collect the contents of” a given directory. See that functions docstring for details.

To handle unexpected errors, exception classes can be registered for the dummy error names
`UNEXPECTED` and `UNKNOWN`. See the documentation of `register_for()` for details.
"""

from collections.abc import Callable
import errno
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

def get_exception_by_error_number(
    error_number: int,
    operation: str,
    path: Path | str | bytes,
    file_type: str = "file",
) -> "LowLevelFileError":
    """
    Get an appropriate `LowLevelFileError` instance for the given error number.

    Note that the exception is *returned*, not raised.

    `operation` indicates what the application was doing when the error occurred. This is
    required because different exception classes may be registered for a given error code
    for different operations. The argument’s value is also used to construct the returned
    exception’s error message; see `register_operation()` for details.

    `file_type` is used in the error message used by some `LowLevelFileError` subclasses,
    so that “The file doesn’t exist” can become “The directory doesn’t exist” if the file
    system object is known to be a directory. For operations that aren’t limited to a
    single type of file system object, always using the “file” default will do.
    """
    path = as_path_object(path)
    error_name = errno.errorcode.get(error_number, UNKNOWN_ERROR_NAME)
    exception_class = (
           _EXCEPTION_CLASSES.get((error_name, operation))
        or _EXCEPTION_CLASSES.get((error_name, ALL_OPERATIONS))
        or _EXCEPTION_CLASSES.get((UNEXPECTED_ERROR_NAME, operation))
        or _EXCEPTION_CLASSES[UNEXPECTED_ERROR_NAME, ALL_OPERATIONS]
    )
    operation_verb = _OPERATION_VERBS.get(operation, DEFAULT_OPERATION_VERB)
    return exception_class(path, error_number, error_name, operation_verb, file_type)


def get_exception_from_os_error(
    cause: OSError,
    operation: str,
    file_type: str = "file",
) -> "LowLevelFileError":
    """
    Get an appropriate `LowLevelFileError` instance for the given `OSError`.

    This functions like `get_exception_by_error_number()`, but the error number and path
    are taken from the given `OSError`.
    """
    path = cause.filename or UNKNOWN_ERROR_NAME
    return get_exception_by_error_number(cause.errno, operation, path, file_type)


# SPECIAL VALUES #########################################################################

# The operation name used to register an exception or operation description for all
# operations that don’t have a more specific exception or description registered.
ALL_OPERATIONS = "ALL"

# A dummy error name used to register exception classes for used for error codes that have
# a known name, but don’t have a exception class registered for that name. The exceptions
# themselves use the error code’s name, not this value.
UNEXPECTED_ERROR_NAME = "UNEXPECTED"

# A dummy error name used to register exception classes that are used for error codes that
# don’t have a known name. It’s also used as the error name when creating exceptions for
# these error codes.
UNKNOWN_ERROR_NAME = "UNKNOWN"

# The operation description that is used if no other description has been registered.
DEFAULT_OPERATION_VERB = "process"


# REGISTRATION ###########################################################################

def register_operation(operation_name: str, verb: str) -> None:
    """
    Register a descriptive verb for an operation.

    By default, the exceptions returned by `get_exception_by_error_number()` have an error
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


def register_for(
    error_name: str,
    operations: str | list[str] = ALL_OPERATIONS,
) -> LowLevelFileErrorSubclassDecorator:
    """
    Register the decorated subclass of `LowLevelFileError` for the given error code.

    If a suitable exception class is decorated with, say, `@register_for("EOVERFLOW")`,
    calling `get_exception_by_error_number()` with the error number for `EOVERFLOW`, 84,
    returns an instance of that exception class.

    If a list of operations is specified in the decorator, the exception is only used if
    `get_exception_by_error_number()` is called with one of the listed operation names.
    The default value, `"ALL"`, indicates that the decorated class should be used for any
    operations that don’t have an exception class registered for them specifically.

    (That is, of class A is decorated with `@register_for("EOVERFLOW")` and class B is
    decorated with `@register_for("EOVERFLOW", operations=["stat"])`, class B will be used
    if `get_exception_by_error_number()` is called with the operation `"stat"`, and class
    A will be used if it’s called with any other operation.)

    Instead of a regular error name, the special values `"UNEXPECTED"` and `"UNKNOWN"` can
    be used. `"UNEXPECTED"` indicates that the decorated exception class should be used as
    a fallback if no other exception class matches a given error number and operation, and
    `"UNKNOWN"` indicates that the decorated exception class should be used if a given
    error number cannot be mapped to an error name.

    For both special values, operations can be specified in the same way as for regular
    error names.

    If another exception class has already been registered for a given error code and
    operation, the function raises `ExistingExceptionClassRegistration`.
    """
    operations = [operations] if isinstance(operations, str) else operations

    def decorator(cls: LowLevelFileErrorSubclass) -> LowLevelFileErrorSubclass:
        for operation in operations:
            _check_no_exception_class_registered(error_name, operation, cls)
            _EXCEPTION_CLASSES[error_name, operation] = cls
        return cls

    return decorator


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


class ExistingExceptionClassRegistration(ExistingRegistration):
    """Raised if two exceptions are registered for one error code and operation."""

    MESSAGE = """
        Cannot register the exception class “{proposed_exception_class.__name__}”
        for the error name “{error_name}” and the operation “{operation}”: The class
        “{existing_exception_class.__name__}” has already been registered for that name
        and operation
    """
    error_name: str
    operation: str
    proposed_exception_class: LowLevelFileErrorSubclass
    existing_exception_class: LowLevelFileErrorSubclass


# REGISTRIES #############################################################################

# Maps tuples of error names and operation names to the matching `LowLevelFileError`
# subclass. The error names `UNEXPECTED` and `UNKNOWN` are used for exceptions that
# handle unexpected and unknown errors, respectively
_EXCEPTION_CLASSES: dict[tuple[str, str], LowLevelFileErrorSubclass] = {}

# Maps operation names to a descriptive verb for that operation.
_OPERATION_VERBS: dict[str, str] = {}


# UTILITY FUNCTIONS ######################################################################

def _check_no_operation_verb_registered(operation_name: str, proposed_verb: str) -> None:
    """Raise an exception if there’s already a different verb for the given operation."""
    existing_verb = _OPERATION_VERBS.get(operation_name)
    if existing_verb and existing_verb != proposed_verb:
        raise ExistingOperationRegistration(operation_name, proposed_verb, existing_verb)


def _check_no_exception_class_registered(
    error_name: str,
    operation: str,
    proposed_class: LowLevelFileErrorSubclass,
) -> None:
    """
    Raise an exception if there’s already an exception class for the given error code and
    operation.
    """
    if existing_class := _EXCEPTION_CLASSES.get((error_name, operation)):
        raise ExistingExceptionClassRegistration(
            error_name, operation, proposed_class, existing_class,
        )

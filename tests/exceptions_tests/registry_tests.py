"""
Test the `wherefrom.exceptions.registry` module.
"""

from pathlib import Path
import pytest

from wherefrom.exceptions.file import MissingFile, NoReadPermission, OverlongPath

import wherefrom.exceptions.registry as module
from wherefrom.exceptions.registry import (
    register_for, register_operation, get_exception_by_error_number, ALL_OPERATIONS,
)


# FIXTURES ###############################################################################

@pytest.fixture
def without_registrations(monkeypatch):
    """Temporarily replace the dicts used to store registrations with empty ones."""
    monkeypatch.setattr(module, "_EXCEPTION_CLASSES", {})
    monkeypatch.setattr(module, "_OPERATION_VERBS", {})


# TESTS ##################################################################################

def test_registry__simple(without_registrations):
    """Does registering exception classes and creating exceptions work?"""
    register_operation("ret", "reticulate")
    register_for("ENOENT")(MissingFile)
    path = "/Users/someone/somewhere/no-such-directory"
    exception = get_exception_by_error_number(2, "ret", path, "directory")
    assert isinstance(exception, MissingFile)
    assert exception.path == Path(path)
    assert exception.error_number == 2
    assert exception.error_name == "ENOENT"
    assert exception.operation_verb == "reticulate"
    assert exception.file_type == "directory"
    assert str(exception) == f"Could not reticulate “{path}”: The directory doesn’t exist"


def test_registry__multiple_operations(without_registrations):
    """Can one error code have different exceptions classes for different operations?"""
    register_for("ENOENT", operations="a")(MissingFile)
    register_for("ENOENT")(OverlongPath)
    register_for("ENOENT", operations=["b", "c"])(NoReadPermission)
    path = "/Users/someone/somewhere/something"
    assert isinstance(get_exception_by_error_number(2, "a", path), MissingFile)
    assert isinstance(get_exception_by_error_number(2, "b", path), NoReadPermission)
    assert isinstance(get_exception_by_error_number(2, "c", path), NoReadPermission)
    assert isinstance(get_exception_by_error_number(2, "x", path), OverlongPath)


def test_register_operation__existing_verb(without_registrations):
    """Is an exception raised if more than one verb is registered for an operation?"""
    register_operation("ret", "reticulate")
    with pytest.raises(module.ExistingOperationRegistration) as exception_information:
        register_operation("ret", "reticulate the spline at")
    assert module._OPERATION_VERBS["ret"] == "reticulate"
    exception = exception_information.value
    assert exception.operation == "ret"
    assert exception.proposed_verb == "reticulate the spline at"
    assert exception.existing_verb == "reticulate"
    assert str(exception) == (
        "Cannot register the verb “reticulate the spline at” for the operation “ret”: "
        "The verb “reticulate” has already been registered for that operation"
    )


def test_register_for__existing_exception_class(without_registrations):
    """Is an exception raised if more than one class is registered for an error code?"""
    register_for("ENOENT")(MissingFile)
    expected_exception = module.ExistingExceptionClassRegistration
    with pytest.raises(expected_exception) as exception_information:
        register_for("ENOENT")(NoReadPermission)
    assert module._EXCEPTION_CLASSES["ENOENT", ALL_OPERATIONS] is MissingFile
    exception = exception_information.value
    assert exception.error_name == "ENOENT"
    assert exception.operation == ALL_OPERATIONS
    assert exception.existing_exception_class is MissingFile
    assert exception.proposed_exception_class is NoReadPermission
    assert str(exception) == (
        "Cannot register the exception class “NoReadPermission” for the error name "
        "“ENOENT” and the operation “ALL”: The class “MissingFile” has already been "
        "registered for that name and operation"
    )

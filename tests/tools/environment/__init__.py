"""
Create a set of files with interesting “where from” values, for use by the test suite.

This package provides the `create_test_environment()` and `delete_test_environment()`
functions, which are used by the `environment` fixture in `tests.conftest`. See its
docstring for details.

The functions makes every effort to ensure they don’t overwrite or delete any important
files; files that are written to are opened for exclusive creation, and files are only
deleted if they are either empty, or are PNG files consisting of a single white pixel.
The logic used to implement these safeguards is subject to race conditions, however.

(Note that Git doesn’t store files’ extended attributes, so it wouldn’t be possible to
just manually create the files once and keep them in the repository.)
"""

from tests.tools.environment.structure import (
    create_test_environment, delete_test_environment,
)

__all__ = ["create_test_environment", "delete_test_environment"]
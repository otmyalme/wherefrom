"""
Provide test fixtures for use by the test suite.
"""

from pathlib import Path

import pytest

from tests.environment import create_test_environment, delete_test_environment
from tests.tools import get_developer_visible_temporary_directory


ENVIRONMENT_DIRECTORY_NAME = "test-environment"


@pytest.fixture(scope="session")
def environment() -> Path:
    """
    Create a set of files with interesting “where from” values and return their base path.

    Files are only created once per test session; since the files aren’t modified by the
    tests, that should be safe.

    Also, rather than being created somewhere in `$TMPDIR`; the files are created in
    the application’s main directory, in `temporary/test-environment`, and they aren’t
    deleted at the end of the test session. This may be useful if the developer needs
    to manually inspect the files’ “where from” attributes using Finder or `xattr`.

    The files are deleted and recreated at the start of each new test session, however,
    to ensure that they reflect any changes made to `create_test_environment()`.

    The `tests.environment` module ensures that creating and deleting the test environment
    is as safe as it can be; see that module’s documentation for details.
    """
    path = get_developer_visible_temporary_directory() / ENVIRONMENT_DIRECTORY_NAME
    delete_test_environment(path)
    create_test_environment(path)
    return path

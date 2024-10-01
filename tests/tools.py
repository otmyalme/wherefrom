"""
Provide assorted utility functions that are useful for the test suite.
"""

from pathlib import Path


TESTS_DIRECTORY_NAME = "tests"
TEMPORARY_DIRECTORY_NAME = "temporary"


def get_developer_visible_temporary_directory() -> Path:
    """
    Get the path to a temporary directory in the application’s `tests` directory. Create
    it, if necessary. See the docstring of `tests.environment` as to why this is useful.
    """
    tests_path = Path(__file__).parent
    assert tests_path.name == TESTS_DIRECTORY_NAME
    temporary_path = tests_path / TEMPORARY_DIRECTORY_NAME
    temporary_path.mkdir(exist_ok=True)
    return temporary_path

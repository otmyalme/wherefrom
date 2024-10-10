"""
Provide assorted utility functions that are useful for the test suite.
"""

from enum import Enum
from pathlib import Path


MAIN_DIRECTORY_NAME = "wherefrom"
TEMPORARY_DIRECTORY_NAME = "temporary"


def get_developer_visible_temporary_directory() -> Path:
    """
    Get the path to a temporary directory in the application’s main directory. Create it,
    if necessary. See the docstring of the `environment` fixture as to why this is useful.
    """
    tests_path = Path(__file__).parent.parent.parent
    assert tests_path.name == MAIN_DIRECTORY_NAME
    temporary_path = tests_path / TEMPORARY_DIRECTORY_NAME
    temporary_path.mkdir(exist_ok=True)
    return temporary_path


# A collection of sentinel values for use in cases where it is necessary to signal the
# absence of a real value, but None isn’t suitable for the purpose because it is possible
# to use it as a real value. The values are implemented as enums items because those are
# allowed in a `Literal` annotation.
Sentinel = Enum("Sentinel", "NO_VALUE")

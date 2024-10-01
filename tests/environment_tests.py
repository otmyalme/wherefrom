"""
Test `tests.tools.environment`.

(The parts that aren’t implicitly tested by the actual tests, at least.)
"""

from pathlib import Path

import pytest

from tests.environment import create_test_environment, delete_test_environment
from tests.tools import get_developer_visible_temporary_directory


def test_create_and_delete_test_environment():
    """Are test environments properly created and deleted?"""
    path = get_developer_visible_temporary_directory() / "test-test-environment"
    create_test_environment(path)
    assert path.exists()
    delete_test_environment(path)
    assert not path.exists()


def test_delete_test_environment__does_not_exist():
    """Does deleting a test environment that doesn’t exist do nothing without an error?"""
    path = get_developer_visible_temporary_directory() / "no-such-test-environment"
    assert not path.exists()
    delete_test_environment(path)


def test_delete_test_environment__unexpected_file():
    """Does the function refuse to delete unexpected files?"""
    path = get_developer_visible_temporary_directory() / "unexpected-test-environment"
    create_test_environment(path)
    unexpected_file_path = path / "unexpected.txt"
    unexpected_file_path.write_text("No one expects the unexpected file!")
    with pytest.raises(AssertionError):
        delete_test_environment(path)
    assert unexpected_file_path.exists()
    unexpected_file_path.unlink()
    delete_test_environment(path)
    assert not path.exists()


def test_environment_fixture(environment: Path):
    """Does the `environment` fixture create a test environment?"""
    assert environment.exists()

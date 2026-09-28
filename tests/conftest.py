"""Ensure src/ and sample/ are importable for the whole test session."""
import _data  # noqa: F401  (side effect: sets sys.path, loads sample)
import pytest


@pytest.fixture(scope="session")
def sample():
    return _data.SAMPLE


@pytest.fixture(scope="session")
def stores():
    return _data.STORES


@pytest.fixture(scope="session")
def data():
    return _data.DATA

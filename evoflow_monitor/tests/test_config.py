import os
from utilities.config_utils import from_env
from pathlib import Path
import pytest

TEST_ENV_PATH = Path(__file__).parent.parent / ".env"


@pytest.fixture(scope="module")
def setup_env():
    original_env_path = os.environ.copy()
    with open(TEST_ENV_PATH, "w") as f:
        f.write("TEST_KEY=success\n")
        f.write("EMPTY_KEY=\n")
    yield
    os.remove(TEST_ENV_PATH)
    os.environ = original_env_path


def test_from_env_with_existing_key(setup_env):
    assert from_env("TEST_KEY") == "success"


def test_from_env_with_non_existing_key_returns_default(setup_env):
    default_val = "default"
    assert from_env("NON_EXISTING_KEY", default_val) == default_val


def test_from_env_with_empty_key_returns_empty(setup_env):
    default_val = ""
    assert from_env("EMPTY_KEY") == default_val

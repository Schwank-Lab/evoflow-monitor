import os
from dotenv import load_dotenv
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
ENVFILE_PATH = os.path.join(PROJECT_DIR, ".env")


def from_env(key, default=None):
    """Returns the value for the given key from the environment variables."""
    load_dotenv(ENVFILE_PATH)
    return os.getenv(key, default)

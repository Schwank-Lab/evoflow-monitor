from utilities.config_utils import from_env


class Config:
    """
    Every entry in the .env file is stored as a class attribute.
    """

    DB_HOST = from_env("DB_HOST")
    DB_PORT = from_env("DB_PORT")
    DB_NAME = from_env("DB_NAME")
    DB_USER = from_env("DB_USER")
    DB_PASS = from_env("DB_PASS")

from utilities.config_utils import from_env


class Config:
    """
    Every entry in the .env file is stored as a class attribute.
    """

    DB_IP = from_env("DB_IP")
    DB_PORT = from_env("DB_PORT")
    DB_NAME = from_env("DB_NAME")
    DB_USER = from_env("DB_USER")
    DB_PASS = from_env("DB_PASS")


if __name__ == "__main__":
    print(Config.DB_IP)
    print(Config.DB_PORT)
    print(Config.DB_NAME)
    print(Config.DB_USER)
    print(Config.DB_PASS)

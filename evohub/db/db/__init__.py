import psycopg2
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from evoflow_utils.config import Config


def __connect():
    conn = psycopg2.connect(
        dbname=Config.DB_NAME,
        user=Config.DB_USER,
        password=Config.DB_PASS,
        host=Config.DB_HOST,
        port=Config.DB_PORT,
    )
    return conn


def idec_engine():
    return create_engine(
        "postgresql+psycopg2://",
        creator=__connect,
    )


def session():
    return sessionmaker(bind=idec_engine())

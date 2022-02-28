import os

from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool


POSTGRES_USER = "bulletin"
# TODO Usually retrieve with a query to something like Hashicorp Vault
POSTGRES_PASSWORD = ""
# TODO Dynamically set; this case, use localhost
POSTGRES_ENDPOINT = "localhost"
POSTGRES_DATABASE_SCHEMA = "bulletin_board"


class DatabaseContext(object):
    _engine = None

    def __init__(self):
        raise Exception("Instantiating not allowed")

    @classmethod
    def engine(cls):
        if cls._engine is None:
            environment = os.environ.get("ENV", None)
            if True or environment in ["Staging", "Production"]:
                # TODO
                cls._engine = create_engine(get_endpoint(), poolclass=QueuePool, echo=True)
        return cls._engine


def get_engine():
    engine = DatabaseContext.engine()
    return engine


def get_endpoint():
    endpoint = f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_ENDPOINT}/{POSTGRES_DATABASE_SCHEMA}"
    return endpoint
import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    mongo_uri: str
    mongo_db: str


def load_settings(uri: str | None = None, db: str | None = None) -> Settings:
    load_dotenv()

    mongo_uri = uri or os.getenv("MONGO_URI") or "mongodb://localhost:27017"
    mongo_db = db or os.getenv("MONGO_DB") or "halo2_archive"

    return Settings(mongo_uri=mongo_uri, mongo_db=mongo_db)

from pymongo import MongoClient
from pymongo.database import Database


def get_database(uri: str, db_name: str) -> Database:
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    return client[db_name]

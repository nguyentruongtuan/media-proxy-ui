from functools import lru_cache

from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

from media_proxy_api.config import settings


@lru_cache
def get_client() -> AsyncMongoClient:
    # The client connects lazily, so creating it at import/startup never blocks.
    return AsyncMongoClient(settings.mongo_uri, tz_aware=True)


def get_database() -> AsyncDatabase:
    return get_client()[settings.mongo_db]

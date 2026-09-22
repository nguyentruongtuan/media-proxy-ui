from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Protocol

from bson import ObjectId
from bson.errors import InvalidId
from pydantic import BaseModel, Field
from pymongo import ReturnDocument
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.errors import DuplicateKeyError


class CrawlStatus(StrEnum):
    PENDING = "pending"
    DONE = "done"
    FAILED = "failed"


class CrawlData(BaseModel):
    title: str | None = None
    description: str | None = None
    images: list[str] = Field(default_factory=list)
    stream_urls: list[str] = Field(default_factory=list)
    embed_urls: list[str] = Field(default_factory=list)


class UrlRecord(BaseModel):
    id: str
    url: str
    status: CrawlStatus = CrawlStatus.PENDING
    crawl: CrawlData | None = None
    error: str | None = None
    created_at: datetime
    updated_at: datetime
    crawled_at: datetime | None = None


class DuplicateUrlError(Exception):
    pass


class UrlRepository(Protocol):
    async def create(self, url: str) -> UrlRecord: ...

    async def list(self) -> list[UrlRecord]: ...

    async def get(self, url_id: str) -> UrlRecord | None: ...

    async def update_url(self, url_id: str, url: str) -> UrlRecord | None:
        """Change the URL and reset any crawl result, since it described the old URL."""
        ...

    async def save_crawl(self, url_id: str, crawl: CrawlData) -> UrlRecord | None: ...

    async def save_crawl_error(self, url_id: str, error: str) -> UrlRecord | None: ...

    async def delete(self, url_id: str) -> bool: ...


def _now() -> datetime:
    return datetime.now(UTC)


def _object_id(url_id: str) -> ObjectId | None:
    try:
        return ObjectId(url_id)
    except (InvalidId, TypeError):
        return None


def _to_record(doc: dict[str, Any]) -> UrlRecord:
    return UrlRecord(id=str(doc.pop("_id")), **doc)


class MongoUrlRepository:
    def __init__(self, db: AsyncDatabase) -> None:
        self._collection = db["urls"]

    async def ensure_indexes(self) -> None:
        await self._collection.create_index("url", unique=True)

    async def create(self, url: str) -> UrlRecord:
        now = _now()
        doc = {
            "url": url,
            "status": CrawlStatus.PENDING.value,
            "crawl": None,
            "error": None,
            "created_at": now,
            "updated_at": now,
            "crawled_at": None,
        }
        try:
            result = await self._collection.insert_one(doc)
        except DuplicateKeyError as exc:
            raise DuplicateUrlError(url) from exc
        doc["_id"] = result.inserted_id
        return _to_record(doc)

    async def list(self) -> list[UrlRecord]:
        cursor = self._collection.find().sort("created_at", -1)
        return [_to_record(doc) async for doc in cursor]

    async def get(self, url_id: str) -> UrlRecord | None:
        oid = _object_id(url_id)
        if oid is None:
            return None
        doc = await self._collection.find_one({"_id": oid})
        return _to_record(doc) if doc else None

    async def update_url(self, url_id: str, url: str) -> UrlRecord | None:
        try:
            return await self._update(
                url_id,
                {
                    "url": url,
                    "status": CrawlStatus.PENDING.value,
                    "crawl": None,
                    "error": None,
                    "crawled_at": None,
                },
            )
        except DuplicateKeyError as exc:
            raise DuplicateUrlError(url) from exc

    async def save_crawl(self, url_id: str, crawl: CrawlData) -> UrlRecord | None:
        return await self._update(
            url_id,
            {
                "status": CrawlStatus.DONE.value,
                "crawl": crawl.model_dump(),
                "error": None,
                "crawled_at": _now(),
            },
        )

    async def save_crawl_error(self, url_id: str, error: str) -> UrlRecord | None:
        return await self._update(
            url_id,
            {"status": CrawlStatus.FAILED.value, "error": error, "crawled_at": _now()},
        )

    async def delete(self, url_id: str) -> bool:
        oid = _object_id(url_id)
        if oid is None:
            return False
        result = await self._collection.delete_one({"_id": oid})
        return result.deleted_count == 1

    async def _update(self, url_id: str, fields: dict[str, Any]) -> UrlRecord | None:
        oid = _object_id(url_id)
        if oid is None:
            return None
        doc = await self._collection.find_one_and_update(
            {"_id": oid},
            {"$set": {**fields, "updated_at": _now()}},
            return_document=ReturnDocument.AFTER,
        )
        return _to_record(doc) if doc else None

from datetime import UTC, datetime
from uuid import uuid4

from media_proxy_api.repositories.urls import (
    CrawlData,
    CrawlStatus,
    DuplicateUrlError,
    UrlRecord,
)


class InMemoryUrlRepository:
    def __init__(self) -> None:
        self.records: dict[str, UrlRecord] = {}

    async def create(self, url: str) -> UrlRecord:
        self._ensure_unique(url)
        now = datetime.now(UTC)
        record = UrlRecord(id=uuid4().hex, url=url, created_at=now, updated_at=now)
        self.records[record.id] = record
        return record

    async def list(self) -> list[UrlRecord]:
        return sorted(self.records.values(), key=lambda r: r.created_at, reverse=True)

    async def get(self, url_id: str) -> UrlRecord | None:
        return self.records.get(url_id)

    async def update_url(self, url_id: str, url: str) -> UrlRecord | None:
        self._ensure_unique(url, exclude=url_id)
        return self._update(
            url_id, url=url, status=CrawlStatus.PENDING, crawl=None, error=None, crawled_at=None
        )

    async def save_crawl(self, url_id: str, crawl: CrawlData) -> UrlRecord | None:
        return self._update(
            url_id, status=CrawlStatus.DONE, crawl=crawl, error=None, crawled_at=datetime.now(UTC)
        )

    async def save_crawl_error(self, url_id: str, error: str) -> UrlRecord | None:
        return self._update(
            url_id, status=CrawlStatus.FAILED, error=error, crawled_at=datetime.now(UTC)
        )

    async def delete(self, url_id: str) -> bool:
        return self.records.pop(url_id, None) is not None

    def _ensure_unique(self, url: str, exclude: str | None = None) -> None:
        if any(r.url == url and r.id != exclude for r in self.records.values()):
            raise DuplicateUrlError(url)

    def _update(self, url_id: str, **fields: object) -> UrlRecord | None:
        record = self.records.get(url_id)
        if record is None:
            return None
        updated = record.model_copy(update={**fields, "updated_at": datetime.now(UTC)})
        self.records[url_id] = updated
        return updated

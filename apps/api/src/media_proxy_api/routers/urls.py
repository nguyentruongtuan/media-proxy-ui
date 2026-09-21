from collections.abc import AsyncIterator
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, HttpUrl

from media_proxy_api.config import settings
from media_proxy_api.crawler import CrawlError, crawl
from media_proxy_api.db import get_database
from media_proxy_api.repositories.urls import (
    DuplicateUrlError,
    MongoUrlRepository,
    UrlRecord,
    UrlRepository,
)

router = APIRouter(prefix="/urls", tags=["urls"])


def get_url_repository() -> UrlRepository:
    return MongoUrlRepository(get_database())


async def get_http_client() -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient(timeout=settings.crawl_timeout_seconds) as client:
        yield client


Repository = Annotated[UrlRepository, Depends(get_url_repository)]
HttpClient = Annotated[httpx.AsyncClient, Depends(get_http_client)]


class UrlIn(BaseModel):
    url: HttpUrl


def _not_found(url_id: str) -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, f"URL {url_id} not found")


def _conflict(url: str) -> HTTPException:
    return HTTPException(status.HTTP_409_CONFLICT, f"URL {url} is already stored")


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_url(body: UrlIn, repo: Repository) -> UrlRecord:
    try:
        return await repo.create(str(body.url))
    except DuplicateUrlError as exc:
        raise _conflict(str(body.url)) from exc


@router.get("")
async def list_urls(repo: Repository) -> list[UrlRecord]:
    return await repo.list()


@router.get("/{url_id}")
async def get_url(url_id: str, repo: Repository) -> UrlRecord:
    record = await repo.get(url_id)
    if record is None:
        raise _not_found(url_id)
    return record


@router.put("/{url_id}")
async def update_url(url_id: str, body: UrlIn, repo: Repository) -> UrlRecord:
    try:
        record = await repo.update_url(url_id, str(body.url))
    except DuplicateUrlError as exc:
        raise _conflict(str(body.url)) from exc
    if record is None:
        raise _not_found(url_id)
    return record


@router.delete("/{url_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_url(url_id: str, repo: Repository) -> Response:
    if not await repo.delete(url_id):
        raise _not_found(url_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{url_id}/crawl")
async def crawl_url(url_id: str, repo: Repository, client: HttpClient) -> UrlRecord:
    """Fetch the stored URL now and store the extracted movie data on the record.

    On failure the error is stored on the record (status "failed") and a 502 is returned.
    """
    record = await repo.get(url_id)
    if record is None:
        raise _not_found(url_id)
    try:
        data = await crawl(record.url, client)
    except CrawlError as exc:
        await repo.save_crawl_error(url_id, str(exc))
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc)) from exc
    saved = await repo.save_crawl(url_id, data)
    if saved is None:
        raise _not_found(url_id)
    return saved

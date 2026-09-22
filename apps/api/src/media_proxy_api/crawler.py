"""Fetch a movie page and extract its title, description, images and streaming URLs.

Extraction prefers structured data (Open Graph / Twitter meta tags, JSON-LD) and falls
back to page markup (<video>, <iframe>, <img>) and media URLs embedded in inline scripts.
"""

import json
import re
from collections.abc import Iterable, Iterator
from typing import Any
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup, Tag

from media_proxy_api.repositories.urls import CrawlData

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0 Safari/537.36"
)

# Direct media URLs, also when JSON-escaped inside scripts (https:\/\/cdn\/a.m3u8).
_MEDIA_URL_RE = re.compile(
    r"""https?:(?:\\?/){2}[^\s"'<>]+?\.(?:m3u8|mpd|mp4|webm)(?:\?[^\s"'<>\\]*)?""",
    re.IGNORECASE,
)
_LD_TYPES = {"movie", "videoobject", "tvepisode", "tvseries", "episode", "creativework"}
_MAX_FALLBACK_IMAGES = 10


class CrawlError(Exception):
    pass


async def crawl(url: str, client: httpx.AsyncClient) -> CrawlData:
    html, final_url = await fetch_html(url, client)
    return extract_movie(html, final_url)


async def fetch_html(url: str, client: httpx.AsyncClient) -> tuple[str, str]:
    """Return the page HTML and the URL it was served from (after redirects)."""
    try:
        response = await client.get(url, headers={"User-Agent": USER_AGENT}, follow_redirects=True)
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise CrawlError(f"{url} responded with {exc.response.status_code}") from exc
    except httpx.HTTPError as exc:
        raise CrawlError(f"Could not fetch {url}: {exc}") from exc

    content_type = response.headers.get("content-type", "")
    if "html" not in content_type:
        raise CrawlError(f"{url} is not an HTML page (content-type: {content_type or 'none'})")
    return response.text, str(response.url)


def extract_movie(html: str, base_url: str) -> CrawlData:
    soup = BeautifulSoup(html, "html.parser")
    ld = _json_ld_nodes(soup)

    def absolute(urls: Iterable[str | None]) -> list[str]:
        return _unique(urljoin(base_url, u.strip()) for u in urls if _is_link(u))

    title = _first(
        _meta(soup, "og:title"),
        _meta(soup, "twitter:title"),
        *(_text(node.get("name")) for node in ld),
        _tag_text(soup.find("h1")),
        _tag_text(soup.title),
    )
    description = _first(
        _meta(soup, "og:description"),
        _meta(soup, "description"),
        _meta(soup, "twitter:description"),
        *(_text(node.get("description")) for node in ld),
    )

    images = absolute(
        [
            _meta(soup, "og:image"),
            _meta(soup, "og:image:url"),
            _meta(soup, "og:image:secure_url"),
            _meta(soup, "twitter:image"),
            _meta(soup, "twitter:image:src"),
            *(_attr(link, "href") for link in soup.select("link[rel~=image_src]")),
            *(_attr(video, "poster") for video in soup.find_all("video")),
            *(u for node in ld for key in ("image", "thumbnailUrl") for u in _ld_urls(node, key)),
        ]
    )
    if not images:
        images = absolute(
            _attr(img, "data-src") or _attr(img, "src") for img in soup.find_all("img")
        )[:_MAX_FALLBACK_IMAGES]

    stream_urls = absolute(
        [
            *(_attr(video, "src") for video in soup.find_all("video")),
            *(_attr(source, "src") for source in soup.select("video source")),
            _meta(soup, "og:video"),
            _meta(soup, "og:video:url"),
            _meta(soup, "og:video:secure_url"),
            _meta(soup, "twitter:player:stream"),
            *(u for node in ld for u in _ld_urls(node, "contentUrl")),
            *(m.replace("\\/", "/") for m in _MEDIA_URL_RE.findall(html)),
        ]
    )
    embed_urls = absolute(
        [
            *(
                _attr(iframe, "data-src") or _attr(iframe, "src")
                for iframe in soup.find_all("iframe")
            ),
            _meta(soup, "twitter:player"),
            *(u for node in ld for u in _ld_urls(node, "embedUrl")),
        ]
    )

    return CrawlData(
        title=title,
        description=description,
        images=images,
        stream_urls=stream_urls,
        embed_urls=embed_urls,
    )


def _meta(soup: BeautifulSoup, name: str) -> str | None:
    tag = soup.find("meta", attrs={"property": name}) or soup.find("meta", attrs={"name": name})
    return _text(tag.get("content")) if isinstance(tag, Tag) else None


def _attr(tag: Any, name: str) -> str | None:
    return _text(tag.get(name)) if isinstance(tag, Tag) else None


def _tag_text(tag: Any) -> str | None:
    return _text(tag.get_text(" ", strip=True)) if isinstance(tag, Tag) else None


def _text(value: Any) -> str | None:
    if isinstance(value, list):
        value = " ".join(str(v) for v in value)
    if not isinstance(value, str):
        return None
    value = " ".join(value.split())
    return value or None


def _first(*values: str | None) -> str | None:
    return next((v for v in values if v), None)


def _is_link(url: str | None) -> bool:
    if not url:
        return False
    lowered = url.strip().lower()
    return not lowered.startswith(("data:", "javascript:", "about:", "blob:"))


def _unique(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _json_ld_nodes(soup: BeautifulSoup) -> list[dict[str, Any]]:
    """JSON-LD objects describing the movie/video, in document order."""
    nodes: list[dict[str, Any]] = []
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            data = json.loads(script.string or "")
        except ValueError:
            continue
        nodes.extend(node for node in _walk(data) if _ld_type_matches(node))
    return nodes


def _walk(data: Any) -> Iterator[dict[str, Any]]:
    if isinstance(data, list):
        for item in data:
            yield from _walk(item)
    elif isinstance(data, dict):
        yield data
        for value in data.values():
            if isinstance(value, dict | list):
                yield from _walk(value)


def _ld_type_matches(node: dict[str, Any]) -> bool:
    types = node.get("@type")
    types = types if isinstance(types, list) else [types]
    return any(isinstance(t, str) and t.lower() in _LD_TYPES for t in types)


def _ld_urls(node: dict[str, Any], key: str) -> list[str]:
    value = node.get(key)
    values = value if isinstance(value, list) else [value]
    urls = []
    for item in values:
        if isinstance(item, dict):
            item = item.get("url") or item.get("contentUrl")
        if isinstance(item, str):
            urls.append(item)
    return urls

from collections.abc import AsyncIterator, Callable, Iterator

import httpx
import pytest
from fastapi.testclient import TestClient

from media_proxy_api.main import app
from media_proxy_api.routers.urls import get_http_client, get_url_repository
from tests.fakes import InMemoryUrlRepository

MOVIE_URL = "https://movies.example.com/watch/big-buck-bunny"
MOVIE_HTML = """
<html><head>
  <meta property="og:title" content="Big Buck Bunny">
  <meta property="og:description" content="A giant rabbit takes revenge.">
  <meta property="og:image" content="/posters/bbb.jpg">
</head><body>
  <video src="https://cdn.example.com/bbb/master.m3u8"></video>
</body></html>
"""

Handler = Callable[[httpx.Request], httpx.Response]


def html_page(body: str, status_code: int = 200) -> Handler:
    return lambda _: httpx.Response(
        status_code, text=body, headers={"content-type": "text/html; charset=utf-8"}
    )


@pytest.fixture
def repo() -> InMemoryUrlRepository:
    return InMemoryUrlRepository()


@pytest.fixture
def remote() -> dict[str, Handler]:
    """The handler that answers crawl requests; tests swap it per scenario."""
    return {"handler": html_page(MOVIE_HTML)}


@pytest.fixture
def client(repo: InMemoryUrlRepository, remote: dict[str, Handler]) -> Iterator[TestClient]:
    async def http_client() -> AsyncIterator[httpx.AsyncClient]:
        transport = httpx.MockTransport(lambda request: remote["handler"](request))
        async with httpx.AsyncClient(transport=transport) as c:
            yield c

    app.dependency_overrides[get_url_repository] = lambda: repo
    app.dependency_overrides[get_http_client] = http_client
    # No `with`: skips the lifespan, which would create indexes on a real MongoDB.
    yield TestClient(app)
    app.dependency_overrides.clear()


def create(client: TestClient, url: str = MOVIE_URL) -> dict:
    response = client.post("/api/urls", json={"url": url})
    assert response.status_code == 201
    return response.json()


def test_create_stores_url_as_pending(client: TestClient) -> None:
    body = create(client)
    assert body["url"] == MOVIE_URL
    assert body["status"] == "pending"
    assert body["crawl"] is None


def test_create_rejects_invalid_url(client: TestClient) -> None:
    assert client.post("/api/urls", json={"url": "not a url"}).status_code == 422


def test_create_rejects_duplicate_url(client: TestClient) -> None:
    create(client)
    assert client.post("/api/urls", json={"url": MOVIE_URL}).status_code == 409


def test_get_and_list(client: TestClient) -> None:
    created = create(client)
    assert client.get(f"/api/urls/{created['id']}").json() == created
    assert client.get("/api/urls").json() == [created]


def test_get_unknown_id_is_404(client: TestClient) -> None:
    assert client.get("/api/urls/nope").status_code == 404


def test_update_changes_url_and_resets_crawl(client: TestClient) -> None:
    created = create(client)
    client.post(f"/api/urls/{created['id']}/crawl")

    new_url = "https://movies.example.com/watch/sintel"
    response = client.put(f"/api/urls/{created['id']}", json={"url": new_url})

    assert response.status_code == 200
    body = response.json()
    assert body["url"] == new_url
    assert body["status"] == "pending"
    assert body["crawl"] is None


def test_update_unknown_id_is_404(client: TestClient) -> None:
    assert client.put("/api/urls/nope", json={"url": MOVIE_URL}).status_code == 404


def test_update_to_existing_url_is_409(client: TestClient) -> None:
    create(client)
    other = create(client, "https://movies.example.com/watch/sintel")
    response = client.put(f"/api/urls/{other['id']}", json={"url": MOVIE_URL})
    assert response.status_code == 409


def test_delete(client: TestClient) -> None:
    created = create(client)
    assert client.delete(f"/api/urls/{created['id']}").status_code == 204
    assert client.get(f"/api/urls/{created['id']}").status_code == 404
    assert client.delete(f"/api/urls/{created['id']}").status_code == 404


def test_crawl_stores_extracted_movie_data(client: TestClient) -> None:
    created = create(client)

    response = client.post(f"/api/urls/{created['id']}/crawl")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "done"
    assert body["crawled_at"] is not None
    assert body["crawl"] == {
        "title": "Big Buck Bunny",
        "description": "A giant rabbit takes revenge.",
        "images": ["https://movies.example.com/posters/bbb.jpg"],
        "stream_urls": ["https://cdn.example.com/bbb/master.m3u8"],
        "embed_urls": [],
    }
    assert client.get(f"/api/urls/{created['id']}").json() == body


def test_crawl_upstream_error_marks_record_failed(
    client: TestClient, remote: dict[str, Handler]
) -> None:
    remote["handler"] = html_page("gone", status_code=404)
    created = create(client)

    response = client.post(f"/api/urls/{created['id']}/crawl")

    assert response.status_code == 502
    stored = client.get(f"/api/urls/{created['id']}").json()
    assert stored["status"] == "failed"
    assert "404" in stored["error"]


def test_crawl_non_html_response_fails(client: TestClient, remote: dict[str, Handler]) -> None:
    remote["handler"] = lambda _: httpx.Response(200, json={"not": "html"})
    created = create(client)

    assert client.post(f"/api/urls/{created['id']}/crawl").status_code == 502


def test_crawl_unknown_id_is_404(client: TestClient) -> None:
    assert client.post("/api/urls/nope/crawl").status_code == 404

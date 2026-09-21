from media_proxy_api.crawler import extract_movie

BASE = "https://movies.example.com/watch/sintel"


def test_prefers_open_graph_metadata() -> None:
    html = """
    <html><head>
      <title>Sintel | Movies</title>
      <meta property="og:title" content="Sintel">
      <meta name="description" content="Plain description">
      <meta property="og:description" content="OG description">
      <meta property="og:image" content="https://img.example.com/sintel.jpg">
      <meta name="twitter:image" content="/sintel-small.jpg">
    </head><body><h1>Heading</h1></body></html>
    """
    data = extract_movie(html, BASE)
    assert data.title == "Sintel"
    assert data.description == "OG description"
    assert data.images == [
        "https://img.example.com/sintel.jpg",
        "https://movies.example.com/sintel-small.jpg",
    ]


def test_falls_back_to_markup_when_no_meta() -> None:
    html = """
    <html><head><title>  Sintel
      | Movies </title><meta name="description" content="A girl and a dragon."></head>
    <body><img src="data:image/gif;base64,xx"><img data-src="/a.jpg" src="/lazy.gif"></body></html>
    """
    data = extract_movie(html, BASE)
    assert data.title == "Sintel | Movies"
    assert data.description == "A girl and a dragon."
    assert data.images == ["https://movies.example.com/a.jpg"]


def test_extracts_video_sources_and_poster() -> None:
    html = """
    <video poster="/poster.jpg" src="/media/sintel.mp4">
      <source src="https://cdn.example.com/sintel.webm" type="video/webm">
      <source src="/media/sintel.mp4">
    </video>
    """
    data = extract_movie(html, BASE)
    assert data.images == ["https://movies.example.com/poster.jpg"]
    assert data.stream_urls == [
        "https://movies.example.com/media/sintel.mp4",
        "https://cdn.example.com/sintel.webm",
    ]


def test_extracts_media_urls_from_inline_scripts() -> None:
    html = r"""
    <script>
      var player = {"file":"https:\/\/cdn.example.com\/hls\/sintel\/index.m3u8?token=abc"};
      jwplayer().setup({sources: [{file: 'https://cdn2.example.com/sintel.mpd'}]});
    </script>
    """
    data = extract_movie(html, BASE)
    assert data.stream_urls == [
        "https://cdn.example.com/hls/sintel/index.m3u8?token=abc",
        "https://cdn2.example.com/sintel.mpd",
    ]


def test_extracts_embeds_from_iframes() -> None:
    html = """
    <iframe src="about:blank" data-src="https://player.example.com/embed/42"></iframe>
    <iframe src="//other.example.com/e/7"></iframe>
    <iframe src="javascript:void(0)"></iframe>
    """
    data = extract_movie(html, BASE)
    assert data.embed_urls == [
        "https://player.example.com/embed/42",
        "https://other.example.com/e/7",
    ]


def test_reads_json_ld_movie() -> None:
    html = """
    <script type="application/ld+json">
    {"@context": "https://schema.org", "@graph": [
      {"@type": "WebSite", "name": "Movies"},
      {"@type": "Movie", "name": "Sintel", "description": "Dragon story.",
       "image": {"@type": "ImageObject", "url": "https://img.example.com/ld.jpg"},
       "trailer": {"@type": "VideoObject", "contentUrl": "https://cdn.example.com/trailer.mp4",
                   "embedUrl": "https://player.example.com/trailer",
                   "thumbnailUrl": ["https://img.example.com/thumb.jpg"]}}
    ]}
    </script>
    <script type="application/ld+json">{broken json</script>
    """
    data = extract_movie(html, BASE)
    assert data.title == "Sintel"
    assert data.description == "Dragon story."
    assert data.images == [
        "https://img.example.com/ld.jpg",
        "https://img.example.com/thumb.jpg",
    ]
    assert data.stream_urls == ["https://cdn.example.com/trailer.mp4"]
    assert data.embed_urls == ["https://player.example.com/trailer"]


def test_empty_page_yields_empty_data() -> None:
    data = extract_movie("<html></html>", BASE)
    assert data.title is None
    assert data.description is None
    assert data.images == data.stream_urls == data.embed_urls == []

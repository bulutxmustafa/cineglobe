"""Title backdrop must not repeat the poster artwork."""

from unittest.mock import MagicMock

import pytest
from apps.catalog import backdrops
from django.core.cache import cache

RED = [1.0] + [0.0] * 63
BLUE = [0.0] * 63 + [1.0]


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()
    yield
    cache.clear()


def fake_histograms(monkeypatch, mapping, layout=1.0):
    """Images are stand-in names; their histograms come from `mapping`."""
    monkeypatch.setattr(backdrops, "load_image", lambda url: url.rsplit("/", 1)[-1])
    monkeypatch.setattr(backdrops, "colour_histogram", lambda name: mapping[name])
    monkeypatch.setattr(backdrops, "layout_match", lambda poster, backdrop: layout)


def test_keeps_default_backdrop_when_it_differs_from_poster(monkeypatch):
    fake_histograms(monkeypatch, {"p.jpg": RED, "default.jpg": BLUE})
    client = MagicMock()
    chosen = backdrops.choose_backdrop(client, "tv", 1, "/p.jpg", "/default.jpg")
    assert chosen == "/default.jpg"
    client.get_images.assert_not_called()


def test_replaces_backdrop_that_repeats_the_poster(monkeypatch):
    fake_histograms(
        monkeypatch,
        {"p.jpg": RED, "default.jpg": RED, "alsored.jpg": RED, "scene.jpg": BLUE},
    )
    client = MagicMock()
    client.get_images.return_value = {
        "backdrops": [
            {"file_path": "/default.jpg", "vote_count": 50},
            {"file_path": "/alsored.jpg", "vote_count": 40},
            {"file_path": "/scene.jpg", "vote_count": 30},
        ]
    }
    chosen = backdrops.choose_backdrop(client, "movie", 2, "/p.jpg", "/default.jpg")
    assert chosen == "/scene.jpg"
    # Cached: a second call needs no downloads.
    monkeypatch.setattr(backdrops, "load_image", lambda url: 1 / 0)
    assert (
        backdrops.choose_backdrop(client, "movie", 2, "/p.jpg", "/default.jpg")
        == "/scene.jpg"
    )


def test_network_problem_keeps_default(monkeypatch):
    chosen = backdrops.choose_backdrop(
        MagicMock(), "movie", 3, "/p.jpg", "/default.jpg"
    )
    assert chosen == "/default.jpg"


def test_same_colours_but_different_layout_keeps_default(monkeypatch):
    fake_histograms(monkeypatch, {"p.jpg": RED, "default.jpg": RED}, layout=0.1)
    client = MagicMock()
    chosen = backdrops.choose_backdrop(client, "movie", 4, "/p.jpg", "/default.jpg")
    assert chosen == "/default.jpg"
    client.get_images.assert_not_called()

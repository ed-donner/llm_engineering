import datetime as dt

from services import utils


def test_normalize_items_deduplicates():
    ts = dt.datetime(2025, 1, 1, tzinfo=dt.timezone.utc)
    items = [
        utils.NormalizedItem(
            source="reddit",
            id="1",
            url="https://example.com/a",
            author="alice",
            timestamp=ts,
            text="ReputationRadar is great!",
            meta={},
        ),
        utils.NormalizedItem(
            source="reddit",
            id="2",
            url="https://example.com/a",
            author="bob",
            timestamp=ts,
            text="ReputationRadar is great!",
            meta={},
        ),
    ]
    cleaned = utils.normalize_items(items)
    assert len(cleaned) == 1


def test_sanitize_text_removes_html():
    raw = "<p>Hello <strong>world</strong> &nbsp; <a href='https://example.com'>link</a></p>"
    cleaned = utils.sanitize_text(raw)
    assert cleaned == "Hello world link"

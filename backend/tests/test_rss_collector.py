import sys
import types
from pathlib import Path
from datetime import datetime
from types import SimpleNamespace

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.append(str(BACKEND_ROOT))

from app.services.collectors.rss import RSSCollector  # noqa: E402


def test_extract_text_from_twitter_html():
    collector = RSSCollector()
    html_content = (
        '<blockquote class="twitter-tweet"><p lang="en">Hello<br>World</p>'
        "— User (@u) <a href=\"https://twitter.com/u/status/1\">Nov 22, 2025</a>"
        '</blockquote><script async src="https://platform.twitter.com/widgets.js"></script>'
    )

    text = collector._extract_text_from_html(html_content)

    assert "Hello World" in text
    assert "widgets.js" not in text
    assert "Nov 22, 2025" in text


def test_build_twitter_item_sets_platform_and_text():
    collector = RSSCollector()
    html_content = '<blockquote class="twitter-tweet"><p lang="en">Hello World</p></blockquote>'
    entry = types.SimpleNamespace(
        title="Sample tweet title",
        description=html_content,
        link="https://x.com/u/status/1",
        id="1",
        dc_creator="@u",
    )

    item = collector._build_twitter_item(entry, datetime(2025, 1, 1), base_heat=80.0, category_override=None)

    assert item.source_platform == "x"
    assert "Hello World" in item.original_text
    assert item.url == "https://x.com/u/status/1"
    assert item.author_name == "@u"
    assert item.heat_score == 80.0


@pytest.mark.asyncio
async def test_collect_with_rss_twitter_feed(monkeypatch):
    collector = RSSCollector()
    collector.config = {
        "rss": {
            "feeds": [
                {
                    "url": "https://rss.app/feeds/AAPQYwfvRjqTfYsj.xml",
                    "name": "naval AI",
                    "type": "rss_twitter",
                    "base_heat": 88,
                }
            ]
        }
    }

    fake_entry = SimpleNamespace(
        title="Tweet title",
        description='<blockquote class="twitter-tweet"><p>Hello<br>AI</p></blockquote>',
        link="https://x.com/u/status/123",
        id="123",
        dc_creator="@u",
        published_parsed=(2025, 1, 1, 0, 0, 0, 0, 0, 0),
    )

    class FakeFeed:
        def __init__(self):
            self.entries = [fake_entry]

    monkeypatch.setattr("app.services.collectors.rss.feedparser.parse", lambda url: FakeFeed())

    items = await collector.collect()

    assert len(items) == 1
    item = items[0]
    assert item.source_platform == "x"
    assert "Hello AI" in item.original_text
    assert item.heat_score == 88
    assert item.url == "https://x.com/u/status/123"

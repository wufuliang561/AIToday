import sys
import types
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.append(str(BACKEND_ROOT))

from app.models.item import RawItem
from app.services import processor as processor_module
from app.services.processor import Processor


class FakeResponse:
    def __init__(self, content: str):
        self.choices = [types.SimpleNamespace(message=types.SimpleNamespace(content=content))]


class FakeClient:
    def __init__(self, content: str):
        self.content = content
        self.calls = []
        # mimic client.chat.completions.create
        self.chat = self
        self.completions = self

    def create(self, model, messages):
        self.calls.append(messages)
        return FakeResponse(self.content)


def make_item(**overrides) -> RawItem:
    base = dict(
        source_platform="rss",
        source_id="sid",
        original_title="Hello AI",
        original_text="This is a body about AI models.",
        title_cn="",
        url="http://example.com",
    )
    base.update(overrides)
    return RawItem(**base)


@pytest.mark.asyncio
async def test_process_item_parses_structured_lines(monkeypatch):
    fake_client = FakeClient("Title: 中文标题\nSummary: 中文摘要\nCategory: AI工具")
    embed_inputs = []
    monkeypatch.setattr(processor_module.embedding_service, "get_embedding", lambda text: embed_inputs.append(text))

    proc = Processor()
    proc.client = fake_client
    proc._is_ai_related = lambda item: True

    item = make_item(source_platform="reddit")
    result = await proc.process_item(item)

    assert result.title_cn == "中文标题"
    assert result.summary_cn == "中文摘要"
    assert result.category == "AI工具"
    assert embed_inputs[-1].startswith("中文标题 中文摘要")


@pytest.mark.asyncio
async def test_process_item_falls_back_when_category_unknown(monkeypatch):
    fake_client = FakeClient("Title: 标题\nSummary: 摘要\nCategory: Unknown")
    monkeypatch.setattr(processor_module.embedding_service, "get_embedding", lambda text: None)

    proc = Processor()
    proc.client = fake_client
    proc._is_ai_related = lambda item: True

    item = make_item(source_platform="rss")
    result = await proc.process_item(item)

    assert result.category == "其他"
    assert result.title_cn == "标题"
    assert result.summary_cn == "摘要"


@pytest.mark.asyncio
async def test_process_item_uses_source_specific_prompt(monkeypatch):
    fake_client = FakeClient("Title: T\nSummary: S\nCategory: 学术论文")
    monkeypatch.setattr(processor_module.embedding_service, "get_embedding", lambda text: None)

    proc = Processor()
    proc.client = fake_client
    proc._is_ai_related = lambda item: True

    item = make_item(source_platform="youtube", original_text="demo description")
    await proc.process_item(item)

    # user prompt is the second message, should mention YouTube 视频
    user_prompt = fake_client.calls[-1][1]["content"]
    assert "YouTube 视频" in user_prompt
    assert "Title: T" not in user_prompt  # ensure we are inspecting prompt, not model output

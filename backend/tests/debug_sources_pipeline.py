"""YouTube / RSS 采集调试脚本。

该脚本把采集器、LLM Processor 以及入库前的准备统一串联起来，
通过详细的中文日志输出“采集→处理→入库前检查”的完整轨迹，
方便排查每一个环节的输入输出，确认配置、模型或网络问题。
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Type

# 将 backend 目录加入 sys.path，确保脚本无论从哪里运行都能定位到 app.* 包。
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.collectors.base import BaseCollector
from app.services.collectors.rss import RSSCollector
from app.services.collectors.youtube import YouTubeCollector
from app.services.collectors.reddit import RedditCollector
from app.services.processor import Processor
from app.core.logging_config import setup_logging


# 支持的采集器，通过映射关系便于根据命令行参数动态实例化。
COLLECTOR_FACTORIES: Dict[str, Type[BaseCollector]] = {
    # "youtube": YouTubeCollector,
    # "rss": RSSCollector,
    "reddit": RedditCollector,
}


# 将长文本压缩成同一行并截断，避免调试日志过长。
def _preview_text(text: str | None, limit: int = 200) -> str:
    if not text:
        return "<empty>"
    flattened = " ".join(text.split())
    if len(flattened) <= limit:
        return flattened
    return f"{flattened[:limit]}..."


# 构造一个接近数据库写入格式的字典，方便观察 Processor 产物。
def _serialize_for_db(item) -> dict:
    return {
        "source_platform": item.source_platform,
        "source_id": item.source_id,
        "title_cn": item.title_cn,
        "summary_cn": item.summary_cn,
        "category": item.category,
        "author_name": item.author_name,
        "url": item.url,
        "published_at": item.published_at.isoformat() if item.published_at else None,
        "heat_score": item.heat_score,
        "embedding_dimensions": len(item.embedding) if item.embedding else 0,
    }


async def _debug_source(source: str, limit: int) -> None:
    collector_cls = COLLECTOR_FACTORIES[source]
    collector = collector_cls()
    # 步骤 1：拉取原始数据，确认采集阶段（API/网络/配置）是否运作正常。
    print(f"【步骤 1】使用 {collector_cls.__name__} 采集原始数据……")
    items = await collector.collect()
    if not items:
        print("采集结果为空，终止调试。请检查频道/抓取配置。")
        return

    items_to_process = items[:limit]
    print(
        f"共采集 {len(items)} 条，选取前 {len(items_to_process)} 条进入流水线调试。"
    )

    processor = Processor()
    for index, item in enumerate(items_to_process, start=1):
        print("\n========================================")
        print(f"调试条目 #{index}")
        print(f"来源平台: {item.source_platform}")
        print(f"来源 ID: {item.source_id}")
        print(f"原始标题: {item.original_title}")
        print(f"原文预览: {_preview_text(item.original_text)}")
        print(f"发布时间: {item.published_at}")
        print(f"原始链接: {item.url}")

        print("【步骤 2】进入 Processor / LLM 流程……")
        # 步骤 2：将条目送入 Processor，观察翻译、分类与嵌入生成是否符合预期。
        processed_item = await processor.process_item(item)
        if not processed_item:
            print("判定为非 AI 相关内容，已跳过后续处理和入库。")
            continue
        print(f"译文标题（title_cn）: {processed_item.title_cn}")
        print(f"中文摘要（summary_cn）: {processed_item.summary_cn or '<empty>'}")
        print(f"分类结果（category）: {processed_item.category or '<unset>'}")
        embedding_dim = len(processed_item.embedding) if processed_item.embedding else 0
        print(f"向量维度: {embedding_dim}")

        print("【步骤 3】模拟入库：打印准备写入数据库的载荷……")
        serialized = _serialize_for_db(processed_item)
        print(json.dumps(serialized, ensure_ascii=False, indent=2))
        if processed_item.embedding:
            preview = processed_item.embedding[:8]
            print(f"向量内容预览（前 8 个数值）: {preview}")

    print("\n调试流程结束，未对数据库执行任何写入操作。")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="调试 RSS / YouTube / Reddit 采集器的全链路流程。")
    parser.add_argument(
        "--source",
        choices=COLLECTOR_FACTORIES.keys(),
        required=True,
        help="选择需要调试的采集器（youtube / rss / reddit）。",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=1,
        help="指定要调试的条目数量，默认 1。",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    setup_logging()
    asyncio.run(_debug_source(args.source, max(1, args.limit)))


if __name__ == "__main__":
    main()

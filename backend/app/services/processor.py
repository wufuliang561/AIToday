import logging
import json
import asyncio
from typing import Dict, Optional
from openai import OpenAI
from app.core.config import settings
from app.models.item import RawItem
from app.services.embedding import embedding_service

logger = logging.getLogger(__name__)

class Processor:
    def __init__(self):
        self.client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL
        ) if settings.OPENAI_API_KEY else None
        self.model = settings.OPENAI_MODEL

    async def process_item(self, item: RawItem) -> Optional[RawItem]:
        """
        将翻译、摘要、分类合并为一次 LLM 调用；提示词根据来源定制。
        """
        if not self.client:
            logger.warning("OpenAI client not initialized; falling back to original title")
            item.title_cn = item.original_title # 回退
            return item

        try:
            logger.info(
                "Processing item %s (%s) with single LLM call",
                item.source_id,
                item.source_platform,
            )
            messages = self._build_messages(item)
            self._log_prompt(item, messages)
            content = await asyncio.to_thread(self._call_llm, messages)
            self._log_response(item, content)
            parsed = self._parse_structured_output(content)

            if parsed.get("filtered"):
                logger.info("Item %s filtered as non-AI; skipping.", item.source_id)
                return None

            item.title_cn = parsed.get("title_cn") or item.original_title
            item.summary_cn = parsed.get("summary_cn") or ""
            category = parsed.get("category")
            if category in settings.NEWS_CATEGORIES:
                item.category = category
            else:
                item.category = "其他"

        except Exception as e:
            logger.exception("Error processing item %s", item.id or item.source_id)
            item.title_cn = item.original_title # 回退
            item.category = item.category or "其他"

        # 生成向量
        try:
            # 优先使用中文标题和摘要
            text_to_embed = f"{item.title_cn}"
            if item.summary_cn:
                text_to_embed += f" {item.summary_cn}"
            elif item.original_text:
                # 如果没有中文摘要，使用原文前500个字符补充
                text_to_embed += f" {item.original_text[:500]}"

            logger.info("Generating embedding for item %s", item.source_id)
            item.embedding = await asyncio.to_thread(embedding_service.get_embedding, text_to_embed)
        except Exception as e:
            logger.exception("Error generating embedding for item %s", item.id or item.source_id)

        return item

    def _build_messages(self, item: RawItem):
        """根据来源构造一次性翻译/摘要/分类/过滤的提示词。"""
        categories_str = ", ".join(settings.NEWS_CATEGORIES)
        source = (item.source_platform or "rss").lower()
        system_prompt = (
            "You are a bilingual tech editor and AI relevance gatekeeper. Translate to professional Chinese, "
            "keep AI/tech terms in English, respect proper nouns, and return compact, factual outputs."
        )

        source_prompts: Dict[str, str] = {
            "x": (
                "来源：Twitter/X 推文\n"
                "重点：保留账号/话题/模型名，捕捉核心观点或更新，生成新闻式标题。"
            ),
            "youtube": (
                "来源：YouTube 视频\n"
                "重点：结合标题与描述抓取核心主题（发布/演示/评测/访谈），突出关键信息。"
            ),
            "huggingface": (
                "来源：HuggingFace Daily Papers\n"
                "重点：科研论文，提炼方法/贡献/结果，保持学术语气。"
            ),
            "reddit": (
                "来源：Reddit 帖子\n"
                "重点：社区讨论或分享，提炼观点或结论，避免主观臆测。"
            ),
            "rss": (
                "来源：RSS 新闻/博客\n"
                "重点：新闻或官方博文，保持客观、精简表述。"
            ),
        }

        source_header = source_prompts.get(source, source_prompts["rss"])
        content_body = item.original_text or ""

        title_step = "1) 翻译 Title 为中文标题，保留专有名词与产品名。"
        if source == "x":
            title_step = "1) 基于正文生成一句新闻式中文标题（不要直译，突出关键信息/动作/对象；正文为空再基于 Title）。"

        user_prompt = f"""
{source_header}

输入：
Title: {item.original_title}
Body: {content_body}

任务（一次性完成）：
0) 首先判断内容是否与“人工智能、AI 工具、AI 产业、AI 研究”密切相关；若不相关，直接返回一行 "Filtered: Not AI-related"（不再输出其他内容）。
{title_step}
2) 生成一句中文摘要（若正文为空，可基于标题）。
3) 从下列分类中选 1 个：{categories_str}。

输出格式（严格按行，不要额外文本、不要 Markdown）：
Title: <中文标题>
Summary: <中文摘要>
Category: <分类名称>
"""
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def _parse_structured_output(self, content: str) -> Dict[str, str]:
        """
        解析 LLM 返回的 Title/Summary/Category 行，兼容 JSON 回退。
        """
        if not content:
            return {}

        normalized = content.strip()
        normalized_lower = normalized.lower()
        if normalized_lower.startswith("filtered"):
            return {"filtered": True}

        # 优先尝试 JSON 解析
        try:
            data = json.loads(content)
            return {
                "title_cn": data.get("title") or data.get("title_cn"),
                "summary_cn": data.get("summary") or data.get("summary_cn"),
                "category": data.get("category"),
            }
        except Exception:
            pass

        title_cn = ""
        summary_cn = ""
        category = ""
        for line in content.splitlines():
            line = line.strip()
            if line.lower().startswith("title:"):
                title_cn = line.split(":", 1)[1].strip()
            elif line.lower().startswith("summary:"):
                summary_cn = line.split(":", 1)[1].strip()
            elif line.lower().startswith("category:"):
                category = line.split(":", 1)[1].strip()

        return {"title_cn": title_cn, "summary_cn": summary_cn, "category": category}

    def _log_prompt(self, item: RawItem, messages):
        """记录发送给大模型的 system 与 user 提示词，便于排查。"""
        try:
            system_msg = next((m.get("content", "") for m in messages if m.get("role") == "system"), "")
            user_msg = next((m.get("content", "") for m in messages if m.get("role") == "user"), "")
            logger.info(
                "LLM prompt for item %s | system=%s | user=%s",
                item.source_id,
                self._truncate(system_msg),
                self._truncate(user_msg),
            )
        except Exception:
            logger.exception("Failed to log LLM prompt for item %s", item.source_id)

    def _log_response(self, item: RawItem, content: str):
        """记录大模型的原始响应，保留排查上下文。"""
        try:
            logger.info(
                "LLM response for item %s | raw=%s",
                item.source_id,
                self._truncate(content),
            )
        except Exception:
            logger.exception("Failed to log LLM response for item %s", item.source_id)

    @staticmethod
    def _truncate(text: str, limit: int = 400) -> str:
        """日志输出前对文本截断，避免过长刷屏。"""
        if text is None:
            return ""
        text = str(text)
        if len(text) <= limit:
            return text
        return text[:limit] + "...[truncated]"

    def _call_llm(self, messages):
        """同步调用 LLM，封装便于在线程池中运行。"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
        )
        return response.choices[0].message.content

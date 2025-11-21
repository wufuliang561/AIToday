import logging
from typing import Optional
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
        将标题翻译成中文，并在需要时进行总结。
        """
        if not self.client:
            logger.warning("OpenAI client not initialized; falling back to original title")
            item.title_cn = item.original_title # 回退
            return item

        if not self._is_ai_related(item):
            logger.info("Item %s is not AI-related; skipping.", item.source_id)
            return None

        try:
            # 翻译标题
            logger.info("Translating item %s from %s", item.source_id, item.source_platform)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional tech translator. Translate the following text to Chinese. Rules:\n1. Keep technical terms (e.g., Gemini, GPT, LLM, Transformer, CUDA) in English.\n2. Do not translate proper nouns or product names (e.g., Apple, Google, OpenAI).\n3. Ensure the translation is natural and professional.\nOnly return the translated text."},
                    {"role": "user", "content": item.original_title}
                ]
            )
            item.title_cn = response.choices[0].message.content.strip()

            # 总结和分类
            if item.source_platform == "x" or (item.original_text and len(item.original_text) > 200):
                categories_str = ", ".join(settings.NEWS_CATEGORIES)
                prompt = f"""
                Task 1: Summarize the following text into a single Chinese sentence.
                Task 2: Categorize the text into one of the following categories: {categories_str}.
                
                Output format:
                Summary: [Your summary here]
                Category: [One of the categories]
                
                Text:
                {item.original_text or item.original_title}
                """
                
                logger.info("Summarizing and categorizing item %s", item.source_id)
                summary_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant. Follow the output format strictly."},
                        {"role": "user", "content": prompt}
                    ]
                )
                content = summary_response.choices[0].message.content.strip()
                
                # 解析响应
                summary = ""
                category = "其他"
                
                for line in content.split('\n'):
                    if line.startswith("Summary:"):
                        summary = line.replace("Summary:", "").strip()
                    elif line.startswith("Category:"):
                        cat = line.replace("Category:", "").strip()
                        if cat in settings.NEWS_CATEGORIES:
                            category = cat
                            
                item.summary_cn = summary
                item.category = category
            else:
                # 对于简短的内容，仅根据标题进行分类
                categories_str = ", ".join(settings.NEWS_CATEGORIES)
                prompt = f"""
                Categorize the following title into one of these categories: {categories_str}.
                Return ONLY the category name.
                
                Title: {item.title_cn}
                """
                
                logger.info("Classifying short item %s", item.source_id)
                cat_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a classifier. Return only the category name."},
                        {"role": "user", "content": prompt}
                    ]
                )
                category = cat_response.choices[0].message.content.strip()
                if category in settings.NEWS_CATEGORIES:
                    item.category = category
                else:
                    item.category = "其他"
            
        except Exception as e:
            logger.exception("Error processing item %s", item.id or item.source_id)
            item.title_cn = item.original_title # 回退

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
            item.embedding = embedding_service.get_embedding(text_to_embed)
        except Exception as e:
            logger.exception("Error generating embedding for item %s", item.id or item.source_id)

        return item

    def _is_ai_related(self, item: RawItem) -> bool:
        """Use the LLM to determine whether the content is AI-related."""
        text = item.original_title
        if item.original_text:
            text += f"\n\n{item.original_text[:500]}"

        prompt = f"""
        你是 AI 新闻过滤器。请判断下述内容是否与“人工智能、AI 工具、AI 产业、AI 研究”密切相关。
        如果相关，回答 YES；如果只是泛泛的科技/商业/生活信息，请回答 NO。
        只需返回 YES 或 NO。

        内容：
        {text}
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an AI relevance classifier. Reply with YES or NO."},
                    {"role": "user", "content": prompt},
                ],
            )
            verdict = response.choices[0].message.content.strip().upper()
            return verdict.startswith("Y")
        except Exception:
            logger.exception("Failed to judge AI relevance for item %s", item.source_id)
            return True

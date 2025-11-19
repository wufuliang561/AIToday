from openai import OpenAI
from app.core.config import settings
from app.models.item import RawItem

class Processor:
    def __init__(self):
        self.client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL
        ) if settings.OPENAI_API_KEY else None
        self.model = settings.OPENAI_MODEL

    async def process_item(self, item: RawItem) -> RawItem:
        """
        将标题翻译成中文，并在需要时进行总结。
        """
        if not self.client:
            print("Warning: OpenAI client not initialized.")
            item.title_cn = item.original_title # 回退
            return item

        try:
            # 翻译标题
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
            print(f"Error processing item {item.id}: {e}")
            item.title_cn = item.original_title # 回退

        return item

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
        Translate title to Chinese and summarize if needed.
        """
        if not self.client:
            print("Warning: OpenAI client not initialized.")
            item.title_cn = item.original_title # Fallback
            return item

        try:
            # Translate Title
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful translator. Translate the following text to Chinese. Only return the translated text."},
                    {"role": "user", "content": item.original_title}
                ]
            )
            item.title_cn = response.choices[0].message.content.strip()

            # Summarize if X (Twitter) or if content is long
            if item.source_platform == "x" or (item.original_text and len(item.original_text) > 200):
                summary_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "Summarize the following text into a single Chinese sentence."},
                        {"role": "user", "content": item.original_text or item.original_title}
                    ]
                )
                item.summary_cn = summary_response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error processing item {item.id}: {e}")
            item.title_cn = item.original_title # Fallback

        return item

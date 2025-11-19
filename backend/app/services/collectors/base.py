from abc import ABC, abstractmethod
from typing import List
from app.models.item import RawItem

class BaseCollector(ABC):
    @abstractmethod
    async def collect(self) -> List[RawItem]:
        """
        从源收集数据并返回 RawItem 对象列表。
        """
        pass

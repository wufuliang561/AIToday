from abc import ABC, abstractmethod
from typing import List
from app.models.item import RawItem

class BaseCollector(ABC):
    @abstractmethod
    async def collect(self) -> List[RawItem]:
        """
        Collect data from the source and return a list of RawItem objects.
        """
        pass

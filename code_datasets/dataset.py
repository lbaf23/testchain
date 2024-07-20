from abc import ABC, abstractmethod
from typing import List, Dict


class CodeDataset(ABC):
    @abstractmethod
    def __init__(self, data_range: List, select_data: List, **kwargs) -> None:
        pass

    @abstractmethod
    def get_data(self) -> List[Dict]:
        pass

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class ExternalServiceInterface(ABC):
    """Interface for external service communication."""
    
    @abstractmethod
    async def fetch_data(self, endpoint: str = None) -> Dict[str, Any]:
        """Fetch data from an external service."""
        pass

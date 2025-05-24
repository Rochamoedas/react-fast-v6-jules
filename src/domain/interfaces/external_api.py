from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

class IExternalAPI(ABC):
    @abstractmethod
    def fetch_data(self, 
                   source_name: str, 
                   params: Optional[Dict[str, Any]] = None
                   ) -> List[Dict[str, Any]]:
        '''
        Fetches data from an external API.
        'source_name' could map to a specific URL or configuration in config.py.
        Returns a list of records (dictionaries).
        '''
        pass

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

    @abstractmethod
    def fetch_production_data_monthly(self, 
                                      year: int, 
                                      month: int, 
                                      params: Optional[Dict[str, Any]] = None
                                      ) -> List[Dict[str, Any]]:
        '''
        Fetches monthly production data from an external API for a specific year and month.
        'year' and 'month' specify the period.
        'params' can include additional filters or query parameters.
        Returns a list of records (dictionaries).
        '''
        pass

from abc import ABC, abstractmethod
from typing import List, TypeVar, Generic, Optional, Any, Dict
from datetime import date

# Import domain entities for type hinting
from src.domain.entities.well import Well
from src.domain.entities.field import Field
from src.domain.entities.production import Production
from src.domain.entities.oil_price import OilPrice
from src.domain.entities.exchange_rate import ExchangeRate

T = TypeVar('T') # Generic type for entities

class IRepository(Generic[T], ABC):
    @abstractmethod
    def add(self, entity: T) -> T:
        pass

    @abstractmethod
    def get(self, entity_id: Any) -> Optional[T]: # For single column PKs
        pass
    
    @abstractmethod
    def get_by_composite_key(self, key_values: Dict[str, Any]) -> Optional[T]: # For composite PKs
        pass

    @abstractmethod
    def list(self, filters: Optional[Dict[str, Any]] = None) -> List[T]:
        pass

    @abstractmethod
    def update(self, entity: T, entity_id: Any) -> T: # For single column PKs
        pass

    @abstractmethod
    def update_by_composite_key(self, entity: T, key_values: Dict[str, Any]) -> T: # For composite PKs
        pass

    @abstractmethod
    def delete(self, entity_id: Any) -> None: # For single column PKs
        pass

    @abstractmethod
    def delete_by_composite_key(self, key_values: Dict[str, Any]) -> None: # For composite PKs
        pass


class IWellRepository(IRepository[Well]):
    @abstractmethod
    def get_by_well_code(self, well_code: str) -> Optional[Well]:
        pass
    
    @abstractmethod
    def find_by_name(self, well_name: str) -> List[Well]:
        pass

    @abstractmethod
    def find_by_field_code(self, field_code: str) -> List[Well]:
        pass


class IFieldRepository(IRepository[Field]):
    @abstractmethod
    def get_by_field_code(self, field_code: str) -> Optional[Field]:
        pass

    @abstractmethod
    def find_by_name(self, field_name: str) -> List[Field]:
        pass


class IProductionRepository(IRepository[Production]):
    @abstractmethod
    def get_by_well_code_and_date(self, well_code: str, reference_date: date) -> Optional[Production]:
        pass

    @abstractmethod
    def find_by_well_code(self, well_code: str) -> List[Production]:
        pass
        
    @abstractmethod
    def find_by_date_range(self, start_date: date, end_date: date) -> List[Production]:
        pass


class IOilPriceRepository(IRepository[OilPrice]):
    @abstractmethod
    def get_by_field_code_and_date(self, field_code: str, reference_date: date) -> Optional[OilPrice]:
        pass

    @abstractmethod
    def find_by_field_code(self, field_code: str) -> List[OilPrice]:
        pass
    
    @abstractmethod
    def find_by_date_range(self, start_date: date, end_date: date) -> List[OilPrice]:
        pass


class IExchangeRateRepository(IRepository[ExchangeRate]):
    @abstractmethod
    def get_by_date(self, reference_date: date) -> Optional[ExchangeRate]: # Assuming reference_date is PK
        pass

    @abstractmethod
    def find_by_date_range(self, start_date: date, end_date: date) -> List[ExchangeRate]:

    @abstractmethod
    def find_by_well_code_and_date_range(self, well_code: str, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[Production]: ...
        pass

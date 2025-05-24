from abc import ABC, abstractmethod
from typing import List, TypeVar, Generic, Optional, Any, Dict, Protocol
from datetime import date

# Define TypeVars for Entities. We can't directly import from src.domain.entities
# due to potential circular dependencies if interfaces are also used by entities (though less common).
# For now, we'll use protocol-based definitions or Any for simplicity in the interface definitions.
# A more robust approach might involve a shared 'types' module if strict typing is paramount here.

class Entity(Protocol):
    # Define common attributes or methods if necessary, or leave as a generic marker
    pass

T = TypeVar('T', bound=Entity) # Generic type for entities

class IRepository(Generic[T], ABC):
    @abstractmethod
    def add(self, entity: T) -> T:
        pass

    @abstractmethod
    def get(self, entity_id: Any) -> Optional[T]: # ID could be int, str, etc.
        pass

    @abstractmethod
    def list(self, filters: Optional[Dict[str, Any]] = None) -> List[T]:
        pass

    @abstractmethod
    def update(self, entity: T) -> T:
        pass

    @abstractmethod
    def delete(self, entity_id: Any) -> None:
        pass

# Specific repository interfaces can extend the generic one if needed,
# or we can rely on the generic one and type hint appropriately at usage sites.
# For example, methods specific to certain entities:

class IProductionRepository(IRepository[Any]): # Replace 'Any' with 'Production' entity type later
    @abstractmethod
    def get_by_well_code_and_date(self, well_code: str, reference_date: date) -> Optional[Any]: # Production
        pass

    @abstractmethod
    def find_by_well_code(self, well_code: str) -> List[Any]: # List[Production]
        pass
        
    @abstractmethod
    def find_by_date_range(self, start_date: date, end_date: date) -> List[Any]: # List[Production]
        pass

class IOilPriceRepository(IRepository[Any]): # Replace 'Any' with 'OilPrice' entity type
    @abstractmethod
    def get_by_field_code_and_date(self, field_code: str, reference_date: date) -> Optional[Any]: # OilPrice
        pass

    @abstractmethod
    def find_by_field_code(self, field_code: str) -> List[Any]: # List[OilPrice]
        pass

class IWellRepository(IRepository[Any]): # Well entity
    @abstractmethod
    def get_by_well_code(self, well_code: str) -> Optional[Any]: # Well
        pass

# Add other specific repository interfaces as needed (Field, ExchangeRate)

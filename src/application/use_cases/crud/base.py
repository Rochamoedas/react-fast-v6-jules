# src/application/use_cases/crud/base.py
from typing import TypeVar, Generic, Type, Optional, List, Dict, Any, Protocol
from pydantic import BaseModel

# --- Generic Type Variables ---
Entity = TypeVar('Entity') # Represents a domain entity (Pydantic model or dataclass)
RequestDTO = TypeVar('RequestDTO', bound=BaseModel) # Request DTO, typically a Pydantic model
ResponseDTO = TypeVar('ResponseDTO', bound=BaseModel) # Response DTO, typically a Pydantic model
RepositoryInterface = TypeVar('RepositoryInterface') # Repository interface
IdentifierType = TypeVar('IdentifierType') # Type of the entity's identifier (e.g., int, str, UUID)

# --- Protocol for Entities that can be created from DTOs ---
# This is not strictly enforced by CreateUseCase yet but good for clarity
class CreatableFromDTO(Protocol[RequestDTO]):
    def __init__(self, **data: Any): ...

# --- Protocol for Response DTOs that can be created from Entities ---
class FromEntityResponse(Protocol[Entity]):
    @classmethod
    def from_entity(cls, entity: Entity) -> 'FromEntityResponse': ...


# --- Base Use Case ---
class BaseUseCase(Generic[RepositoryInterface]):
    def __init__(self, repository: RepositoryInterface):
        self.repository = repository

# --- CRUD Use Cases ---
class CreateUseCase(BaseUseCase[RepositoryInterface], Generic[Entity, RequestDTO, ResponseDTO, RepositoryInterface]):
    def __init__(self, 
                 repository: RepositoryInterface, 
                 entity_type: Type[Entity], 
                 response_dto_type: Type[ResponseDTO]):
        super().__init__(repository)
        self.entity_type = entity_type
        self.response_dto_type = response_dto_type

    def execute(self, dto: RequestDTO) -> ResponseDTO:
        # This is a simplified version. Pre-existence checks or more complex entity creation
        # might need to be handled in subclasses by overriding this method.
        entity_data = dto.model_dump()
        entity_to_create = self.entity_type(**entity_data) # type: ignore 
        # The type: ignore is because self.entity_type is Type[Entity] which is too generic
        # for Pydantic's ** unpack. A more specific Entity type hint might be needed if possible.

        created_entity = self.repository.add(entity_to_create) # type: ignore
        
        if hasattr(self.response_dto_type, 'from_entity'):
            return self.response_dto_type.from_entity(created_entity) # type: ignore
        else:
            # Fallback if from_entity is not available (though it's preferred)
            return self.response_dto_type(**created_entity.model_dump()) # type: ignore

class ReadUseCase(BaseUseCase[RepositoryInterface], Generic[Entity, ResponseDTO, RepositoryInterface, IdentifierType]):
    def __init__(self, 
                 repository: RepositoryInterface, 
                 response_dto_type: Type[ResponseDTO]):
        super().__init__(repository)
        self.response_dto_type = response_dto_type

    def execute(self, entity_id: IdentifierType) -> Optional[ResponseDTO]:
        # Assumes repository has a get_by_id method
        entity = self.repository.get_by_id(entity_id) # type: ignore
        if entity:
            if hasattr(self.response_dto_type, 'from_entity'):
                return self.response_dto_type.from_entity(entity) # type: ignore
            else:
                return self.response_dto_type(**entity.model_dump()) # type: ignore
        return None

class UpdateUseCase(BaseUseCase[RepositoryInterface], Generic[Entity, RequestDTO, ResponseDTO, RepositoryInterface, IdentifierType]):
    def __init__(self, 
                 repository: RepositoryInterface,
                 entity_type: Type[Entity], # Added entity_type for model_copy
                 response_dto_type: Type[ResponseDTO]):
        super().__init__(repository)
        self.entity_type = entity_type
        self.response_dto_type = response_dto_type

    def execute(self, entity_id: IdentifierType, dto: RequestDTO) -> Optional[ResponseDTO]:
        existing_entity = self.repository.get_by_id(entity_id) # type: ignore
        if not existing_entity:
            return None

        update_data = dto.model_dump(exclude_unset=True)
        
        # Ensure existing_entity is a Pydantic model for model_copy
        if not isinstance(existing_entity, BaseModel):
             # This might happen if repository returns a dict or other type.
             # For now, we assume it's a Pydantic model or compatible.
             # A more robust solution would involve converting it to self.entity_type first.
             # existing_entity = self.entity_type(**existing_entity) # If it's a dict
            pass

        updated_entity_instance = existing_entity.model_copy(update=update_data)
        
        persisted_entity = self.repository.update(updated_entity_instance) # type: ignore
        
        if hasattr(self.response_dto_type, 'from_entity'):
            return self.response_dto_type.from_entity(persisted_entity) # type: ignore
        else:
            return self.response_dto_type(**persisted_entity.model_dump()) # type: ignore

class DeleteUseCase(BaseUseCase[RepositoryInterface], Generic[RepositoryInterface, IdentifierType]):
    # No ResponseDTO or Entity needed here if it just deletes
    def __init__(self, repository: RepositoryInterface):
        super().__init__(repository)

    def execute(self, entity_id: IdentifierType) -> None:
        # Assumes repository has a delete method.
        # Some implementations might require fetching first to ensure existence,
        # which could be added here or in a subclass.
        # For simplicity, directly calling delete.
        self.repository.delete(entity_id) # type: ignore

class ListUseCase(BaseUseCase[RepositoryInterface], Generic[Entity, ResponseDTO, RepositoryInterface]):
    def __init__(self, 
                 repository: RepositoryInterface, 
                 response_dto_type: Type[ResponseDTO]):
        super().__init__(repository)
        self.response_dto_type = response_dto_type

    def execute(self, filters: Optional[Dict[str, Any]] = None) -> List[ResponseDTO]:
        entities: List[Entity] = self.repository.list(filters=filters) # type: ignore
        
        response_list = []
        for entity in entities:
            if hasattr(self.response_dto_type, 'from_entity'):
                response_list.append(self.response_dto_type.from_entity(entity)) # type: ignore
            else:
                response_list.append(self.response_dto_type(**entity.model_dump())) # type: ignore
        return response_list

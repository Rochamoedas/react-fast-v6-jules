# tests/presentation/test_api.py
import pytest
from fastapi.testclient import TestClient
from typing import List, Optional, Dict, Any

from src.main import app, get_field_repository # Assuming get_field_repository is the dependency provider
from src.domain.interfaces.repository import IFieldRepository
from src.domain.entities.field import Field
from src.application.dtos.response.field_response import FieldResponse

# Mock Field Repository
class MockFieldRepository(IFieldRepository):
    def __init__(self, initial_fields: Optional[List[Field]] = None):
        self._fields: Dict[str, Field] = {}
        if initial_fields:
            for field in initial_fields:
                # Assuming field_code is the primary key for Field entity
                self._fields[field.field_code] = field

    def add(self, entity: Field) -> Field:
        self._fields[entity.field_code] = entity
        return entity

    def get(self, entity_id: Any) -> Optional[Field]: # Generic get by PK
        return self._fields.get(str(entity_id))

    def get_by_field_code(self, field_code: str) -> Optional[Field]:
        return self._fields.get(field_code)
    
    def get_by_composite_key(self, key_values: Dict[str, Any]) -> Optional[Field]:
        # Not applicable for Field entity as it has a single PK
        raise NotImplementedError

    def list(self, filters: Optional[Dict[str, Any]] = None) -> List[Field]:
        if not filters:
            return list(self._fields.values())
        
        # Simple filtering for testing
        results = []
        for field in self._fields.values():
            match = True
            for key, value in filters.items():
                if not hasattr(field, key) or getattr(field, key) != value:
                    match = False
                    break
            if match:
                results.append(field)
        return results

    def update(self, entity: Field, entity_id: Any) -> Field: # Matches IRepository
        if entity_id in self._fields:
            self._fields[str(entity_id)] = entity
            return entity
        raise ValueError("Field not found for update") # Or return None / specific exception

    def update_by_composite_key(self, entity: Field, key_values: Dict[str, Any]) -> Field:
        raise NotImplementedError

    def delete(self, entity_id: Any) -> None: # Matches IRepository
        if str(entity_id) in self._fields:
            del self._fields[str(entity_id)]
            return
        # Optionally raise error if not found, or do nothing
        
    def delete_by_composite_key(self, key_values: Dict[str, Any]) -> None:
        raise NotImplementedError

    def find_by_name(self, field_name: str) -> List[Field]:
        return [f for f in self._fields.values() if f.field_name == field_name]


@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_field_repo_with_data():
    # Pre-populate with some data for GET tests
    initial_data = [
        Field(field_code="TF01", field_name="Test Field Alpha"),
        Field(field_code="TF02", field_name="Test Field Beta"),
        Field(field_code="TF03", field_name="Another Test Field"),
    ]
    return MockFieldRepository(initial_fields=initial_data)

def test_list_fields_no_filter(client: TestClient, mock_field_repo_with_data: MockFieldRepository):
    """
    Tests GET /fields/ endpoint without any filters.
    """
    # Override the dependency for IFieldRepository
    app.dependency_overrides[get_field_repository] = lambda: mock_field_repo_with_data
    
    response = client.get("/fields/")
    
    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 3
    assert response_data[0]["field_code"] == "TF01"
    assert response_data[1]["field_name"] == "Test Field Beta"
    
    # Clean up dependency override
    app.dependency_overrides.clear()


def test_list_fields_with_name_filter(client: TestClient, mock_field_repo_with_data: MockFieldRepository):
    """
    Tests GET /fields/?field_name=Test Field Alpha
    """
    app.dependency_overrides[get_field_repository] = lambda: mock_field_repo_with_data
    
    response = client.get("/fields/?field_name=Test Field Alpha")
    
    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 1
    assert response_data[0]["field_code"] == "TF01"
    assert response_data[0]["field_name"] == "Test Field Alpha"
    
    app.dependency_overrides.clear()

def test_read_field_by_code_found(client: TestClient, mock_field_repo_with_data: MockFieldRepository):
    """
    Tests GET /fields/{field_code} when field exists.
    """
    app.dependency_overrides[get_field_repository] = lambda: mock_field_repo_with_data
    
    response = client.get("/fields/TF02")
    
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["field_code"] == "TF02"
    assert response_data["field_name"] == "Test Field Beta"
    
    app.dependency_overrides.clear()

def test_read_field_by_code_not_found(client: TestClient, mock_field_repo_with_data: MockFieldRepository):
    """
    Tests GET /fields/{field_code} when field does not exist.
    """
    app.dependency_overrides[get_field_repository] = lambda: mock_field_repo_with_data
    
    response = client.get("/fields/TFNONEXIST")
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Field not found" # Matches HTTPException in main.py
    
    app.dependency_overrides.clear()

# Example of a POST test (can be expanded)
def test_create_field_api(client: TestClient):
    """
    Tests POST /fields/ to create a new field.
    """
    # Use a fresh mock repository for POST to avoid side effects from other tests
    mock_repo = MockFieldRepository()
    app.dependency_overrides[get_field_repository] = lambda: mock_repo
    
    field_data = {"field_code": "TFNEW", "field_name": "New Test Field"}
    response = client.post("/fields/", json=field_data)
    
    assert response.status_code == 201 # Created
    response_data = response.json()
    assert response_data["field_code"] == field_data["field_code"]
    assert response_data["field_name"] == field_data["field_name"]
    
    # Verify it was added to our mock repo
    assert mock_repo.get_by_field_code("TFNEW") is not None
    assert mock_repo.get_by_field_code("TFNEW").field_name == "New Test Field" # type: ignore
    
    app.dependency_overrides.clear()

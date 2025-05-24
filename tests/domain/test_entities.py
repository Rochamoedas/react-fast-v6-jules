# tests/domain/test_entities.py
import pytest
from src.domain.entities.well import Well
from datetime import date

def test_create_well_entity():
    """
    Tests the instantiation and attribute assignment of a Well entity.
    """
    data = {
        "well_code": "W001",
        "well_name": "Test Well Alpha",
        "field_name": "Test Field",
        "field_code": "F01"
        # Assuming other fields like spud_date, completion_date, status are optional or not tested here
    }
    
    well = Well(**data)
    
    assert well.well_code == data["well_code"]
    assert well.well_name == data["well_name"]
    assert well.field_name == data["field_name"]
    assert well.field_code == data["field_code"]

def test_well_entity_missing_required_field():
    """
    Tests that Pydantic raises an error if a required field is missing.
    """
    data = {
        "well_name": "Test Well Beta", # Missing well_code
        "field_name": "Another Field",
        "field_code": "F02"
    }
    with pytest.raises(ValueError): # Pydantic v1 raises ValueError, v2 ValidationError
        Well(**data)

# Add more entity tests as needed, e.g., for Field, Production etc.
# For example:
from src.domain.entities.field import Field
def test_create_field_entity():
    data = {"field_name": "Test Field", "field_code": "TF01"}
    field_obj = Field(**data)
    assert field_obj.field_name == data["field_name"]
    assert field_obj.field_code == data["field_code"]

from src.domain.entities.production import Production
def test_create_production_entity():
    data = {
        "reference_date": date(2023, 1, 1),
        "oil_prod": 100.0,
        "gas_prod": 50.0,
        "water_prod": 20.0,
        "well_code": "WXYZ"
    }
    prod = Production(**data)
    assert prod.reference_date == data["reference_date"]
    assert prod.oil_prod == data["oil_prod"]
    assert prod.well_code == data["well_code"]

def test_production_entity_negative_values():
    data = {
        "reference_date": date(2023,1,1),
        "oil_prod": -10.0, # Invalid
        "gas_prod": 50.0,
        "water_prod": 20.0,
        "well_code": "WNEG"
    }
    with pytest.raises(ValueError): # Pydantic v1 raises ValueError, v2 ValidationError
        Production(**data)

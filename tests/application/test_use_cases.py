# tests/application/test_use_cases.py
import pytest
from unittest.mock import MagicMock
from src.application.use_cases.crud.create_well import CreateWellUseCase
from src.application.dtos.request.well_request import WellRequest
from src.application.dtos.response.well_response import WellResponse
from src.domain.entities.well import Well
from src.domain.interfaces.repository import IWellRepository

def test_create_well_use_case():
    """
    Tests the CreateWellUseCase.
    """
    # 1. Create a mock for IWellRepository
    mock_well_repo = MagicMock(spec=IWellRepository)
    
    # 2. Sample request data
    request_data = WellRequest(
        well_code="W002",
        well_name="Mock Test Well",
        field_name="Mock Field",
        field_code="MF01"
    )
    
    # 3. Expected Well entity that the repository should receive and return
    expected_well_entity = Well(
        well_code=request_data.well_code,
        well_name=request_data.well_name,
        field_name=request_data.field_name,
        field_code=request_data.field_code
    )
    
    # 4. Configure the mock repository's `add` method
    #    It should return the entity that was "added"
    mock_well_repo.add.return_value = expected_well_entity
    
    # 5. Instantiate CreateWellUseCase with the mock repository
    use_case = CreateWellUseCase(well_repository=mock_well_repo)
    
    # 6. Execute the use case
    response = use_case.execute(request_data)
    
    # 7. Assert that the repository's `add` method was called once
    #    The argument passed to `add` should match our expected_well_entity.
    #    Pydantic models are compared by their values if they are BaseModel instances.
    mock_well_repo.add.assert_called_once()
    
    # To assert the argument, you can access it from call_args
    # call_args is a tuple: (args, kwargs). We want the first positional arg.
    called_with_entity = mock_well_repo.add.call_args[0][0]
    assert called_with_entity == expected_well_entity
    
    # 8. Assert that the result from the use case matches the expected WellResponse structure
    assert isinstance(response, WellResponse)
    assert response.well_code == expected_well_entity.well_code
    assert response.well_name == expected_well_entity.well_name
    assert response.field_name == expected_well_entity.field_name
    assert response.field_code == expected_well_entity.field_code

# Add more use case tests as needed.
# For example, for ReadWellUseCase:
from src.application.use_cases.crud.read_well import ReadWellUseCase
def test_read_well_use_case_found():
    mock_well_repo = MagicMock(spec=IWellRepository)
    well_code_to_find = "WEXISTS"
    expected_well = Well(well_code=well_code_to_find, well_name="Existing Well", field_name="F", field_code="F01")
    
    mock_well_repo.get_by_well_code.return_value = expected_well
    
    use_case = ReadWellUseCase(well_repository=mock_well_repo)
    response = use_case.execute(well_code_to_find)
    
    mock_well_repo.get_by_well_code.assert_called_once_with(well_code_to_find)
    assert isinstance(response, WellResponse)
    assert response.well_code == well_code_to_find

def test_read_well_use_case_not_found():
    mock_well_repo = MagicMock(spec=IWellRepository)
    well_code_to_find = "WNOTEXISTS"
    
    mock_well_repo.get_by_well_code.return_value = None # Simulate not found
    
    use_case = ReadWellUseCase(well_repository=mock_well_repo)
    response = use_case.execute(well_code_to_find)
    
    mock_well_repo.get_by_well_code.assert_called_once_with(well_code_to_find)
    assert response is None

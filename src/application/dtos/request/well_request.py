from pydantic import BaseModel

class WellRequest(BaseModel):
    well_code: str
    well_name: str # Added well_name
    field_name: str
    field_code: str

from pydantic import BaseModel

class Well(BaseModel):
    well_code: str
    well_name: str # Added well_name
    field_name: str
    field_code: str

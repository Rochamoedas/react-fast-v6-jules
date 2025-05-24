from pydantic import BaseModel

class WellRequest(BaseModel):
    well_code: str
    field_name: str
    field_code: str

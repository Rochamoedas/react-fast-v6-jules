from pydantic import BaseModel

class Well(BaseModel):
    well_code: str
    field_name: str
    field_code: str

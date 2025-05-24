from pydantic import BaseModel

class Field(BaseModel):
    field_name: str
    field_code: str

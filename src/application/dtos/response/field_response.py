# src/application/dtos/response/field_response.py
from pydantic import BaseModel

class FieldResponse(BaseModel):
    field_name: str
    field_code: str

# src/application/dtos/request/field_request.py
from pydantic import BaseModel

class FieldRequest(BaseModel):
    field_name: str
    field_code: str

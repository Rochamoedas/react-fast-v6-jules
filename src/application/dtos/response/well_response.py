from pydantic import BaseModel
from typing import Optional, Any

class WellResponse(BaseModel):
    well_code: str
    field_name: str
    field_code: str
    # id: Optional[Any] = None # If we decide to expose a database ID

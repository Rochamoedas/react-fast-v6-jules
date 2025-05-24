from datetime import date
from pydantic import BaseModel

class DateVO(BaseModel):
    value: date

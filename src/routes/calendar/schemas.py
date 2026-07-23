from pydantic import BaseModel
from datetime import date
from typing import Optional

class EventResponse(BaseModel):
    id: int
    title: str
    scheduled_to: date
    description: Optional[str] = None

    class Config:
        from_attributes = True
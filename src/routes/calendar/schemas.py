from pydantic import BaseModel, ConfigDict
from datetime import date
from typing import Optional


class EventCreate(BaseModel):
    title: str
    scheduled_to: date
    description: Optional[str] = None

class EventUpdate(BaseModel):
    title: Optional[str] = None
    scheduled_to: Optional[date] = None
    description: Optional[str] = None

class EventResponse(BaseModel):
    id: int
    title: str
    scheduled_to: date
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
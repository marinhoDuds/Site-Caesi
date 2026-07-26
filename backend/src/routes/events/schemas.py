"""
Pydantic schemas for Event (Calendar) endpoints.
"""
from pydantic import BaseModel, Field
from typing import Optional


class EventBase(BaseModel):
    title: str = Field(..., description="Event title")
    scheduled_to: str = Field(..., description="Date the event is scheduled for (YYYY-MM-DD)")
    start_time: Optional[str] = Field(None, description="Start time (HH:MM)")
    end_time: Optional[str] = Field(None, description="End time (HH:MM)")
    location: Optional[str] = Field(None, description="Event location")
    category: Optional[str] = Field("CAESI", description="Event category: CAESI or Acadêmico")
    description: Optional[str] = Field("", description="Short description of the event")
    formulario_id: Optional[int] = Field(None, description="Linked form ID")


class EventCreate(EventBase):
    pass


class EventUpdate(EventBase):
    pass


class EventResponse(EventBase):
    id: int

    class Config:
        from_attributes = True

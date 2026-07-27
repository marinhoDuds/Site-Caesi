from datetime import date
from typing import Optional, Union
from pydantic import BaseModel, ConfigDict, Field, model_validator


class EventBase(BaseModel):
    title: str = Field(..., description="Event title")
    scheduled_to: Union[date, str] = Field(..., description="Date the event is scheduled for (YYYY-MM-DD)")
    start_time: Optional[str] = Field(None, description="Start time (HH:MM)")
    end_time: Optional[str] = Field(None, description="End time (HH:MM)")
    location: Optional[str] = Field(None, description="Event location")
    category: Optional[str] = Field("CAESI", description="Event category: CAESI or Acadêmico")
    description: Optional[str] = Field("", description="Short description of the event")
    formulario_id: Optional[int] = Field(None, description="Linked form ID")

    @model_validator(mode="after")
    def validate_time_range(self) -> "EventBase":
        if self.start_time and self.end_time and self.start_time > self.end_time:
            raise ValueError("Data/hora inicial não pode ser posterior à data/hora final")
        return self


class EventCreate(EventBase):
    pass


class EventUpdate(EventBase):
    pass


class EventResponse(EventBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

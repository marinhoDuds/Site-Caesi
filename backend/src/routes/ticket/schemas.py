from pydantic import BaseModel, ConfigDict
from typing import Optional
from enum import Enum


class TicketType(str, Enum):
    classmates = "classmates"
    infrastructure = "infrastructure"
    professors = "professors"
    schedules = "schedules"
    student_groups = "student_groups"
    subjects = "subjects"
    other = "other"


class TicketBase(BaseModel):
    semester: str
    content: str
    ticket_type: TicketType
    author: Optional[str] = None
    email: Optional[str] = None


class TicketCreate(TicketBase):
    pass


class TicketUpdate(BaseModel):
    content: Optional[str] = None
    ticket_type: Optional[TicketType] = None
    semester: Optional[str] = None


class TicketResponse(TicketBase):
    id: int
    public_id: str
    protocol: str
    
    model_config = ConfigDict(from_attributes=True)

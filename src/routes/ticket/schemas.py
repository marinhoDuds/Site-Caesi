from pydantic import BaseModel, Field, EmailStr, ConfigDict
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


class TicketCreate(BaseModel):
    semester: str = Field(..., max_length=4)
    content: str = Field(..., min_length=1, description="A mensagem do relato não pode ser vazia.")
    ticket_type: TicketType
    author: Optional[str] = Field(None, max_length=120)
    email: Optional[EmailStr] = None


class TicketResponse(BaseModel):
    id: int
    public_id: str
    protocol: str
    semester: str
    content: str
    ticket_type: TicketType
    author: Optional[str] = None
    email: Optional[EmailStr] = None

    model_config = ConfigDict(from_attributes=True)
from enum import Enum
from pydantic import BaseModel, ConfigDict
from typing import Optional


class InformationTypeEnum(str, Enum):
    announcements = 'announcements'
    laboratories = 'laboratories'
    map = 'map'
    professors = 'professors'
    tamburetei = 'tamburetei'


class InformationCreate(BaseModel):
    content: str
    information_type: InformationTypeEnum


class InformationUpdate(BaseModel):
    content: Optional[str] = None
    information_type: Optional[InformationTypeEnum] = None


class InformationResponse(BaseModel):
    id: int
    content: str
    information_type: InformationTypeEnum
    attachment_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
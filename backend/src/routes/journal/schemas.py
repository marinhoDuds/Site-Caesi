from datetime import date
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class PostType(str, Enum):
    aviso = "aviso"
    evento = "evento"
    vaga = "vaga"
    oportunidade = "oportunidade"


class PostCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    post_type: str = Field(..., max_length=100)
    caption: str = Field(..., min_length=10, max_length=2200)


class PostUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    post_type: Optional[str] = Field(None, max_length=100)
    caption: Optional[str] = Field(None, min_length=10, max_length=2200)


class AttachmentInfo(BaseModel):
    id: int
    filename: str
    content_type: str
    url: str


class PostResponse(BaseModel):
    id: int
    title: str
    post_type: str
    caption: str
    created_at: date
    updated_at: Optional[date] = None
    attachments: list[AttachmentInfo] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

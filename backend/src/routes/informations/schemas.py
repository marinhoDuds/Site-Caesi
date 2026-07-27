from pydantic import BaseModel, ConfigDict, Field

class InformationBase(BaseModel):
    information_type: str = Field(..., description="Type of the information (e.g., announcements, laboratories, professors, tamburetei)")
    content: str = Field(..., description="JSON serialized content of the information")

class InformationCreate(InformationBase):
    pass

class InformationUpdate(InformationBase):
    pass

class InformationResponse(InformationBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import date
from enum import Enum


class OperationType(str, Enum):
    aid = "aid"
    events = "events"
    incomes = "incomes"
    infrastructure = "infrastructure"
    procurement = "procurement"
    reimbursement = "reimbursement"
    other = "other"


class OperationBase(BaseModel):
    value: float
    description: str
    operation_type: OperationType


class OperationCreate(OperationBase):
    pass


class OperationResponse(OperationBase):
    id: int
    created_at: date
    previous: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class OperationHistoryResponse(OperationResponse):
    history: List[OperationResponse] = []

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class Message (BaseModel):
    id: int
    text: str
    timestamp: datetime
    report_id: Optional[int] = None

class MessageResponse (BaseModel):
    messages: list[Message]

class ReportResponse (BaseModel):
    name: str
    credit_cost: Decimal

class UsageItem (BaseModel):
    model_config = ConfigDict(extra="forbid")

    message_id: int
    timestamp: str
    report_name: Optional[str] = None
    credits_used: float = Field(..., ge=0.0)

class UsageResponse (BaseModel):
    usage: list[UsageItem]
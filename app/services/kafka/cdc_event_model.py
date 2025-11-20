from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime


class CdcEvent(BaseModel):
    database: str
    table: str
    operation: str
    before: Optional[Any]
    after: Optional[Any]
    sourceTimestamp: datetime

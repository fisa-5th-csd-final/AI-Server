from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Optional
from app.services.llm_service_spending import generate_spending_comment

router = APIRouter()

class SpendingInsightRequest(BaseModel):
    salary: float = Field(..., description="월 소득")
    spending: Dict[str, float] = Field(..., description="카테고리별 소비 금액")
    prev_spending: Optional[Dict[str, float]] = Field(None, description="전월 소비 금액")

class SpendingInsightResponse(BaseModel):
    comment: str
    model_version: str

@router.post("/insight/spending", response_model=SpendingInsightResponse)
def insight_spending(request: SpendingInsightRequest):
    try:
        comment = generate_spending_comment(request.salary, request.spending, request.prev_spending)
        return SpendingInsightResponse(comment=comment, model_version="phi3-mini-4k-instruct")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

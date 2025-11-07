from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Optional
from app.services.llm_service_spending import generate_spending_comment

router = APIRouter()

class SpendingInsightRequest(BaseModel):
    spending_data: Dict[str, float] = Field(..., description="사용자 카테고리별 소비 금액 (income 포함)")
    avg_spending_data: Dict[str, float] = Field(..., description="또래 평균 카테고리별 소비 금액")
    peer_age: Optional[str] = Field("20대 후반", description="또래 연령대")
    peer_income_range: Optional[str] = Field("월 300~400만 원대", description="또래 소득 구간")

class SpendingInsightResponse(BaseModel):
    comment: str
    model_version: str

@router.post("/insight/spending", response_model=SpendingInsightResponse)
def insight_spending(request: SpendingInsightRequest):
    try:
        comment = generate_spending_comment(
            spending_data=request.spending_data,
            avg_spending_data=request.avg_spending_data,
            peer_age=request.peer_age,
            peer_income_range=request.peer_income_range
        )
        return SpendingInsightResponse(
            comment=comment,
            model_version="phi3-mini-4k-instruct"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

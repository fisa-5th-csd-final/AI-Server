from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.services.llm_service_loan import generate_loan_comment

router = APIRouter()

class LoanInsightRequest(BaseModel):
    loan_name: str = Field(..., description="대출 상품명 (예: 농협주택대출)")
    interest_rate: float = Field(..., description="금리(%)")
    repayment_ratio: float = Field(..., description="상환진척률(%)")
    delinquency_probability: float = Field(..., description="모델 예측 연체 확률 (0~1)")
    next_due_date: str = Field(..., description="다음 납입일 (YYYY-MM-DD)")
    remaining_principal: float = Field(..., description="남은 원금")
    principal_amount: float = Field(..., description="대출 총 원금")

class LoanInsightResponse(BaseModel):
    comment: str
    model_version: str

@router.post("/insight/loan", response_model=LoanInsightResponse)
def insight_loan(request: LoanInsightRequest):
    try:
        comment = generate_loan_comment(request.model_dump())
        return LoanInsightResponse(comment=comment, model_version="phi3-mini-4k-instruct")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

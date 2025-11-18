from pydantic import BaseModel, Field


class LoanRiskItem(BaseModel):
    loan_ledger_id: int = Field(..., description="대출 원장 ID")
    risk: float = Field(..., description="해당 대출의 연체 확률 (0~1)")
    explanation: str = Field(..., description="LLM 한줄 코멘트")


class UserPredictResponse(BaseModel):
    overall_risk: float = Field(..., description="사용자의 전체 평균 위험도 (0~1)")
    loans: list[LoanRiskItem] = Field(..., description="사용자가 보유한 각 대출의 연체 위험도 리스트")
    model_version: str = Field(..., description="사용된 모델 버전 (예: v1.0)")

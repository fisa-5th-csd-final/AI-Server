from pydantic import BaseModel, Field
from decimal import Decimal
from typing import List

class ExtraChange(BaseModel):
    type: str = Field(..., description="변화 유형 (income=수입, expense=지출)")
    name: str = Field(..., description="항목명 (예: 부업, 관리비, 여행)")
    amount: Decimal = Field(..., description="금액 (원 단위)")


class SimulationRequest(BaseModel):
    user_id: int = Field(..., description="시뮬레이션 대상 사용자 ID")
    changes: List[ExtraChange] = Field(
        ..., 
        description="수입/지출 변화 리스트"
    )


class SimulationResponse(BaseModel):
    base_risk_score: float = Field(..., description="기존 위험도 (0~1)")
    simulated_risk_score: float = Field(..., description="변경 적용 후 위험도 (0~1)")
    delta: float = Field(..., description="위험도 변화량 (양수=상승, 음수=하락)")
    explanation: str = Field(..., description="변동에 따른 요약 설명")

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }

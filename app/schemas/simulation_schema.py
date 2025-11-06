# app/schemas/simulation_schema.py
from pydantic import BaseModel, Field
from decimal import Decimal
from typing import List
from app.schemas.predict_schema import PredictRequest

class ExtraChange(BaseModel):
    type: str = Field(..., description="변화 유형 (income=수입, expense=지출)")
    name: str = Field(..., description="항목명 (예: 해외여행, 상여금)")
    amount: Decimal = Field(..., description="금액 (원 단위)")

class SimulationRequest(BaseModel):
    model_input: PredictRequest = Field(..., description="모델 입력 데이터")
    changes: List[ExtraChange] = Field(..., description="소득/지출 변화 리스트")


class SimulationResponse(BaseModel):
    base_risk_score: float = Field(..., description="기존 위험도 (0~1)")
    simulated_risk_score: float = Field(..., description="시뮬레이션 적용 후 위험도 (0~1)")
    delta: float = Field(..., description="위험도 변화량 (양수=상승, 음수=하락)")
    explanation: str = Field(..., description="상황에 대한 간단한 설명")

# 모델이 JSON으로 직렬화될 때 Decimal을 float으로 변환
class Config:
        json_encoders = {Decimal: lambda v: float(v)}
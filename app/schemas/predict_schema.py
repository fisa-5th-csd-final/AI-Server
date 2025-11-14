from pydantic import BaseModel, Field
from typing import Optional

class PredictResponse(BaseModel):
    delinquency_probability: float = Field(
        ..., description="연체 확률 (0~1)"
    )
    delinquency_label: int = Field(
        ..., description="예측 결과 (0=정상, 1=위험)"
    )
    threshold: float = Field(
        ..., description="모델에서 사용한 임계값"
    )
    model_version: str = Field(
        ..., description="모델 버전 정보"
    )
    explanation: str = Field(
        ..., description="간단한 위험 설명 텍스트"
    )

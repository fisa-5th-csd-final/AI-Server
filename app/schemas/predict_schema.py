from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal

class PredictRequest(BaseModel):
    BAS_YH: str = Field(..., description="기준 분기 (예: 2022Q2)")
    AGE: int = Field(..., description="고객 나이")
    SEX_CD: int = Field(..., description="성별 코드 (1=남, 2=여)")
    MBR_RK: int = Field(..., description="회원 등급 코드")

    # 소비 관련
    TOT_USE_AM: Decimal
    CRDSL_USE_AM: Decimal
    CNF_USE_AM: Decimal
    INTERIOR_AM: Decimal
    INSUHOS_AM: Decimal
    OFFEDU_AM: Decimal
    TRVLEC_AM: Decimal
    FSBZ_AM: Decimal
    SVCARC_AM: Decimal
    DIST_AM: Decimal
    PLSANIT_AM: Decimal
    CLOTHGDS_AM: Decimal
    AUTO_AM: Decimal

    # 재무 관련
    salary: Decimal
    balance: Decimal
    loan_type: int
    principal_amount: Decimal
    remaining_principal: Decimal
    interest_rate: Decimal
    interest_type: int
    repayment_method: int
    repayment_date: Optional[str] = Field(None, description="상환일자(YYYY-MM-DD)")
    is_completed: int
    quarter_order: int

    # 증감률 관련
    salary_diff: Decimal = Decimal("0.0")
    salary_pct_change: Decimal = Decimal("0.0")
    balance_diff: Decimal = Decimal("0.0")
    balance_pct_change: Decimal = Decimal("0.0")
    principal_amount_diff: Decimal = Decimal("0.0")
    principal_amount_pct_change: Decimal = Decimal("0.0")
    remaining_principal_diff: Decimal = Decimal("0.0")
    remaining_principal_pct_change: Decimal = Decimal("0.0")

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)  # FastAPI가 JSON 직렬화 가능하도록 변환
        }

class PredictResponse(BaseModel):
    delinquency_probability: float = Field(..., description="연체 확률 (0~1)")
    delinquency_label: int = Field(..., description="예측 결과 (0=정상, 1=위험)")
    threshold: float = Field(..., description="적용된 임계값")
    model_version: str = Field(..., description="모델 버전")
    explanation: str = Field(..., description="간단한 위험도 설명")

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }

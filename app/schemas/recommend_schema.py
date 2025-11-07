from pydantic import BaseModel, Field
from typing import Optional, List
from decimal import Decimal

class SpendingData(BaseModel):
    interior_am: Optional[Decimal] = Field(None, description="인테리어 관련 지출 금액")
    insuhos_am: Optional[Decimal] = Field(None, description="보험/병원 관련 지출 금액")
    offedu_am: Optional[Decimal] = Field(None, description="오프라인 교육 관련 지출 금액")
    trvlec_am: Optional[Decimal] = Field(None, description="여행/레저 관련 지출 금액")
    fsbz_am: Optional[Decimal] = Field(None, description="식비 관련 지출 금액")
    svcarc_am: Optional[Decimal] = Field(None, description="서비스/자동차 관련 지출 금액")
    plsanit_am: Optional[Decimal] = Field(None, description="생활용품/위생 관련 지출 금액")
    clothgds_am: Optional[Decimal] = Field(None, description="의류/패션 관련 지출 금액")
    auto_am: Optional[Decimal] = Field(None, description="자동차 관련 지출 금액")
    income: Optional[Decimal] = Field(None, description="월 소득 금액")


class RecommendRequest(BaseModel):
    spending_data: SpendingData = Field(
        ...,
        description="사용자의 소비 데이터 (각 항목별 금액 포함)"
    )
    avg_spending_data: Optional[SpendingData] = Field(
        ..., 
        description="평균 소비 데이터 (비교용)"
    )


class RecommendResponse(BaseModel):
    comment: str = Field(..., description="AI의 코멘트")

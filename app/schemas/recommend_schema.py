from pydantic import BaseModel, Field, condecimal
from typing import Dict, Optional
from decimal import Decimal

# 소수점 1자리로 고정된 비율 타입
RatioDecimal = condecimal(max_digits=4, decimal_places=1)   # 예: 0.0 ~ 9.9까지 표현


# ----------------------------------------------
# 사용자의 실제 소비 비율
# ----------------------------------------------
class SpendingRatio(BaseModel):
    categories: Dict[str, RatioDecimal] = Field(
        ...,
        description="사용자의 실제 소비 비율 (예: {'FOOD': 0.3, 'TRAVEL': 0.1})"
    )
    income: Optional[Decimal] = Field(
        None,
        description="사용자 월 소득 (원 단위). 비율 기반이므로 선택값"
    )


# ----------------------------------------------
# 사용자가 직접 설정한 한도 비율
# ----------------------------------------------
class UserLimitRatio(BaseModel):
    limits: Dict[str, RatioDecimal] = Field(
        ...,
        description="사용자가 설정한 카테고리별 소비 한도 비율 (예: {'FOOD': 0.2})"
    )


# ----------------------------------------------
# 요청 스키마
# ----------------------------------------------
class RecommendRequest(BaseModel):
    spending_ratio: SpendingRatio = Field(
        ...,
        description="사용자의 실제 소비 비율"
    )
    age_group_ratio: Dict[str, RatioDecimal] = Field(
        ...,
        description="해당 연령대의 바른 소비 비율 (예: {'FOOD': 0.2})"
    )
    user_limit_ratio: UserLimitRatio = Field(
        ...,
        description="사용자 설정 소비 한도 비율"
    )


# ----------------------------------------------
# 응답 스키마
# ----------------------------------------------
class RecommendResponse(BaseModel):
    comment: str = Field(
        ...,
        description="AI가 생성한 소비 패턴 분석 코멘트"
    )

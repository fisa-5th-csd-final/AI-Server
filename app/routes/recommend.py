from fastapi import APIRouter, HTTPException
from app.schemas.recommend_schema import RecommendRequest, RecommendResponse
from app.services.llm_service_spending import generate_spending_comment
import traceback
from decimal import Decimal

router = APIRouter()

def decimal_to_float_map(data: dict):
    """Decimal을 float로 변환해주는 유틸 (LLM 입력용)"""
    return {k: float(v) if isinstance(v, Decimal) else v for k, v in data.items()}


@router.post("/recommend", response_model=RecommendResponse)
def recommend(request: RecommendRequest):
    try:
        # 사용자 실제 소비 비율
        user_ratio = request.spending_ratio.categories
        income = request.spending_ratio.income

        # 연령대 바른 소비 비율
        age_group_ratio = request.age_group_ratio

        # 사용자가 설정한 한도 비율
        user_limit_ratio = request.user_limit_ratio.limits

        # Debug Logging
        print("사용자 소비 비율:", user_ratio)
        print("연령대 바른 소비 비율:", age_group_ratio)
        print("사용자 설정 소비 한도:", user_limit_ratio)
        print("사용자 소득:", income)

        # Decimal → float 변환 (LLM-friendly)
        user_ratio_f = decimal_to_float_map(user_ratio)
        age_group_ratio_f = decimal_to_float_map(age_group_ratio)
        user_limit_ratio_f = decimal_to_float_map(user_limit_ratio)

        income_f = float(income) if isinstance(income, Decimal) else income

        # LLM 분석 호출
        comment = generate_spending_comment(
            spending_ratio=user_ratio_f,
            age_group_ratio=age_group_ratio_f,
            user_limit_ratio=user_limit_ratio_f,
            income=income_f
        )

        print("생성된 코멘트:", comment)
        return RecommendResponse(comment=comment)

    except Exception as e:
        print("에러 발생:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"내부 서버 오류: {e}")

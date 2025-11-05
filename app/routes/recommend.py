from decimal import Decimal
from fastapi import APIRouter, HTTPException
from app.schemas.recommend_schema import RecommendRequest, RecommendResponse

router = APIRouter()

# 임시용 함수 — 나중에 llm_service로 분리 예정
def generate_recommendation(spending_data: dict):
    # None 값 제거 및 총 지출 계산
    total_spending = sum(
        (v for k, v in spending_data.items() if v is not None and k != "income"),
        Decimal("0")
    )

    income = spending_data.get("income") or Decimal("0")
    ratio = (total_spending / income * Decimal("100")) if income != Decimal("0") else Decimal("0")
    summary = f"총 지출은 {total_spending:,}원이며, 소득 대비 지출 비율은 약 {float(ratio):.1f}%입니다."

    recommendations = [
        "임시 추천: LLM 서비스가 준비되면 더 스마트한 결과를 보여드릴 예정입니다."
    ]
    comment = "이 결과는 더미 로직으로 생성되었습니다."

    return summary, recommendations, comment


@router.post("/recommend", response_model=RecommendResponse)
def recommend(request: RecommendRequest):
    try:
        summary, recs, comment = generate_recommendation(request.spending_data.model_dump())
        return RecommendResponse(summary=summary, recommendations=recs, comment=comment)
    except Exception as e:
        raise HTTPException(status_code=500, detail="내부 서버 오류가 발생했습니다.")

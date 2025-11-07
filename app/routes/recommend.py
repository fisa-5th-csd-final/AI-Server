from fastapi import APIRouter, HTTPException
from app.schemas.recommend_schema import RecommendRequest, RecommendResponse
from app.services.llm_service_spending import generate_spending_comment
import traceback

router = APIRouter()

@router.post("/recommend", response_model=RecommendResponse)
def recommend(request: RecommendRequest):
    try:
        # 요청 데이터 추출
        spending_data = request.spending_data.model_dump()
        avg_spending_data = request.avg_spending_data.model_dump() if request.avg_spending_data else {}

        print("입력 spending_data:", spending_data)
        print("입력 avg_spending_data:", avg_spending_data)

        # LLM 분석 호출
        comment = generate_spending_comment(
            spending_data=spending_data,
            avg_spending_data=avg_spending_data
        )

        print("생성된 코멘트:", comment)
        return RecommendResponse(comment=comment)

    except Exception as e:
        print("에러 발생:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"내부 서버 오류: {e}")

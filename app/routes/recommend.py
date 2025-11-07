from decimal import Decimal
from fastapi import APIRouter, HTTPException
from app.schemas.recommend_schema import RecommendRequest, RecommendResponse
from app.services.llm_service_spending import generate_spending_comment

router = APIRouter()

@router.post("/recommend", response_model=RecommendResponse)
def recommend(request: RecommendRequest):
    try:
        # 입력값에서 데이터 추출
        data = request.spending_data.model_dump()

        salary = float(data.get("income", 0))
        spending = {k: float(v) for k, v in data.items() if k not in ("income", None) and v is not None}

        # LLM으로 코멘트 생성
        comment = generate_spending_comment(salary=salary, spending=spending)

        return RecommendResponse(comment=comment)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail="내부 서버 오류가 발생했습니다.")

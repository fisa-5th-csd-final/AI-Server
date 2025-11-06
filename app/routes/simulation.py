from fastapi import APIRouter, HTTPException
from app.schemas.simulation_schema import SimulationRequest, SimulationResponse
from app.services.model_service import predict_risk
import logging
from decimal import Decimal

router = APIRouter()
logger = logging.getLogger(__name__)

# ExtraChange(소득/지출 변화)를 반영하여 모델 재추론을 통해 새로운 위험도를 계산
@router.post("/simulation", response_model=SimulationResponse)
def simulate_risk(request: SimulationRequest):
    try:
        logger.info("[/simulation] 시뮬레이션 요청 수신")

        # 기본 예측 수행
        base_result = predict_risk(request.model_input.model_dump())
        base_score = float(base_result["delinquency_probability"])
        logger.info(f"기본 연체확률: {base_score:.4f}")

        # 기존 입력 복사 및 변화 반영
        simulated_input = request.model_input.model_dump()

        # 변화 금액 계산 (원 단위)
        income_delta = sum(float(c.amount) for c in request.changes if c.type == "income")
        expense_delta = sum(float(c.amount) for c in request.changes if c.type == "expense")

        # 단위 변환: 원 → 천원
        income_delta_thousand = Decimal(str(income_delta)) / Decimal(1000)
        expense_delta_thousand = Decimal(str(expense_delta)) / Decimal(1000)

        logger.info(f"소득 변화(천원 단위): +{income_delta_thousand}, 지출 변화(천원 단위): +{expense_delta_thousand}")

        # 실제 모델 입력 필드명에 맞게 반영
        if "salary" in simulated_input:
            simulated_input["salary"] += income_delta_thousand
        if "TOT_USE_AM" in simulated_input:
            simulated_input["TOT_USE_AM"] += expense_delta_thousand

        # 모델 재추론 수행
        simulated_result = predict_risk(simulated_input)
        simulated_score = float(simulated_result["delinquency_probability"])
        logger.info(f"시뮬레이션 후 연체확률: {simulated_score:.4f}")

        # 변화량 계산
        delta = simulated_score - base_score
 
        # 설명 생성
        if delta > 0:
            explanation = f"지출 증가 또는 소득 감소로 연체 위험도가 {abs(delta)*100:.0f}% 상승했습니다."
        elif delta < 0:
            explanation = f"소득 증가 또는 지출 감소로 연체 위험도가 {abs(delta)*100:.0f}% 하락했습니다."
        else:
            explanation = "변화가 거의 없어 위험도는 동일합니다."

        # 응답 반환
        response = SimulationResponse(
            base_risk_score=base_score,
            simulated_risk_score=simulated_score,
            delta=delta,
            explanation=explanation,
        )

        logger.info(f"시뮬레이션 결과: {response.model_dump()}")
        return response

    except Exception as e:
        logger.exception(f"Simulation Error: {e}")
        raise HTTPException(status_code=500, detail=f"Simulation Error: {str(e)}")


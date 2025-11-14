from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

from app.database.connection import get_feature_db
from app.schemas.simulation_schema import SimulationRequest, SimulationResponse
from app.services.model_service import predict_risk

router = APIRouter()
logger = logging.getLogger(__name__)


# --------------------------------------------------------
# 최신 Feature 가져오기 (59개 명시 SELECT)
# --------------------------------------------------------
def load_latest_features(db: Session, user_id: int):

    query = text("""
        SELECT
            TOT_USE_AM_mean,
            TOT_USE_AM_max,
            TOT_USE_AM_min,
            TOT_USE_AM_std,
            CRDSL_USE_AM_mean,
            CRDSL_USE_AM_std,
            CNF_USE_AM_mean,
            CNF_USE_AM_std,
            credit_ratio_mean,
            credit_ratio_std,
            credit_ratio_last,
            check_ratio_mean,
            check_ratio_std,
            check_ratio_last,
            spend_growth_mean,
            spend_growth_std,
            spend_growth_last,
            spend_accel_mean,
            spend_accel_std,
            spend_accel_last,
            top3_ratio_sum_mean,
            top3_ratio_sum_std,
            top3_ratio_sum_last,
            top3_ratio_trend_mean,
            top3_ratio_trend_std,
            top3_ratio_trend_last,
            spending_entropy_mean,
            spending_entropy_std,
            spending_entropy_last,
            AGE,
            SEX_CD,
            MBR_RK,
            salary_mean,
            salary_max,
            salary_min,
            salary_std,
            balance_mean,
            balance_max,
            balance_min,
            balance_std,
            principal_amount_mean,
            principal_amount_max,
            principal_amount_min,
            principal_amount_std,
            remaining_principal_mean,
            remaining_principal_max,
            remaining_principal_min,
            remaining_principal_std,
            interest_rate_mean,
            interest_rate_max,
            interest_rate_min,
            interest_rate_std,
            repayment_ratio_mean,
            loan_type_mean,
            is_completed_mean,
            balance_to_loan_ratio,
            income_to_loan_ratio,
            debt_to_income_ratio,
            loan_usage_ratio
        FROM user_features
        WHERE user_id = :user_id
        ORDER BY created_at DESC
        LIMIT 1
    """)

    row = db.execute(query, {"user_id": user_id}).mappings().first()

    if not row:
        raise HTTPException(404, "해당 사용자의 Feature 데이터가 없습니다.")

    return dict(row)



# --------------------------------------------------------
# 변화 적용
# --------------------------------------------------------
def apply_changes_to_features(features: dict, changes):
    income_delta = sum(c.amount for c in changes if c.type == "income")
    expense_delta = sum(c.amount for c in changes if c.type == "expense")

    # 소비 증가 반영
    features["TOT_USE_AM_mean"] = float(features["TOT_USE_AM_mean"]) + float(expense_delta)

    # 소비 증가 → spend_growth_last 영향
    salary_mean = float(features["salary_mean"])
    features["spend_growth_last"] = features["TOT_USE_AM_mean"] / (salary_mean + 1e-6)

    # 잔액 변화 반영
    features["balance_mean"] = float(features["balance_mean"]) + float(income_delta) - float(expense_delta)

    # 비율 계산
    remaining = float(features["remaining_principal_mean"])
    new_income = salary_mean + float(income_delta)

    features["income_to_loan_ratio"] = new_income / (remaining + 1e-6)
    features["debt_to_income_ratio"] = remaining / (new_income + 1e-6)

    return features



# --------------------------------------------------------
# 시뮬레이션 API (predict.py와 동일한 구조)
# --------------------------------------------------------
@router.post("/simulation", response_model=SimulationResponse)
def run_simulation(
    request: SimulationRequest,
    db: Session = Depends(get_feature_db)
):
    try:
        # 최신 feature 로드
        base_features = load_latest_features(db, request.user_id)

        # numeric 변환
        base_features = {k: float(v) for k, v in base_features.items()}

        # 기존 위험도
        base_pred = predict_risk(base_features)
        base_score = base_pred["delinquency_probability"]

        # 변화 적용
        updated_features = base_features.copy()
        updated_features = apply_changes_to_features(updated_features, request.changes)

        # 시뮬레이션 위험도 재계산
        sim_pred = predict_risk(updated_features)
        sim_score = sim_pred["delinquency_probability"]

        delta = round(sim_score - base_score, 4)
        explanation = f"수입/지출 변화로 위험도가 {delta:+.4f} 만큼 변했습니다."

        return SimulationResponse(
            base_risk_score=round(base_score, 4),
            simulated_risk_score=round(sim_score, 4),
            delta=delta,
            explanation=explanation
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[Simulation API Error] {e}")
        raise HTTPException(500, f"Simulation failed: {str(e)}")

from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database.connection import FeatureSessionLocal
from app.schemas.predict_schema import PredictResponse
from app.services.model_service import predict_risk
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


def get_latest_features(db: Session, user_id: int):
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
    result = db.execute(query, {"user_id": user_id}).mappings().first()
    return dict(result) if result else None


@router.get("/predict/{user_id}", response_model=PredictResponse)
def predict(user_id: int):
    try:
        db = FeatureSessionLocal()

        # 최신 Feature 가져오기
        features = get_latest_features(db, user_id)
        if features is None:
            raise HTTPException(404, "해당 사용자의 Feature 데이터가 없습니다.")

        # 모델 입력에서 제외해야 하는 컬럼
        features.pop("user_id", None)
        features.pop("feature_date", None)

        # 모델 예측
        result = predict_risk(features)

        return PredictResponse(**result)

    except HTTPException:
        raise

    except Exception as e:
        logger.exception(f"[Predict API Error] {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal prediction error."
        )

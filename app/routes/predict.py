from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel, Field

from app.database.connection import get_feature_db
from app.services.model_service import predict_risk
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


# -------------------------------------------------------
# Request / Response 모델
# -------------------------------------------------------
class UserPredictRequest(BaseModel):
    user_id: int = Field(..., description="예측할 사용자 ID")


class LoanRiskItem(BaseModel):
    loan_ledger_id: int
    risk: float
    explanation: str


class UserRiskResponse(BaseModel):
    overall_risk: float
    loans: list[LoanRiskItem]
    model_version: str


# -------------------------------------------------------
# 개별 loan_ledger_id의 최신 Feature 가져오기
# -------------------------------------------------------
def load_latest_loan_features(db: Session, loan_ledger_id: int):

    query = text("""
        SELECT *
        FROM loan_features
        WHERE loan_ledger_id = :loan_ledger_id
        ORDER BY created_at DESC
        LIMIT 1
    """)

    row = db.execute(query, {"loan_ledger_id": loan_ledger_id}).mappings().first()
    return dict(row) if row else None


# -------------------------------------------------------
# user_id 기준 loan_ledger_id 리스트 조회
# -------------------------------------------------------
def load_user_loan_ids(db: Session, user_id: int):

    query = text("""
        SELECT DISTINCT loan_ledger_id
        FROM loan_features
        WHERE user_id = :user_id
    """)

    rows = db.execute(query, {"user_id": user_id}).mappings().all()
    return [r["loan_ledger_id"] for r in rows]


# -------------------------------------------------------
# POST /predict/user-risk
# -------------------------------------------------------
@router.post("/predict", response_model=UserRiskResponse)
def predict_user_risk(request: UserPredictRequest, db: Session = Depends(get_feature_db)):

    try:
        user_id = request.user_id

        # 사용자 loan_ledger_id 조회
        loan_ids = load_user_loan_ids(db, user_id)

        if not loan_ids:
            raise HTTPException(404, "해당 사용자의 대출 Feature 데이터가 없습니다.")

        loan_risk_items: list[LoanRiskItem] = []
        risk_list = []

        last_pred_info = None  # model_version 가져올 때 사용

        # loan 별로 예측 수행
        for ledger_id in loan_ids:

            features = load_latest_loan_features(db, ledger_id)
            if not features:
                continue

            # 예측에 필요 없는 컬럼 제거
            for drop_key in ["id", "loan_ledger_id", "user_id", "created_at"]:
                features.pop(drop_key, None)

            # float 형 변환
            features = {k: float(v) for k, v in features.items()}

            # 모델 예측
            pred = predict_risk(features)
            last_pred_info = pred

            risk = float(pred.get("delinquency_probability", 0.0))
            explanation = pred.get("explanation", "")

            loan_risk_items.append(
                LoanRiskItem(
                    loan_ledger_id=ledger_id,
                    risk=risk,
                    explanation=explanation,
                )
            )
            risk_list.append(risk)

        if not risk_list:
            raise HTTPException(500, "위험도 예측을 위한 Feature 데이터가 부족합니다.")

        # 사용자 전체 위험도 = 대출 위험도 중 최댓값
        overall_risk = round(max(risk_list), 4)

        # loan 리스트를 위험도 높은 순으로 정렬
        loan_risk_items.sort(key=lambda x: x.risk, reverse=True)

        # model_version
        model_version = last_pred_info.get("model_version", "unknown")

        return UserRiskResponse(
            overall_risk=overall_risk,
            loans=loan_risk_items,
            model_version=model_version
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.exception(f"[User Risk Prediction Error] {e}")
        raise HTTPException(500, "Internal server error in prediction.")

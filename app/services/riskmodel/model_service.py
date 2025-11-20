import numpy as np
import pandas as pd
from typing import Dict
import logging

from app.services.riskmodel.model_loader import get_model, THRESHOLD, MODEL_VERSION

logger = logging.getLogger(__name__)

# 모델 로드
bst = get_model()

def preprocess_input(features: Dict):
    df = pd.DataFrame([features])
    df = df.apply(pd.to_numeric, errors="coerce")
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df.fillna(0, inplace=True)
    df = df.astype(np.float32)
    return df


def predict_risk(features: Dict):
    try:
        df = preprocess_input(features)

        # Booster → predict()
        if hasattr(bst, "predict") and not hasattr(bst, "predict_proba"):
            prob = float(bst.predict(df)[0])

        # LGBMClassifier → predict_proba()
        elif hasattr(bst, "predict_proba"):
            prob = float(bst.predict_proba(df)[0][1])

        else:
            raise RuntimeError("Unknown LightGBM model type")

        label = int(prob > THRESHOLD)
        explanation = generate_explanation(features, prob, label)

        logger.info(
            f"[예측 결과] 확률={prob:.4f}, 라벨={label}, 버전={MODEL_VERSION}"
        )

        return {
            "delinquency_probability": round(prob, 4),
            "delinquency_label": label,
            "threshold": THRESHOLD,
            "model_version": MODEL_VERSION,
            "explanation": explanation,
        }

    except Exception as e:
        logger.exception(f"Prediction Error: {e}")
        raise


def generate_explanation(features: Dict, prob: float, label: int):
    total_spend = features.get("TOT_USE_AM_mean", 0)
    salary = features.get("salary_mean", 0)
    balance = features.get("balance_mean", 0)
    remaining = features.get("remaining_principal_mean", 0)

    spend_ratio = round(total_spend / salary, 2) if salary else 0
    dti = features.get("debt_to_income_ratio", 0)

    if label == 1:
        if spend_ratio > 0.5:
            return f"소득 대비 소비 비율이 {spend_ratio*100:.0f}%로 높아 위험합니다."
        if dti > 1:
            return f"부채가 소득보다 많아(DTI={dti:.2f}) 부담이 큽니다."
        if balance < remaining * 0.2:
            return "예금 잔액이 대출 잔액 대비 매우 낮아 유동성이 부족합니다."
        return "소비 및 대출 패턴에서 위험 신호가 감지됩니다."

    else:
        if spend_ratio < 0.3:
            return "소득 대비 소비 비율이 안정적입니다."
        if dti < 0.5:
            return "소득 여력이 충분해 상환 위험이 낮습니다."
        return "전반적으로 안정적인 소비·대출 구조입니다."

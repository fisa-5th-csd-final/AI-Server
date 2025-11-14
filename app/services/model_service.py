import numpy as np
import pandas as pd
from typing import Dict
import logging

from app.services.model_loader import get_model, THRESHOLD, MODEL_VERSION

logger = logging.getLogger(__name__)

# 서버 시작 시 LightGBM 모델 로드
bst = get_model()


# ===============================================================
# 입력 Feature 전처리 (65개 Feature 기반)
# ===============================================================
def preprocess_input(features: Dict):
    """LightGBM 입력 전처리: dict → float32 DataFrame"""

    logger.debug(f"[입력 데이터 수신] features keys={list(features.keys())}")

    # dict → DataFrame
    df = pd.DataFrame([features])

    # 모든 값을 numeric으로 변환
    df = df.apply(pd.to_numeric, errors="coerce")

    # NaN / Inf 처리
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df.fillna(0, inplace=True)

    # LightGBM은 float32/64 모두 허용, float32 추천
    df = df.astype(np.float32)

    logger.debug(f"[전처리 완료] shape={df.shape}, nulls={df.isna().sum().sum()}")
    return df


# ===============================================================
# 연체 위험 예측
# ===============================================================
def predict_risk(features: Dict):
    try:
        df = preprocess_input(features)

        # LightGBM 예측 (Booster 또는 LGBMClassifier 모두 지원)
        # Booster 타입
        if hasattr(bst, "predict") and not hasattr(bst, "predict_proba"):
            prob = float(bst.predict(df)[0])

        # LGBMClassifier 타입
        elif hasattr(bst, "predict_proba"):
            prob = float(bst.predict_proba(df)[0][1])

        else:
            raise RuntimeError("알 수 없는 LightGBM 모델 타입")

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


# ===============================================================
# 위험 설명 생성 (Feature 기반 요약)
# ===============================================================
def generate_explanation(features: Dict, prob: float, label: int):
    """65개 Feature 기반 간단 위험 설명"""

    # 주요 지표
    total_spend = features.get("TOT_USE_AM_mean", 0)
    salary = features.get("salary_mean", 0)
    balance = features.get("balance_mean", 0)
    remaining = features.get("remaining_principal_mean", 0)

    # 소비 비율
    spend_ratio = round(total_spend / salary, 2) if salary else 0

    # DTI
    dti = features.get("debt_to_income_ratio", 0)

    # --------- 위험 고객 ---------
    if label == 1:
        if spend_ratio > 0.5:
            return f"소득 대비 소비 비율이 {spend_ratio*100:.0f}%로 매우 높아 연체 위험이 증가했습니다."

        if dti > 1:
            return f"부채가 소득보다 많아(DTI={dti:.2f}) 상환 부담이 큽니다."

        if balance < remaining * 0.2:
            return "예금 잔액이 대출 잔액 대비 매우 낮아 유동성이 부족합니다."

        return "소비 및 대출 패턴에서 위험 신호가 감지되었습니다."

    # --------- 정상 고객 ---------
    else:
        if spend_ratio < 0.3:
            return "소득 대비 소비 비율이 안정적으로 관리되고 있습니다."

        if dti < 0.5:
            return "부채 대비 소득 여력이 충분해 상환 위험이 낮습니다."

        return "전반적인 소비, 소득, 대출 구조가 안정적입니다."

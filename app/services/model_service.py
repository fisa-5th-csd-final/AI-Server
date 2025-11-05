import xgboost as xgb
import numpy as np
import pandas as pd
from typing import Dict
import logging
import matplotlib.pyplot as plt
from app.services.model_loader import get_model, THRESHOLD, MODEL_VERSION

logger = logging.getLogger(__name__)

# 서버 시작 시 자동으로 모델 불러오기
bst, encoding_maps = get_model()

def preprocess_input(features: Dict):
    """모델 입력 데이터 전처리"""
    logger.debug(f"[입력 데이터 수신] features keys: {list(features.keys())}")
    df = pd.DataFrame([features])

    # 불필요 컬럼 제거
    drop_cols = ["customer_id", "is_delinquent"]
    df.drop(columns=[c for c in drop_cols if c in df.columns], inplace=True, errors="ignore")

    # 인코딩 처리
    for col, mapping in encoding_maps.items():
        if col in df.columns:
            rev_map = {v: k for k, v in mapping.items()}
            df[col] = df[col].map(rev_map).fillna(-1).astype(int)

    # 형변환
    for col in df.columns:
        if df[col].dtype == "object":
            if col.lower() == "repayment_date":
                df.drop(columns=[col], inplace=True)
            else:
                df[col] = pd.to_numeric(df[col], errors="coerce")

    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df.fillna(0, inplace=True)
    df = df.astype(np.float32)

    logger.debug(f"[전처리 완료] 컬럼 수: {df.shape[1]}, 결측치 수: {df.isna().sum().sum()}")
    return df

def predict_risk(features: Dict):
    """연체 위험 예측 수행"""
    try:
        df = preprocess_input(features)
        dtest = xgb.DMatrix(df)

        prob = float(bst.predict(dtest)[0])
        label = int(prob > THRESHOLD)
        explanation = generate_explanation(features, prob, label)

        logger.info(f"[예측 결과] 확률={prob:.4f}, 라벨={label}, 버전={MODEL_VERSION}")
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
    """간단한 예측 설명"""
    salary = float(features.get("salary", 0) or 0)
    balance = float(features.get("balance", 0) or 0)
    remaining = float(features.get("remaining_principal", 0) or 0)
    spending = float(features.get("TOT_USE_AM", 0) or 0)
    spending_ratio = round(spending / salary, 2) if salary else 0

    if label == 1:
        if spending_ratio > 0.5:
            return f"소비 비율이 {spending_ratio*100:.0f}%로 높고 대출 잔액이 소득의 절반 이상을 차지하여 연체 위험이 높습니다."
        elif balance < salary:
            return f"예금 잔액이 월급보다 적어 유동성이 낮습니다. 대출 상환 여력이 부족할 수 있습니다."
        else:
            return f"소비 및 대출 구조상 중간 수준의 위험이 감지되었습니다."
    else:
        return f"소득 대비 소비 비율이 {spending_ratio*100:.0f}%로 안정적이며, 잔액이 충분해 연체 위험이 낮습니다."


# 특성 중요도 시각화 코드 추가 
xgb.plot_importance(bst, importance_type="gain", max_num_features=38)
plt.show()
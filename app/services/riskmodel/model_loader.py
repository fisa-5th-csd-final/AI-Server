import joblib
import logging
import threading

MODEL_PATH = "app/models/lightgbm_risk_model.pkl"

logger = logging.getLogger(__name__)

bst = None
THRESHOLD = 0.344
MODEL_VERSION = "lightgbm_risk_model"

_model_lock = threading.Lock()


def load_model():
    global bst

    # 이미 로드된 경우 바로 반환
    if bst is not None:
        logger.debug("[Model Loader] 캐시된 모델 반환 중...")
        return bst

    # 모델 로드를 위한 락
    with _model_lock:
        # 락 내에서도 다시 확인
        if bst is not None:
            logger.debug("[Model Loader] 락 내에서 모델 이미 로드됨 — 캐시 사용")
            return bst

        try:
            logger.info("[Model Loader] LightGBM 모델 로드 중...")
            bst = joblib.load(MODEL_PATH)
            logger.info(f"[Model Loader] 모델 로드 완료 ({MODEL_VERSION}), Threshold={THRESHOLD}")
            return bst

        except Exception as e:
            logger.exception(f"[Model Loader] 모델 로드 실패: {e}")
            raise RuntimeError("모델 로드 중 오류 발생")


def get_model():
    global bst
    if bst is None:
        load_model()
    return bst

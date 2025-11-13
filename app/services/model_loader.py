import joblib
import json
import logging
import threading

MODEL_PATH = "app/models/lightgbm_risk_model.pkl"
ENCODE_MAP_PATH = "app/models/encoding_map.json"

logger = logging.getLogger(__name__)

bst = None
encoding_maps = None
THRESHOLD = 0.344
MODEL_VERSION = "lightgbm_risk_model"

_model_lock = threading.Lock()

def load_model():
    global bst, encoding_maps

    # 이미 로드된 경우 빠르게 반환
    if bst is not None and encoding_maps is not None:
        logger.debug("[Model Loader] 캐시된 모델 반환 중...")
        return bst, encoding_maps

    # 모델 로드 구간 보호
    with _model_lock:
        # 다른 스레드가 이미 로드했는지 한 번 더 확인
        if bst is not None and encoding_maps is not None:
            logger.debug("[Model Loader] 락 내에서 이미 모델 로드 완료 — 캐시 사용")
            return bst, encoding_maps

        try:
            logger.info("[Model Loader] LightGBM 모델 및 인코딩 맵 로드 중...")
            bst = joblib.load(MODEL_PATH)
            with open(ENCODE_MAP_PATH, "r", encoding="utf-8") as f:
                encoding_maps = json.load(f)
            logger.info(f"[Model Loader] 모델 로드 완료 ({MODEL_VERSION}), Threshold={THRESHOLD}")
            return bst, encoding_maps
        except Exception as e:
            logger.exception(f"[Model Loader] 모델 로드 실패: {e}")
            raise RuntimeError("모델 로드 중 오류 발생")

def get_model():
    global bst, encoding_maps
    if bst is None or encoding_maps is None:
        load_model()
    return bst, encoding_maps

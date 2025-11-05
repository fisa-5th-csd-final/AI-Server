import joblib, json, logging

MODEL_PATH = "app/models/xgb_delinquency_model_v2.pkl"
ENCODE_MAP_PATH = "app/models/category_encoding_map_v2.json"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

bst = None
encoding_maps = None
THRESHOLD = 0.88
MODEL_VERSION = "xgb_delinquency_model_v2"

def load_model():
    """FastAPI 실행 시 단 1회만 모델 로드"""
    global bst, encoding_maps

    if bst is not None and encoding_maps is not None:
        logger.info("[Model Loader] 모델 이미 로드됨 — 캐시 사용 중")
        return bst, encoding_maps

    try:
        logger.info("[Model Loader] XGBoost 모델 및 인코딩 맵 로드 중...")
        bst = joblib.load(MODEL_PATH)
        with open(ENCODE_MAP_PATH, "r", encoding="utf-8") as f:
            encoding_maps = json.load(f)
        logger.info(f"[Model Loader] 모델 로드 완료 ({MODEL_VERSION}), Threshold={THRESHOLD}")
        return bst, encoding_maps
    except Exception as e:
        logger.exception(f"[Model Loader] 모델 로드 실패: {e}")
        raise RuntimeError("모델 로드 중 오류 발생")

def get_model():
    """전역 모델 반환"""
    global bst, encoding_maps
    if bst is None or encoding_maps is None:
        load_model()
    return bst, encoding_maps

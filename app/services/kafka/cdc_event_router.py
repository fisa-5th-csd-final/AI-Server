# app/services/kafka/cdc_event_router.py

from app.services.kafka.cdc_event_model import CdcEvent
from app.services.kafka.cdc_save_data import apply_cdc_event_to_core_db
from datetime import datetime, timezone

def micros_to_datetime(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromtimestamp(value / 1_000_000, tz=timezone.utc)
    except Exception:
        return None
    
DATETIME_FIELDS = {
    "loan_ledger": [
        "next_repayment_date",
        "last_repayment_date",
        "loan_end_date",
        "created_at",
        "updated_at",
    ],
    "loan_transaction": [
        "date",
        "created_at",
        "updated_at",
    ],
    "account": [
        "created_at",
        "updated_at",
    ],
    "user": [
        "birthday",
        "created_at",
        "updated_at",
    ],
    "loan_product": [
        "created_at",
        "updated_at",
    ],
    "interest_rate": [
        "created_at",
        "updated_at",
    ],
    "prefer_interest": [
        # prefer_interest는 datetime 없음
    ],
}

def transform_datetime_fields(event_dict: dict):
    """CDC 이벤트에서 datetime 필드를 Python datetime으로 변환"""
    table = event_dict.get("table")
    after = event_dict.get("after")

    if not after or table not in DATETIME_FIELDS:
        return event_dict  # 변환할 필드 없음

    for field in DATETIME_FIELDS[table]:
        if field in after:
            after[field] = micros_to_datetime(after[field])

    # before에도 datetime이 있을 수 있으므로 동일 처리
    before = event_dict.get("before")
    if before:
        for field in DATETIME_FIELDS[table]:
            if field in before:
                before[field] = micros_to_datetime(before[field])

    return event_dict


async def route_cdc_event(event: CdcEvent):

    event_dict = event.model_dump()
    event_dict = transform_datetime_fields(event_dict)
    
    # core_bank DB에 원본 데이터 저장
    await apply_cdc_event_to_core_db(event_dict)

    # 모든 CDC 이벤트마다 전체 feature 갱신
    # await update_features_for_event(event)

    print(f"[CDC Router] 처리 완료 → table={event.table}")

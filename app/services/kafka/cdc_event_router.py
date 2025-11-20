# app/services/kafka/cdc_event_router.py

from app.services.kafka.cdc_event_model import CdcEvent
from app.services.kafka.cdc_save_data import apply_cdc_event_to_core_db
from app.services.feature.update_feature import update_features_for_event


async def route_cdc_event(event: CdcEvent):
    # 1) core_bank DB에 원본 데이터 저장
    await apply_cdc_event_to_core_db(event.model_dump())

    # 2) 모든 CDC 이벤트마다 전체 feature 갱신
    # await update_features_for_event(event)

    print(f"[CDC Router] 처리 완료 → table={event.table}")

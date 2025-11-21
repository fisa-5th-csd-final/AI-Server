import asyncio
import json
import traceback
from aiokafka import AIOKafkaConsumer

from app.services.kafka.cdc_event_model import CdcEvent
from app.services.kafka.cdc_event_router import route_cdc_event


# =============================
# Kafka 설정
# =============================
BOOTSTRAP_SERVERS = "kafka:9092"
TOPIC = "bank.cdc.changelog"
GROUP_ID = "bank-cdc-consumer"


# =============================
# Kafka Consumer 시작
# =============================
async def start_kafka_consumer():
    consumer = AIOKafkaConsumer(
        TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        group_id=GROUP_ID,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
    )

    await consumer.start()
    print("Kafka CDC Consumer Started")

    try:
        async for msg in consumer:
            try:
                # 1) Debezium 메시지 디코딩
                raw_json = json.loads(msg.value.decode())
                print(f"[Kafka RAW] {raw_json}")

                # Debezium payload 추출
                payload = raw_json.get("payload")
                if not payload:
                    print("[WARN] payload 없음 → skip")
                    continue

                source = payload.get("source", {})
                before = payload.get("before")
                after = payload.get("after")

                # 필수 필드 없는 경우 skip
                table = source.get("table")
                op = payload.get("op")

                if not table or not op:
                    print(f"[WARN] table/op 없음 → skip raw={raw_json}")
                    continue

                # 2) CdcEvent 모델 생성
                event = CdcEvent(
                    database=source.get("db"),
                    table=table,
                    operation=op,
                    before=before,
                    after=after,
                    sourceTimestamp=source.get("ts_ms")
                )

                print(f"[CDC 이벤트 수신] table={event.table}, op={event.operation}")

                # 3) 라우팅 실행
                await route_cdc_event(event)

            except Exception as e:
                print("CDC 처리 중 오류 발생!", e)
                traceback.print_exc()
                # 에러가 나도 consumer가 죽으면 안되므로 continue
                continue

    finally:
        await consumer.stop()
        print("Kafka Consumer Stopped")

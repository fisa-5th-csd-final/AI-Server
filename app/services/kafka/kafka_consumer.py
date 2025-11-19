# app/services/kafka/kafka_consumer.py

import asyncio
import json
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
            # JSON 디코딩
            raw_json = json.loads(msg.value.decode())

            # CDC Event 모델 변환
            event = CdcEvent(**raw_json)

            print(f"CDC 이벤트 수신: table={event.table} op={event.operation}")

            # 라우팅
            await route_cdc_event(event)

    finally:
        await consumer.stop()
        print("Kafka Consumer Stopped")

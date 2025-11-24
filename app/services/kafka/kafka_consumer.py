import asyncio
import json
from aiokafka import AIOKafkaConsumer
import os

from app.services.kafka.cdc_event_model import CdcEvent
from app.services.kafka.cdc_event_router import route_cdc_event

BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
TOPIC = os.getenv("KAFKA_TOPIC")
GROUP_ID = os.getenv("KAFKA_GROUP_ID")


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
            raw_json = json.loads(msg.value.decode())
            print(f"[Kafka RAW] {raw_json}")

            # Debezium 커스텀 포맷 직접 매핑
            event = CdcEvent(
                database=raw_json.get("database"),
                table=raw_json.get("table"),
                operation=raw_json.get("operation"),
                before=raw_json.get("before"),
                after=raw_json.get("after"),
                sourceTimestamp=raw_json.get("sourceTimestamp")
            )

            print(f"[Kafka → Model] table={event.table}, op={event.operation}")

            # CDC 라우터로 전달
            await route_cdc_event(event)

    finally:
        await consumer.stop()
        print("Kafka Consumer Stopped")

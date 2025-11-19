from app.services.kafka.cdc_event_model import CdcEvent
from app.services.feature.feature_service import process_cdc_event as process_feature_cdc

# CDC 이벤트 라우터
async def route_cdc_event(event: CdcEvent):

    table = event.table.lower()
    op = event.operation
    after = event.after

    # LoanLedger 변경 → Feature 업데이트
    if table == "loan_ledger" and op in ("c", "u"):
        await process_feature_cdc(event.model_dump())

    else:
        print(f"처리할 Consumer 없음: table={table}, op={op}")

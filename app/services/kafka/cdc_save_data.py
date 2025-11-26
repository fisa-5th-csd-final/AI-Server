from datetime import datetime, timezone
from app.database.connection import CoreSessionLocal
from app.database.models import (
    User, Account, AccountTransaction, CardTransaction,
    LoanLedger, LoanTransaction, LoanProduct, InterestRate, PreferInterest
)
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.sql.sqltypes import DateTime as SQLAlchemyDateTime

def convert_timestamp(value):
    """Debezium micosecond timestamp → Python datetime"""
    if isinstance(value, int) and value > 10**12:
        return datetime.fromtimestamp(value / 1_000_000, tz=timezone.utc)
    return value

def convert_datetime_fields(model, data: dict):
    """Model 컬럼 중 datetime 타입만 찾아 변환"""
    new_data = data.copy()
    for column in model.__table__.columns:
        if isinstance(column.type, SQLAlchemyDateTime):
            col = column.name
            if col in new_data and new_data[col] is not None:
                new_data[col] = convert_timestamp(new_data[col])
    return new_data

TABLE_MODEL_MAP = {
    "user": User,
    "account": Account,
    "transaction_account": AccountTransaction,
    "transaction_card": CardTransaction,
    "loan_ledger": LoanLedger,
    "loan_transaction": LoanTransaction,
    "loan_product": LoanProduct,
    "interest_rate": InterestRate,
    "prefer_interest": PreferInterest,
}

async def apply_cdc_event_to_core_db(event_dict):

    table = event_dict["table"].lower()
    op = event_dict["operation"].lower()
    after = event_dict["after"]
    before = event_dict["before"]

    Model = TABLE_MODEL_MAP.get(table)
    if not Model:
        print(f"[CDC] Unknown table: {table}")
        return

    db = CoreSessionLocal()

    try:
        # CREATE or UPDATE
        if op in ("c", "u"):
            after = convert_datetime_fields(Model, after)
            stmt = insert(Model).values(after)
            update_stmt = stmt.on_duplicate_key_update(**after)
            db.execute(update_stmt)
            db.commit()
            print(f"[CDC] UPSERT → {table}")

        # DELETE
        elif op == "d":
            pk_col = list(Model.__table__.primary_key.columns)[0].name
            pk_value = before[pk_col]
            db.query(Model).filter(getattr(Model, pk_col) == pk_value).delete()
            db.commit()
            print(f"[CDC] DELETE → {table} id={pk_value}")

    except Exception as e:
        db.rollback()
        print(f"[CDC] ERROR: {e}")

    finally:
        db.close()

from datetime import datetime, timezone
from app.database.connection import CoreSessionLocal
from app.database.models import (
    User, Account, AccountTransaction, CardTransaction,
    LoanLedger, LoanTransaction, LoanProduct, InterestRate, PreferInterest
)
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.sql.sqltypes import DateTime as SQLAlchemyDateTime
from sqlalchemy.sql.schema import ForeignKey


# ---------------------------------------------------------
# 1) Debezium datetime 변환 (microseconds → datetime)
# ---------------------------------------------------------
def convert_timestamp(value):
    """Debezium microsecond timestamp → Python datetime"""
    if isinstance(value, int) and value > 10**12:
        return datetime.fromtimestamp(value / 1_000_000, tz=timezone.utc)
    return value


def convert_datetime_fields(model, data: dict):
    """Model 컬럼 중 datetime 타입만 변환"""
    new_data = data.copy()
    for column in model.__table__.columns:
        if isinstance(column.type, SQLAlchemyDateTime):
            col = column.name
            if col in new_data and new_data[col] is not None:
                new_data[col] = convert_timestamp(new_data[col])
    return new_data


# ---------------------------------------------------------
# 2) FK가 아직 parent 테이블에 없을 경우 NULL로 변경
# ---------------------------------------------------------
def nullify_missing_foreign_keys(model, data):
    """
    INSERT 시 외래키 parent row가 존재하지 않으면 FK를 NULL 처리하여
    IntegrityError 방지 → Debezium snapshot 순서 문제 해결
    """
    new_data = data.copy()

    for column in model.__table__.columns:
        # FK인지 체크
        for fk in column.foreign_keys:
            fk_col = column.name  # 예: user_id, account_id, loan_ledger_id

            if fk_col not in new_data:
                continue

            fk_value = new_data[fk_col]

            # 값 자체가 None이면 그대로 둠
            if fk_value is None:
                continue

            # parent 테이블 모델 찾기
            parent_table = fk.column.table
            parent_table_name = parent_table.name

            from app.database.models import Base
            parent_model = Base._decl_class_registry.get(parent_table_name)

            if not parent_model:
                continue  # 예상치 못한 경우지만 무시

            # parent row 실제 존재 여부 확인
            db = CoreSessionLocal()
            parent_exists = db.query(parent_model)\
                .filter(fk.column == fk_value)\
                .first()
            db.close()

            if not parent_exists:
                print(f"[CDC] FK parent missing → {fk_col}={fk_value} → NULL 처리됨")
                new_data[fk_col] = None

    return new_data


# ---------------------------------------------------------
# 3) 테이블 → 모델 매핑
# ---------------------------------------------------------
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


# ---------------------------------------------------------
# 4) CDC 적용 메인 함수
# ---------------------------------------------------------
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
        # --------------------------------------------
        # INSERT or UPDATE (UPSERT)
        # --------------------------------------------
        if op in ("c", "u"):

            # datetime 변환
            after = convert_datetime_fields(Model, after)

            # FK parent 없는 경우 NULL 처리
            after = nullify_missing_foreign_keys(Model, after)

            # UPSERT
            stmt = insert(Model).values(after)
            update_stmt = stmt.on_duplicate_key_update(**after)
            db.execute(update_stmt)
            db.commit()

            print(f"[CDC] UPSERT → {table}")

        # --------------------------------------------
        # DELETE
        # --------------------------------------------
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

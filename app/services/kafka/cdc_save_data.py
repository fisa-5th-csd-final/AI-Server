from datetime import datetime, timezone
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.sql.sqltypes import DateTime as SQLAlchemyDateTime
from sqlalchemy.inspection import inspect
from app.database.connection import CoreSessionLocal
from app.database.models import (
    User, Account, AccountTransaction, CardTransaction,
    LoanLedger, LoanTransaction, LoanProduct, InterestRate, PreferInterest, Base
)

# --------------------------------------------------------
# FK 업데이트 대기 목록 (in-memory)
# --------------------------------------------------------
pending_fk_fixes = []


# --------------------------------------------------------
# Timestamp 변환
# --------------------------------------------------------
def convert_timestamp(value):
    if isinstance(value, int) and value > 10**12:
        return datetime.fromtimestamp(value / 1_000_000, tz=timezone.utc)
    return value


def convert_datetime_fields(model, data):
    new_data = data.copy()
    for column in model.__table__.columns:
        if isinstance(column.type, SQLAlchemyDateTime):
            col = column.name
            if col in new_data and new_data[col] is not None:
                new_data[col] = convert_timestamp(new_data[col])
    return new_data


# --------------------------------------------------------
# 모델 찾기
# --------------------------------------------------------
def get_model_by_table_name(table_name: str):
    for mapper in Base.registry.mappers:
        cls = mapper.class_
        if hasattr(cls, "__tablename__") and cls.__tablename__ == table_name:
            return cls
    return None


# --------------------------------------------------------
# FK parent 존재 여부 체크 + NULL 처리
# --------------------------------------------------------
def nullify_missing_foreign_keys(model, data):
    new_data = data.copy()
    pk_col = list(model.__table__.primary_key.columns)[0].name
    child_pk = new_data.get(pk_col)

    for column in model.__table__.columns:
        if not column.foreign_keys:
            continue

        fk_col = column.name

        if fk_col not in new_data:
            continue

        fk_value = new_data[fk_col]
        if fk_value is None:
            continue

        fk = list(column.foreign_keys)[0]
        parent_table_name = fk.column.table.name

        parent_model = get_model_by_table_name(parent_table_name)
        if not parent_model:
            # UserAuth 같은 테이블은 AI DB에 없음 → FK NULL 처리
            new_data[fk_col] = None
            continue

        # parent 존재 여부 검사
        db = CoreSessionLocal()
        parent_exists = db.query(parent_model)\
            .filter(fk.column == fk_value)\
            .first()
        db.close()

        if not parent_exists:
            # FK 복원 대기 등록
            pending_fk_fixes.append({
                "child_table": model.__tablename__,
                "child_pk": child_pk,
                "fk_col": fk_col,
                "target_value": fk_value,
                "parent_table": parent_table_name
            })

            print(f"[CDC] FK parent missing → {fk_col}={fk_value} → NULL 처리됨 (repair scheduled)")
            new_data[fk_col] = None

    return new_data


# --------------------------------------------------------
# FK 복구 시도
# --------------------------------------------------------
def try_repair_foreign_keys(parent_table, parent_pk_value):
    """parent row가 이제 도착했으므로 FK NULL로 남아있던 child를 복구"""

    db = CoreSessionLocal()
    repaired = []

    for pending in list(pending_fk_fixes):
        if pending["parent_table"] != parent_table:
            continue
        if pending["target_value"] != parent_pk_value:
            continue

        child_model = get_model_by_table_name(pending["child_table"])
        if not child_model:
            continue

        pk_col = list(child_model.__table__.primary_key.columns)[0]

        # UPDATE child FK 복원
        db.query(child_model)\
            .filter(pk_col == pending["child_pk"])\
            .update({
                pending["fk_col"]: parent_pk_value
            })

        repaired.append(pending)
        pending_fk_fixes.remove(pending)

        print(f"[CDC] FK REPAIRED → {pending['child_table']}({pending['child_pk']}) "
              f"{pending['fk_col']}={parent_pk_value}")

    db.commit()
    db.close()

    return repaired


# --------------------------------------------------------
# 테이블 매핑
# --------------------------------------------------------
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

# 특정 필드 제거
IGNORED_FIELDS = {
    "user": ["user_auth_login_id"]
}


def filter_ignored_fields(table, data):
    if table in IGNORED_FIELDS:
        for field in IGNORED_FIELDS[table]:
            data.pop(field, None)
    return data


# --------------------------------------------------------
# CDC MAIN
# --------------------------------------------------------
async def apply_cdc_event_to_core_db(event_dict):
    table = event_dict["table"].lower()
    op = event_dict["operation"].lower()
    after = event_dict["after"]
    before = event_dict["before"]

    if after:
        after = filter_ignored_fields(table, after)

    if before:
        before = filter_ignored_fields(table, before)

    Model = TABLE_MODEL_MAP.get(table)
    if not Model:
        print(f"[CDC] Unknown table: {table}")
        return

    db = CoreSessionLocal()

    try:

        # -------------------------
        # INSERT or UPDATE
        # -------------------------
        if op in ("c", "u"):

            after = convert_datetime_fields(Model, after)
            after = nullify_missing_foreign_keys(Model, after)

            # UPSERT
            stmt = insert(Model).values(after)
            update_stmt = stmt.on_duplicate_key_update(**after)
            db.execute(update_stmt)
            db.commit()

            print(f"[CDC] UPSERT → {table}")

            # 여기서 parent INSERT인지 확인 후 FK 복구 시도
            pk_col = list(Model.__table__.primary_key.columns)[0].name
            parent_pk_value = after.get(pk_col)

            try_repair_foreign_keys(
                parent_table=table,
                parent_pk_value=parent_pk_value
            )

        # -------------------------
        # DELETE
        # -------------------------
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

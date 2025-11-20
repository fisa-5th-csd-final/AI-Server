# app/services/feature/update_feature.py

from app.database.connection import get_core_db, get_feature_db
from app.database.models import LoanLedger
from app.services.feature.feature_service import build_loan_features


async def update_features_for_event(event):
    """
    CDC 이벤트가 올 때마다 전체 loan_ledger를 기반으로 feature를 재작업한다.
    (batch data ingestion model에 최적)
    """

    print("[Feature] CDC 이벤트 수신 → 전체 Feature 업데이트 시작")

    core_db_gen = get_core_db()
    feature_db_gen = get_feature_db()

    core_db = next(core_db_gen)
    feature_db = next(feature_db_gen)

    try:
        loan_ledgers = core_db.query(LoanLedger).all()

        for loan in loan_ledgers:
            features = build_loan_features(loan.loan_ledger_id, core_db)

            placeholders = ", ".join([f"{k} = :{k}" for k in features.keys()])

            sql = f"""
                INSERT INTO loan_features ({", ".join(features.keys())})
                VALUES ({", ".join([":" + k for k in features.keys()])})
                ON DUPLICATE KEY UPDATE {placeholders}
            """

            feature_db.execute(sql, features)

        feature_db.commit()
        print("[Feature] 전체 Feature 업데이트 완료")

    finally:
        core_db.close()
        feature_db.close()

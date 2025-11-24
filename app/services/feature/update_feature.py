# app/services/feature/update_feature.py

from app.database.connection import get_core_db, get_feature_db
from app.database.models import LoanLedger
from app.services.feature.feature_service import build_loan_features


async def update_features_for_event(event):
    """
    CDC 이벤트가 올 때마다 전체 loan_ledger 기반으로 feature 재생성
    (실시간 입력 방식일 때 사용)
    """
    print("[Feature] CDC 이벤트 수신 → 전체 Feature 업데이트 시작")

    core_db = next(get_core_db())
    feature_db = next(get_feature_db())

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



async def update_features_daily():
    """
    매일 한번 전체 feature를 재계산하는 일일 배치 용도.
    CDC 이벤트에는 반응 X
    """
    print("[Feature] 일일 전체 Feature 업데이트 시작")

    core_db = next(get_core_db())
    feature_db = next(get_feature_db())

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
        print("[Feature] 일일 전체 Feature 업데이트 완료")

    except Exception as e:
        print("[Feature] ERROR", e)

    finally:
        core_db.close()
        feature_db.close()

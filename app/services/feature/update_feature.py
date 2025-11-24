from app.database.connection import CoreSessionLocal, FeatureSessionLocal
from app.database.models import LoanLedger
from app.services.feature.feature_service import build_loan_features


async def update_features_daily():
    print("[Feature] 일일 전체 Feature 업데이트 시작")

    core_db = CoreSessionLocal()

    try:
        # 1) core_bank 에서 전체 대출 조회
        loan_ledgers = core_db.query(LoanLedger).all()
        print(f"[Feature] 총 {len(loan_ledgers)}개의 LoanLedger 처리 중...")

        for ledger in loan_ledgers:
            loan_id = ledger.loan_ledger_id

            # 2) 단일 loan_ledger → feature 계산
            features = build_loan_features(loan_id, core_db)

            # 3) feature DB에 UPSERT 적용
            feature_db = FeatureSessionLocal()

            try:
                placeholders = ", ".join([f"{k} = :{k}" for k in features.keys()])

                sql = f"""
                    INSERT INTO loan_features ({", ".join(features.keys())})
                    VALUES ({", ".join([":" + k for k in features.keys()])})
                    ON DUPLICATE KEY UPDATE {placeholders}
                """

                feature_db.execute(sql, features)
                feature_db.commit()

                print(f"[Feature] UPSERT 완료 → loan_ledger_id={loan_id}")

            except Exception as fe:
                feature_db.rollback()
                print(f"[Feature] ERROR (loan_id={loan_id}):", fe)

            finally:
                feature_db.close()

        print("[Feature] 일일 전체 Feature 업데이트 완료")

    except Exception as e:
        print("[Feature] ERROR:", e)

    finally:
        core_db.close()

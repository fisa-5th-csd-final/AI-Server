import pandas as pd
import numpy as np
from datetime import datetime
from sqlalchemy.orm import Session

from app.database.models import (
    User, Account, AccountTransaction, CardTransaction,
    LoanLedger, LoanProduct, InterestRate
)


# ===============================
# Helper Functions
# ===============================

def safe_mean(values):
    return float(np.mean(values)) if len(values) > 0 else 0.0

def safe_std(values):
    return float(np.std(values)) if len(values) > 1 else 0.0

def safe_last(values):
    return float(values[-1]) if len(values) > 0 else 0.0


# ===============================
# 메인 Feature 생성 함수
# ===============================

def build_user_features(user_id: int, db: Session):

    # -----------------------------------------------------
    # User 정보
    # -----------------------------------------------------
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise Exception("User not found")

    age = (datetime.utcnow() - user.birthday).days // 365

    SEX_CD = getattr(user, "sex_cd", 0)
    MBR_RK = getattr(user, "customer_level", 0)
    income = user.income


    # -----------------------------------------------------
    # Account + AccountTransaction + CardTransaction
    # -----------------------------------------------------
    accounts = db.query(Account).filter(Account.user_id == user_id).all()
    account_ids = [acc.account_id for acc in accounts]

    trx_acc = db.query(AccountTransaction)\
        .filter(AccountTransaction.account_id.in_(account_ids)).all()

    trx_card = db.query(CardTransaction)\
        .filter(CardTransaction.account_id.in_(account_ids)).all()

    df_acc = pd.DataFrame([{
        "amount": float(t.amount),
        "is_income": t.is_income,
        "type": t.type.value,
        "created_at": pd.to_datetime(t.created_at)
    } for t in trx_acc]) if trx_acc else pd.DataFrame()

    df_card = pd.DataFrame([{
        "amount": float(t.amount),
        "category": t.category.value if t.category else None,
        "created_at": pd.to_datetime(t.created_at)
    } for t in trx_card]) if trx_card else pd.DataFrame()


    # -----------------------------------------------------
    # 월 단위 grouping
    # -----------------------------------------------------
    if len(df_acc) > 0:
        df_acc["month"] = df_acc["created_at"].dt.to_period("M")
    if len(df_card) > 0:
        df_card["month"] = df_card["created_at"].dt.to_period("M")


    # -----------------------------------------------------
    # TOT_USE_AM
    # -----------------------------------------------------
    if len(df_acc) > 0:
        total_use = df_acc[df_acc["is_income"] == False]["amount"]
    else:
        total_use = []

    TOT_USE_AM_mean = safe_mean(total_use)
    TOT_USE_AM_max = max(total_use) if len(total_use) else 0
    TOT_USE_AM_min = min(total_use) if len(total_use) else 0
    TOT_USE_AM_std = safe_std(total_use)


    # -----------------------------------------------------
    # 카드 금액
    # -----------------------------------------------------
    crd = df_card["amount"] if len(df_card) else []
    CRDSL_USE_AM_mean = safe_mean(crd)
    CRDSL_USE_AM_std = safe_std(crd)


    # -----------------------------------------------------
    # 출금
    # -----------------------------------------------------
    cnf = df_acc[df_acc["is_income"] == False]["amount"] if len(df_acc) else []
    CNF_USE_AM_mean = safe_mean(cnf)
    CNF_USE_AM_std = safe_std(cnf)


    # -----------------------------------------------------
    # 월별 credit/check ratio + std + last
    # -----------------------------------------------------
    # 월별 카드 + 출금 합계 생성
    card_month = df_card.groupby("month")["amount"].sum() if len(df_card) else pd.Series([])
    acc_withdraw_month = df_acc[df_acc["is_income"] == False].groupby("month")["amount"].sum() if len(df_acc) else pd.Series([])

    all_months = sorted(set(card_month.index).union(acc_withdraw_month.index))

    credit_ratio_list = []
    check_ratio_list = []

    for m in all_months:
        c = card_month.get(m, 0)
        w = acc_withdraw_month.get(m, 0)
        total = c + w if (c + w) > 0 else 1
        credit_ratio_list.append(c / total)
        check_ratio_list.append(w / total)

    credit_ratio_mean = safe_mean(credit_ratio_list)
    credit_ratio_std = safe_std(credit_ratio_list)
    credit_ratio_last = safe_last(credit_ratio_list)

    check_ratio_mean = safe_mean(check_ratio_list)
    check_ratio_std = safe_std(check_ratio_list)
    check_ratio_last = safe_last(check_ratio_list)


    # -----------------------------------------------------
    # 월별 소비 성장(growth) / 가속도(accel)
    # -----------------------------------------------------
    if len(df_acc) > 0:
        monthly = df_acc.groupby("month")["amount"].sum()
        growth = monthly.pct_change().fillna(0)
        accel = growth.diff().fillna(0)
    else:
        growth = []
        accel = []

    spend_growth_mean = safe_mean(growth)
    spend_growth_std = safe_std(growth)
    spend_growth_last = safe_last(growth)

    spend_accel_mean = safe_mean(accel)
    spend_accel_std = safe_std(accel)
    spend_accel_last = safe_last(accel)


    # -----------------------------------------------------
    # top3_ratio_sum + trend (월 단위)
    # -----------------------------------------------------
    if len(df_card) > 0:
        df_cat = df_card.copy()
        df_cat["count"] = 1
        monthly_cat = df_cat.groupby(["month", "category"])["count"].sum()

        # month → 카테고리 비율
        top3_ratio_sum_list = []
        top3_ratio_trend_list = []

        months_sorted = sorted(set(df_cat["month"]))

        for m in months_sorted:
            cat_counts = monthly_cat[m] if m in monthly_cat.index.levels[0] else pd.Series([])
            if len(cat_counts) == 0:
                top3_ratio_sum_list.append(0)
                top3_ratio_trend_list.append(0)
                continue

            pct = cat_counts / cat_counts.sum()
            top3 = pct.sort_values(ascending=False)[:3].sum()
            top3_ratio_sum_list.append(float(top3))

        # trend = diff of top3 ratio
        for i in range(len(top3_ratio_sum_list)):
            if i == 0:
                top3_ratio_trend_list.append(0)
            else:
                diff = top3_ratio_sum_list[i] - top3_ratio_sum_list[i-1]
                top3_ratio_trend_list.append(float(diff))

        top3_ratio_sum_mean = safe_mean(top3_ratio_sum_list)
        top3_ratio_sum_std = safe_std(top3_ratio_sum_list)
        top3_ratio_sum_last = safe_last(top3_ratio_sum_list)

        top3_ratio_trend_mean = safe_mean(top3_ratio_trend_list)
        top3_ratio_trend_std = safe_std(top3_ratio_trend_list)
        top3_ratio_trend_last = safe_last(top3_ratio_trend_list)

    else:
        top3_ratio_sum_mean = top3_ratio_sum_std = top3_ratio_sum_last = 0
        top3_ratio_trend_mean = top3_ratio_trend_std = top3_ratio_trend_last = 0


    # -----------------------------------------------------
    # spending_entropy
    # -----------------------------------------------------
    if len(df_card) > 0:
        months = sorted(df_card["month"].unique())
        entropy_list = []

        for m in months:
            month_df = df_card[df_card["month"] == m]
            pct = month_df["category"].value_counts(normalize=True)
            ent = -(pct * np.log(pct)).sum()
            entropy_list.append(float(ent))

        spending_entropy_mean = safe_mean(entropy_list)
        spending_entropy_std = safe_std(entropy_list)
        spending_entropy_last = safe_last(entropy_list)

    else:
        spending_entropy_mean = spending_entropy_std = spending_entropy_last = 0


    # -----------------------------------------------------
    # salary_* (급여) → 현재 DB에서 분리 불가 → 0
    # -----------------------------------------------------
    salary_mean = salary_max = salary_min = salary_std = 0


    # -----------------------------------------------------
    # Account 잔액
    # -----------------------------------------------------
    balances = [float(a.balance) for a in accounts] if accounts else []
    balance_mean = safe_mean(balances)
    balance_max = max(balances) if balances else 0
    balance_min = min(balances) if balances else 0
    balance_std = safe_std(balances)


    # -----------------------------------------------------
    # LoanLedger Feature
    # -----------------------------------------------------
    loans = db.query(LoanLedger).filter(LoanLedger.user_id == user_id).all()
    principal_vals = [float(l.principal) for l in loans]
    remaining_vals = [float(l.remain_principal) for l in loans]
    interest_vals = [float(l.completed_interest) for l in loans]

    principal_amount_mean = safe_mean(principal_vals)
    principal_amount_max = max(principal_vals) if principal_vals else 0
    principal_amount_min = min(principal_vals) if principal_vals else 0
    principal_amount_std = safe_std(principal_vals)

    remaining_principal_mean = safe_mean(remaining_vals)
    remaining_principal_max = max(remaining_vals) if remaining_vals else 0
    remaining_principal_min = min(remaining_vals) if remaining_vals else 0
    remaining_principal_std = safe_std(remaining_vals)

    interest_rate_mean = safe_mean(interest_vals)
    interest_rate_max = max(interest_vals) if interest_vals else 0
    interest_rate_min = min(interest_vals) if interest_vals else 0
    interest_rate_std = safe_std(interest_vals)

    repayment_ratio_mean = (principal_amount_mean - remaining_principal_mean) / (principal_amount_mean + 1e-6)

    loan_type_mean = np.mean([1 if l.repayment_type.value == "BULLET" else 0 for l in loans]) if loans else 0
    is_completed_mean = np.mean([1 if l.repayment_status.value == "COMPLETED" else 0 for l in loans]) if loans else 0

    # ratios
    balance_to_loan_ratio = balance_mean / (remaining_principal_mean + 1e-6)
    income_to_loan_ratio = income / (remaining_principal_mean + 1e-6)
    debt_to_income_ratio = remaining_principal_mean / (income + 1e-6)
    loan_usage_ratio = len(loans) / 5.0

    # delinquency
    is_delinquent_any = int(any(l.repayment_status.value == "OVERDUE" for l in loans))


    # -----------------------------------------------------
    # 최종 Feature dict (65개 완성)
    # -----------------------------------------------------
    return {
        "TOT_USE_AM_mean": TOT_USE_AM_mean,
        "TOT_USE_AM_max": TOT_USE_AM_max,
        "TOT_USE_AM_min": TOT_USE_AM_min,
        "TOT_USE_AM_std": TOT_USE_AM_std,

        "CRDSL_USE_AM_mean": CRDSL_USE_AM_mean,
        "CRDSL_USE_AM_std": CRDSL_USE_AM_std,

        "CNF_USE_AM_mean": CNF_USE_AM_mean,
        "CNF_USE_AM_std": CNF_USE_AM_std,

        "credit_ratio_mean": credit_ratio_mean,
        "credit_ratio_std": credit_ratio_std,
        "credit_ratio_last": credit_ratio_last,

        "check_ratio_mean": check_ratio_mean,
        "check_ratio_std": check_ratio_std,
        "check_ratio_last": check_ratio_last,

        "spend_growth_mean": spend_growth_mean,
        "spend_growth_std": spend_growth_std,
        "spend_growth_last": spend_growth_last,

        "spend_accel_mean": spend_accel_mean,
        "spend_accel_std": spend_accel_std,
        "spend_accel_last": spend_accel_last,

        "top3_ratio_sum_mean": top3_ratio_sum_mean,
        "top3_ratio_sum_std": top3_ratio_sum_std,
        "top3_ratio_sum_last": top3_ratio_sum_last,

        "top3_ratio_trend_mean": top3_ratio_trend_mean,
        "top3_ratio_trend_std": top3_ratio_trend_std,
        "top3_ratio_trend_last": top3_ratio_trend_last,

        "spending_entropy_mean": spending_entropy_mean,
        "spending_entropy_std": spending_entropy_std,
        "spending_entropy_last": spending_entropy_last,

        "AGE": age,
        "SEX_CD": SEX_CD,
        "MBR_RK": MBR_RK,

        "salary_mean": salary_mean,
        "salary_max": salary_max,
        "salary_min": salary_min,
        "salary_std": salary_std,

        "balance_mean": balance_mean,
        "balance_max": balance_max,
        "balance_min": balance_min,
        "balance_std": balance_std,

        "principal_amount_mean": principal_amount_mean,
        "principal_amount_max": principal_amount_max,
        "principal_amount_min": principal_amount_min,
        "principal_amount_std": principal_amount_std,

        "remaining_principal_mean": remaining_principal_mean,
        "remaining_principal_max": remaining_principal_max,
        "remaining_principal_min": remaining_principal_min,
        "remaining_principal_std": remaining_principal_std,

        "interest_rate_mean": interest_rate_mean,
        "interest_rate_max": interest_rate_max,
        "interest_rate_min": interest_rate_min,
        "interest_rate_std": interest_rate_std,

        "repayment_ratio_mean": repayment_ratio_mean,
        "loan_type_mean": loan_type_mean,
        "is_completed_mean": is_completed_mean,

        "balance_to_loan_ratio": balance_to_loan_ratio,
        "income_to_loan_ratio": income_to_loan_ratio,
        "debt_to_income_ratio": debt_to_income_ratio,
        "loan_usage_ratio": loan_usage_ratio,

        "is_delinquent_any": is_delinquent_any
    }

from sqlalchemy import (
    Column, Integer, BigInteger, String, Numeric, Boolean,
    DateTime, Enum, ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.orm import declarative_base
from datetime import datetime, timezone
import enum


# ============================================================
# BaseEntity
# ============================================================
Base = declarative_base()

class BaseEntity:
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    deleted_at = Column(DateTime, nullable=True)


# ============================================================
# ENUM 매핑
# ============================================================

class SexEnum(enum.Enum):
    MALE = 0
    FEMALE = 1

class CreditRatingEnum(enum.Enum):
    AAA = "AAA"
    AA = "AA"
    A = "A"
    B = "B"
    C = "C"
    D = "D"


class CustomerLevelEnum(enum.Enum):
    VVIP = "VVIP"
    VIP = "VIP"
    GOLD = "GOLD"
    SILVER = "SILVER"
    BRONZE = "BRONZE"

class TransactionTypeEnum(enum.Enum):
    ATM_DEPOSIT = "ATM_DEPOSIT"             # ATM 입금
    ATM_WITHDRAW = "ATM_WITHDRAW"           # ATM 출금
    TRANSFER_SEND = "TRANSFER_SEND"         # 송금(보내는 쪽)
    TRANSFER_RECEIVE = "TRANSFER_RECEIVE"   # 송금(받는 쪽)
    EXTERNAL_TRANSFER_SEND = "EXTERNAL_TRANSFER_SEND" # 타행 송금(보내는 쪽)
    CARD_PAYMENT = "CARD_PAYMENT"           # 카드 결제
    CARD_REFUND = "CARD_REFUND"             # 카드 환불
    LOAN_REPAYMENT = "LOAN_REPAYMENT"       # 대출 상환
    EARLY_REPAYMENT = "EARLY_REPAYMENT"     # 중도 상환


class ConsumptionCategoryEnum(enum.Enum):
    TRANSFER = "TRANSFER"           # 이체
    FOOD = "FOOD"                   # 식비
    TRANSPORT = "TRANSPORT"         # 교통
    SHOPPING = "SHOPPING"           # 쇼핑
    ENTERTAINMENT = "ENTERTAINMENT" # 엔터테인먼트
    ETC = "ETC"                     # 기타

class LoanTypeEnum(enum.Enum):
    CREDIT = "CREDIT"       # 신용
    MORTGAGE = "MORTGAGE"   # 담보

class LoanTransactionTypeEnum(enum.Enum):
    LATE_INTEREST = "LATE_INTEREST"
    LOAN = "LOAN"
    REPAYMENT = "REPAYMENT"
    

class RepaymentTypeEnum(enum.Enum):
    EQUAL_INSTALLMENT = "EQUAL_INSTALLMENT"   # 원리금균등
    EQUAL_PRINCIPAL = "EQUAL_PRINCIPAL"   # 원금균등
    BULLET = "BULLET"                     # 만기일시


class RepaymentStatusEnum(enum.Enum):
    NORMAL = "NORMAL"
    OVERDUE = "OVERDUE"
    TERMINATED = "TERMINATED"
    COMPLETED = "COMPLETED"


class InterestTypeEnum(enum.Enum):
    FIXED = "FIXED"
    VARIABLE = "VARIABLE"


# ======================================================
# User
# ======================================================

class User(Base, BaseEntity):
    __tablename__ = "user"
    
    user_id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    # sex_cd = Column(Enum(SexEnum), nullable=False)
    address = Column(String(255), nullable=False)
    birthday = Column(DateTime, nullable=False)
    job = Column(String(255), nullable=False)
    income = Column(Numeric(38, 2), nullable=False)
    credit_level = Column(Enum(CreditRatingEnum), nullable=False)
    customer_level = Column(Enum(CustomerLevelEnum), nullable=False)
    # user_auth_login_id = Column(String(255), unique=True, nullable=True)

    accounts = relationship("Account", back_populates="user")
    loan_ledgers = relationship("LoanLedger", back_populates="user")


# ============================================================
# Account
# ============================================================

class Account(Base, BaseEntity):
    __tablename__ = "account"
    
    account_id = Column(BigInteger, primary_key=True, autoincrement=True)
    account_number = Column(String(255), unique=True, nullable=False)
    user_id = Column(BigInteger, ForeignKey("user.user_id"), nullable=False)
    balance = Column(Numeric(38, 2), nullable=False, default=0)
    bank_code = Column(String(3), nullable=False)

    user = relationship("User", back_populates="accounts")

    account_transactions = relationship(
        "AccountTransaction",
        back_populates="account",
        cascade="all, delete-orphan"
    )

    card_transactions = relationship(
        "CardTransaction",
        back_populates="account",
        cascade="all, delete-orphan"
    )


# ============================================================
# AccountTransaction
# ============================================================

class AccountTransaction(Base, BaseEntity):
    __tablename__ = "transaction_account"

    trxaid = Column(BigInteger, primary_key=True, autoincrement=True)
    account_id = Column(
        BigInteger,
        ForeignKey("account.account_id"),
        nullable=False
    )
    type = Column(Enum(TransactionTypeEnum), nullable=False)
    amount = Column(Numeric(38, 2), nullable=False)
    balance_before = Column(Numeric(38, 2), nullable=False)
    balance_after = Column(Numeric(38, 2), nullable=False)
    destination_account = Column(String(20), nullable=True)
    is_income = Column(Boolean, nullable=False)
    account = relationship("Account", back_populates="account_transactions")


# ============================================================
# CardTransaction
# ============================================================

class CardTransaction(Base, BaseEntity):
    __tablename__ = "transaction_card"

    trxcid = Column(BigInteger, primary_key=True, autoincrement=True)
    account_id = Column(
        BigInteger,
        ForeignKey("account.account_id"),
        nullable=False
    )
    amount = Column(Numeric(38, 2), nullable=False)
    store_name = Column(String(50), nullable=True)
    category = Column(Enum(ConsumptionCategoryEnum))

    account = relationship("Account", back_populates="card_transactions")

# ============================================================
# InterestRate
# ============================================================

class InterestRate(Base, BaseEntity):
    __tablename__ = "interest_rate"

    interest_rate_id = Column(BigInteger, primary_key=True, autoincrement=True)
    loan_product_id = Column(
        BigInteger,
        ForeignKey("loan_product.loan_product_id"),
        nullable=False
    )
    base_interest = Column(Numeric(38, 2), nullable=False)
    add_interest = Column(Numeric(38, 2), nullable=False)
    limit_prefer_interest = Column(Numeric(38, 2), nullable=False)

    loan_product = relationship("LoanProduct", back_populates="interest_rates")


# ======================================================
# PreferInterest
# ======================================================

class PreferInterest(Base):
    __tablename__ = "prefer_interest"

    # 복합키 구성 (EmbeddedId 대체)
    credit_rating = Column(Enum(CreditRatingEnum), primary_key=True)
    customer_level = Column(Enum(CustomerLevelEnum), primary_key=True)

    # 우대 금리
    prefer_interest = Column(Numeric(38, 2), nullable=False)

    def __init__(self, credit_rating, customer_level, prefer_interest):
        self.credit_rating = credit_rating
        self.customer_level = customer_level
        self.prefer_interest = prefer_interest


# ======================================================
# LoanProduct
# ======================================================

class LoanProduct(Base, BaseEntity):
    __tablename__ = "loan_product"

    loan_product_id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    type = Column(Enum(LoanTypeEnum), nullable=False)

    loan_ledgers = relationship("LoanLedger", back_populates="loan_product")
    interest_rates = relationship(
        "InterestRate",
        back_populates="loan_product",
        cascade="all, delete-orphan"
    )

# ======================================================
# LoanTransaction
# ======================================================

class LoanTransaction(Base):
    __tablename__ = "loan_transaction"

    trxlid = Column(BigInteger, primary_key=True, autoincrement=True)

    amount = Column(Numeric(38, 2), nullable=False)
    date = Column(DateTime, nullable=False)
    remain_principal = Column(Numeric(38, 2), nullable=False)

    repayment_interest_amount = Column(Numeric(38, 2), nullable=True)
    repayment_principal_amount = Column(Numeric(38, 2), nullable=True)
    transaction_type = Column(Enum(LoanTransactionTypeEnum),nullable=False)
    loan_ledger_id = Column(
        BigInteger, 
        ForeignKey("loan_ledger.loan_ledger_id"), 
        nullable=False
    )

    loan_ledger = relationship("LoanLedger", back_populates="loan_transactions")



# ======================================================
# LoanLedger
# ======================================================

class LoanLedger(Base, BaseEntity):
    __tablename__ = "loan_ledger"

    loan_ledger_id = Column(BigInteger, primary_key=True, autoincrement=True)
    loan_product_id = Column(BigInteger, ForeignKey("loan_product.loan_product_id"), nullable=False)
    user_id = Column(BigInteger, ForeignKey("user.user_id"), nullable=False)
    completed_interest = Column(Numeric(38, 2), nullable=False)
    principal = Column(Numeric(38, 2), nullable=False)
    remain_principal = Column(Numeric(38, 2), nullable=False)
    repayment_type = Column(Enum(RepaymentTypeEnum), nullable=False)
    repayment_status = Column(Enum(RepaymentStatusEnum), nullable=False)
    interest_type = Column(Enum(InterestTypeEnum), nullable=False)
    early_repay_interest_rate = Column(Numeric(38, 2), nullable=False)
    next_repayment_date = Column(DateTime)
    last_repayment_date = Column(DateTime)
    loan_end_date = Column(DateTime, nullable=False)
    overdue_count = Column(Integer, nullable=False)
    term = Column(Integer, nullable=False)
    account_id = Column(
        BigInteger,
        ForeignKey("account.account_id"),
        nullable=True,
        unique=True
    )

    loan_product = relationship("LoanProduct", back_populates="loan_ledgers")
    user = relationship("User", back_populates="loan_ledgers")
    account = relationship("Account")
    loan_transactions = relationship("LoanTransaction", back_populates="loan_ledger")


# ======================================================
# LoanFeatures
# ======================================================

class LoanFeatures(Base):
    __tablename__ = "loan_features"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    loan_ledger_id = Column(BigInteger, nullable=False)
    user_id = Column(BigInteger, nullable=False)

    created_at = Column(DateTime)

    TOT_USE_AM_mean = Column(Numeric(20, 6))
    TOT_USE_AM_max = Column(Numeric(20, 6))
    TOT_USE_AM_min = Column(Numeric(20, 6))
    TOT_USE_AM_std = Column(Numeric(20, 6))

    CRDSL_USE_AM_mean = Column(Numeric(20, 6))
    CRDSL_USE_AM_std = Column(Numeric(20, 6))

    CNF_USE_AM_mean = Column(Numeric(20, 6))
    CNF_USE_AM_std = Column(Numeric(20, 6))

    credit_ratio_mean = Column(Numeric(20, 6))
    credit_ratio_std = Column(Numeric(20, 6))
    credit_ratio_last = Column(Numeric(20, 6))

    check_ratio_mean = Column(Numeric(20, 6))
    check_ratio_std = Column(Numeric(20, 6))
    check_ratio_last = Column(Numeric(20, 6))

    spend_growth_mean = Column(Numeric(20, 6))
    spend_growth_std = Column(Numeric(20, 6))
    spend_growth_last = Column(Numeric(20, 6))

    spend_accel_mean = Column(Numeric(20, 6))
    spend_accel_std = Column(Numeric(20, 6))
    spend_accel_last = Column(Numeric(20, 6))

    top3_ratio_sum_mean = Column(Numeric(20, 6))
    top3_ratio_sum_std = Column(Numeric(20, 6))
    top3_ratio_sum_last = Column(Numeric(20, 6))

    top3_ratio_trend_mean = Column(Numeric(20, 6))
    top3_ratio_trend_std = Column(Numeric(20, 6))
    top3_ratio_trend_last = Column(Numeric(20, 6))

    spending_entropy_mean = Column(Numeric(20, 6))
    spending_entropy_std = Column(Numeric(20, 6))
    spending_entropy_last = Column(Numeric(20, 6))

    AGE = Column(Integer)
    SEX_CD = Column(Integer)
    MBR_RK = Column(String(10))

    salary_mean = Column(Numeric(20, 6))
    salary_max = Column(Numeric(20, 6))
    salary_min = Column(Numeric(20, 6))
    salary_std = Column(Numeric(20, 6))

    balance_mean = Column(Numeric(20, 6))
    balance_max = Column(Numeric(20, 6))
    balance_min = Column(Numeric(20, 6))
    balance_std = Column(Numeric(20, 6))

    principal_amount_mean = Column(Numeric(20, 6))
    principal_amount_max = Column(Numeric(20, 6))
    principal_amount_min = Column(Numeric(20, 6))
    principal_amount_std = Column(Numeric(20, 6))

    remaining_principal_mean = Column(Numeric(20, 6))
    remaining_principal_max = Column(Numeric(20, 6))
    remaining_principal_min = Column(Numeric(20, 6))
    remaining_principal_std = Column(Numeric(20, 6))

    interest_rate_mean = Column(Numeric(20, 6))
    interest_rate_max = Column(Numeric(20, 6))
    interest_rate_min = Column(Numeric(20, 6))
    interest_rate_std = Column(Numeric(20, 6))

    repayment_ratio_mean = Column(Numeric(20, 6))
    loan_type_mean = Column(Numeric(20, 6))
    is_completed_mean = Column(Numeric(20, 6))

    balance_to_loan_ratio = Column(Numeric(20, 6))
    income_to_loan_ratio = Column(Numeric(20, 6))
    debt_to_income_ratio = Column(Numeric(20, 6))
    loan_usage_ratio = Column(Numeric(20, 6))
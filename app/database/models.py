from sqlalchemy import (
    Column, Integer, BigInteger, String, Numeric, Boolean,
    DateTime, Enum, ForeignKey
)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.connection import Base
import enum


# ============================================================
# BaseEntity
# ============================================================
class BaseEntity:
    created_at = Column(DateTime, default=datetime.now(datetime.timezone.gmt))
    updated_at = Column(DateTime, default=datetime.now(datetime.timezone.gmt), onupdate=datetime.now(datetime.timezone.gmt))
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
    

class RepaymentTypeEnum(enum.Enum):
    EQUAL_INSTALLMENT = "EQUAL_PAYMENT"   # 원리금균등
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
# LoanLedger
# ======================================================

class User(Base, BaseEntity):
    __tablename__ = "user"
    
    user_id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    sex_cd = Column(Enum(SexEnum), nullable=False)
    address = Column(String(200), nullable=False)
    birthday = Column(DateTime, nullable=False)
    job = Column(String(50), nullable=False)
    income = Column(BigInteger, nullable=False)
    credit_level = Column(Enum(CreditRatingEnum), nullable=False)
    customer_level = Column(Enum(CustomerLevelEnum), nullable=False)

    accounts = relationship("Account", back_populates="user")
    loan_ledgers = relationship("LoanLedger", back_populates="user")


# ============================================================
# Account
# ============================================================

class Account(Base, BaseEntity):
    __tablename__ = "account"
    
    account_id = Column(BigInteger, primary_key=True, autoincrement=True)
    account_number = Column(String(50), unique=True, nullable=False)
    user_id = Column(String(50), ForeignKey("User.user_id"), nullable=False)
    balance = Column(Numeric(precision=18, scale=2), nullable=False, default=0)
    bank_code = Column(String(3), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

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

    trx_a_id = Column(BigInteger, primary_key=True, autoincrement=True)
    account_id = Column(
        BigInteger,
        ForeignKey("account.account_id"),
        nullable=False
    )
    type = Column(Enum(TransactionTypeEnum), nullable=False)
    amount = Column(Numeric(18, 2), nullable=False)
    balance_before = Column(Numeric(18, 2), nullable=False)
    balance_after = Column(Numeric(18, 2), nullable=False)
    destination_account = Column(String(20), nullable=True)
    is_income = Column(Boolean, nullable=False)
    created_at = Column(DateTime, default=datetime.now(datetime.timezone.gmt))
    account = relationship("Account", back_populates="account_transactions")


# ============================================================
# CardTransaction
# ============================================================

class CardTransaction(Base, BaseEntity):
    __tablename__ = "transaction_card"

    trx_c_id = Column(BigInteger, primary_key=True, autoincrement=True)
    account_id = Column(
        BigInteger,
        ForeignKey("account.account_id"),
        nullable=False
    )
    amount = Column(Numeric(18, 2), nullable=False)
    store_name = Column(String(50))
    category = Column(Enum(ConsumptionCategoryEnum))
    created_at = Column(DateTime, default=datetime.now(datetime.timezone.gmt))

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
    base_interest = Column(Numeric(10, 4), nullable=False)
    add_interest = Column(Numeric(10, 4), nullable=False)
    limit_prefer_interest = Column(Numeric(10, 4), nullable=False)

    loan_product = relationship("LoanProduct", back_populates="interest_rates")

# ======================================================
# LoanProduct
# ======================================================

class LoanProduct(Base, BaseEntity):
    __tablename__ = "loan_product"

    loan_product_id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    type = Column(Enum(LoanTypeEnum), nullable=False)

    loan_ledgers = relationship("LoanLedger", back_populates="loan_product")
    interest_rates = relationship(
        "InterestRate",
        back_populates="loan_product",
        cascade="all, delete-orphan"
    )

# ======================================================
# LoanLedger
# ======================================================

class LoanLedger(Base, BaseEntity):
    __tablename__ = "loan_ledger"

    loan_ledger_id = Column(BigInteger, primary_key=True, autoincrement=True)
    loan_product_id = Column(
        BigInteger,
        ForeignKey("loan_product.loan_product_id"),
        nullable=False
    )
    user_id = Column(
        String(50),
        ForeignKey("User.user_id"),
        nullable=False
    )
    completed_interest = Column(Numeric(18, 4), nullable=False)
    principal = Column(Numeric(18, 2), nullable=False)
    remain_principal = Column(Numeric(18, 2), nullable=False)
    repayment_type = Column(Enum(RepaymentTypeEnum), nullable=False)
    repayment_status = Column(Enum(RepaymentStatusEnum), nullable=False)
    interest_type = Column(Enum(InterestTypeEnum), nullable=False)
    early_repay_interest_rate = Column(Numeric(10, 4), nullable=False)
    next_repayment_date = Column(DateTime)
    last_repayment_date = Column(DateTime)
    loan_end_date = Column(DateTime, nullable=False)
    overdue_count = Column(BigInteger, nullable=False)
    term = Column(BigInteger, nullable=False)
    account_id = Column(
        BigInteger,
        ForeignKey("account.account_id"),
        nullable=True
    )

    loan_product = relationship("LoanProduct", back_populates="loan_ledgers")
    user = relationship("User", back_populates="loan_ledgers")
    account = relationship("Account")
    loan_transactions = relationship("LoanTransaction", back_populates="loan_ledger")
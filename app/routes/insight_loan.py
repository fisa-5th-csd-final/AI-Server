from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.database.connection import get_core_db
from app.database.models import LoanLedger, LoanProduct, InterestRate
from app.services.llm.llm_service_loan import generate_loan_comment

router = APIRouter()


class LoanInsightRequest(BaseModel):
    loan_ledger_id: int = Field(..., description="분석할 loan_ledger_id")


class LoanInsightResponse(BaseModel):
    loan_name: str = Field(..., description="대출 상품명")
    comment: str = Field(..., description="LLM이 생성한 분석 코멘트")
    model_version: str = Field(..., description="LLM 모델 버전")


@router.post("/insight/loan", response_model=LoanInsightResponse)
def insight_loan(request: LoanInsightRequest, db: Session = Depends(get_core_db)):
    """
    POST 방식 loan_ledger_id 기반 대출 분석 API
    """

    loan_ledger_id = request.loan_ledger_id

    # -----------------------------
    # loan_ledger 조회
    # -----------------------------
    ledger: LoanLedger = (
        db.query(LoanLedger)
        .filter(LoanLedger.loan_ledger_id == loan_ledger_id)
        .first()
    )

    if ledger is None:
        raise HTTPException(404, detail="해당 loan_ledger_id의 대출 정보가 없습니다.")

    # -----------------------------
    # 대출 상품 정보 조회
    # -----------------------------
    product: LoanProduct = ledger.loan_product

    if product is None:
        raise HTTPException(500, detail="대출 상품 정보가 존재하지 않습니다.")

    # -----------------------------
    # 금리 정보 조회
    # -----------------------------
    interest: InterestRate = (
        db.query(InterestRate)
        .filter(InterestRate.loan_product_id == ledger.loan_product_id)
        .first()
    )

    if interest is None:
        raise HTTPException(500, detail="금리 정보가 존재하지 않습니다.")

    # 실 금리 계산
    real_interest = float(
        interest.base_interest +
        interest.add_interest -
        interest.limit_prefer_interest
    )

    # -----------------------------
    # 상환 진척률
    # -----------------------------
    total_principal = float(ledger.principal)
    remain_principal = float(ledger.remain_principal)

    repayment_ratio = (
        (1 - remain_principal / total_principal) * 100
        if total_principal > 0 else 0.0
    )

    # -----------------------------
    # 연체 확률 (임시 계산)
    # -----------------------------
    delinquency_probability = min(ledger.overdue_count * 0.05, 1.0)

    # -----------------------------
    # 다음 납입일
    # -----------------------------
    next_due_date = (
        ledger.next_repayment_date.strftime("%Y-%m-%d")
        if ledger.next_repayment_date else ""
    )

    # -----------------------------
    # LLM 입력 데이터 생성
    # -----------------------------
    loan_data = {
        "loan_name": product.name,
        "interest_rate": real_interest,
        "repayment_ratio": repayment_ratio,
        "delinquency_probability": delinquency_probability,
        "next_due_date": next_due_date,
        "remaining_principal": remain_principal,
        "principal_amount": total_principal,
    }

    # -----------------------------
    # LLM 코멘트 생성
    # -----------------------------
    try:
        comment = generate_loan_comment(loan_data)
    except Exception:
        comment = "대출 분석 중 오류가 발생했습니다."

    return LoanInsightResponse(
        loan_name=product.name,
        comment=comment,
        model_version="phi3-mini-4k-instruct"
    )

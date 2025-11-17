from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.database.connection import get_core_db
from app.database.models import LoanLedger, LoanProduct, InterestRate
from app.services.llm_service_loan import generate_loan_comment

router = APIRouter()

class LoanInsightRequest(BaseModel):
    user_id: int = Field(..., description="대출 정보를 조회할 사용자 ID")

class LoanCommentItem(BaseModel):
    loan_name: str
    comment: str

class LoanInsightResponse(BaseModel):
    loans: list[LoanCommentItem]
    model_version: str


@router.post("/insight/loan", response_model=LoanInsightResponse)
def insight_loan(request: LoanInsightRequest, db: Session = Depends(get_core_db)):

    # 사용자 대출 전체 조회
    ledgers: list[LoanLedger] = (
        db.query(LoanLedger)
        .filter(LoanLedger.user_id == request.user_id)
        .all()
    )

    if not ledgers:
        raise HTTPException(status_code=404, detail="해당 사용자의 대출 정보가 없습니다.")

    loan_items = []

    # 각 대출에 대해 코멘트 생성
    for ledger in ledgers:

        product: LoanProduct = ledger.loan_product
        if product is None:
            continue  # 비정상 데이터 스킵

        # 금리 조회
        interest = (
            db.query(InterestRate)
            .filter(InterestRate.loan_product_id == ledger.loan_product_id)
            .first()
        )
        if interest is None:
            continue

        # 실 금리 계산
        real_interest = float(
            interest.base_interest
            + interest.add_interest
            - interest.limit_prefer_interest
        )

        # 상환 진척률 계산
        total_principal = float(ledger.principal)
        remain_principal = float(ledger.remain_principal)

        repayment_ratio = (
            (1 - remain_principal / total_principal) * 100
            if total_principal > 0 else 0.0
        )

        # 연체 확률 (prototype)
        delinquency_probability = min(ledger.overdue_count * 0.05, 1.0)

        next_due = (
            ledger.next_repayment_date.strftime("%Y-%m-%d")
            if ledger.next_repayment_date else ""
        )

        # LLM 입력 데이터
        loan_data = {
            "loan_name": product.name,
            "interest_rate": real_interest,
            "repayment_ratio": repayment_ratio,
            "delinquency_probability": delinquency_probability,
            "next_due_date": next_due,
            "remaining_principal": remain_principal,
            "principal_amount": total_principal,
        }

        # LLM 호출
        try:
            comment = generate_loan_comment(loan_data)
        except Exception:
            comment = "대출 정보를 분석하는 중 오류가 발생했습니다."

        loan_items.append(
            LoanCommentItem(
                loan_name=product.name,
                comment=comment
            )
        )

    return LoanInsightResponse(
        loans=loan_items,
        model_version="phi3-mini-4k-instruct"
    )

from app.services.llm_loader import get_generator

generator = get_generator()

def generate_loan_comment(data: dict) -> str:
    loan_name = data.get("loan_name", "대출 상품")
    rate = data.get("interest_rate", 0)
    repay = data.get("repayment_ratio", 0)
    delinquency = data.get("delinquency_probability", 0)
    due = data.get("next_due_date", "")
    remain = data.get("remaining_principal", 0)
    total = data.get("principal_amount", 0)

    prompt = (
        f"다음 대출 정보를 보고 사용자의 상태를 짧고 구체적으로 설명하는 코멘트를 작성하세요. "
        f"1~2문장 이내로, 친절하지만 간결하게.\n\n"
        f"[대출 정보]\n"
        f"- 상품명: {loan_name}\n"
        f"- 금리: {rate}%\n"
        f"- 상환진척률: {repay}%\n"
        f"- 연체확률: {delinquency}\n"
        f"- 다음 납입일: {due}\n"
        f"- 남은 원금: {remain}원 / 총 원금: {total}원\n\n"
        f"[출력 예시]\n"
        f"- 납입 진척률이 높고 연체 위험이 낮아 안정적인 상환 상태입니다.\n"
        f"- 금리가 다소 높지만, 상환이 꾸준해 긍정적입니다.\n\n"
        f"코멘트:"
    )

    result = generator(prompt, max_new_tokens=60, temperature=0.7, do_sample=True)
    comment = result[0]["generated_text"].split("코멘트:")[-1].strip()
    return comment

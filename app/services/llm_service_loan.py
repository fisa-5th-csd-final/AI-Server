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

    # === 영어 기반 프롬프트 ===
    prompt = f"""
You are a financial assistant who writes short, natural comments in Korean for banking apps.
Analyze the loan information below and write a concise comment (1–2 sentences) describing
the customer's repayment and risk status. The tone should be warm, professional, and encouraging.

[Loan Information]
- Loan Product: {loan_name}
- Interest Rate: {rate:.2f}%
- Repayment Progress: {repay:.1f}%
- Delinquency Probability: {delinquency:.2f}
- Next Due Date: {due}
- Remaining Principal: {remain:,.0f}원
- Total Principal: {total:,.0f}원

Instructions:
1. Write in **Korean**.
2. Keep it **1–2 sentences long**.
3. Mention repayment stability or risk clearly.
4. If the delinquency probability is high (>0.7), include a gentle warning.
5. Do NOT use markdown, lists, or English words in the output.

Example outputs:
- 상환 진척률이 높고 연체 위험이 낮아 안정적인 상태입니다.
- 금리가 다소 높지만 상환이 꾸준해 긍정적입니다.
- 연체 위험이 다소 있으니 납입일을 놓치지 않도록 주의하세요.

Output:
Comment (in Korean):
""".strip()

    result = generator(
        prompt,
        max_new_tokens=70,
        temperature=0.6,  # 문체 안정화
        top_p=0.9,
        do_sample=True
    )

    # 결과 텍스트 정제
    text = result[0]["generated_text"]
    comment = text.split("Comment (in Korean):")[-1].strip().split("\n")[0]

    if not comment or len(comment) < 5:
        comment = "대출 상환이 안정적으로 진행되고 있습니다."

    return comment

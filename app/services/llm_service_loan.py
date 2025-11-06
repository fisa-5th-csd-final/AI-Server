from app.services.llm_loader import safe_generate

def generate_loan_comment(data: dict) -> str:
    loan_name = data.get("loan_name", "대출 상품")
    rate = data.get("interest_rate", 0)
    repay = data.get("repayment_ratio", 0)
    delinquency = data.get("delinquency_probability", 0)
    due = data.get("next_due_date", "")
    remain = data.get("remaining_principal", 0)
    total = data.get("principal_amount", 0)

    messages = [
        {
            "role": "system",
            "content": (
                "You are a financial assistant for a Korean retail banking app. "
                "Write short, polite, and natural comments in Korean (~습니다 style). "
                "Avoid redundant phrases such as '즉', '따라서', '결과적으로'. "
                "The comment should sound like a professional banking insight, not a report."
            ),
        },
        {
            "role": "user",
            "content": (
                f"[Loan Information]\n"
                f"- Loan Product: {loan_name}\n"
                f"- Interest Rate: {rate:.2f}%\n"
                f"- Repayment Progress: {repay:.1f}%\n"
                f"- Delinquency Probability: {delinquency:.2f}\n"
                f"- Next Due Date: {due}\n"
                f"- Remaining Principal: {remain:,.0f}원 / Total: {total:,.0f}원\n\n"
                "Output Rules:\n"
                "1. Respond only in Korean.\n"
                "2. Write exactly one or two sentences.\n"
                "3. Be concise and avoid repeated or filler words.\n"
                "4. Use clear, factual tone (~습니다 style).\n"
                "5. Do not use connectors like '즉', '따라서', '결과적으로'.\n"
                "6. End with a full Korean sentence.\n\n"
                "Example outputs:\n"
                "- 상환 진척률이 높고 연체 위험이 낮아 안정적인 상태입니다.\n"
                "- 연체 가능성이 있어 납입 일정을 꾸준히 유지하는 것이 좋습니다.\n\n"
                "Answer:"
            ),
        },
    ]

    result = safe_generate(messages, max_new_tokens=250, temperature=0.4, top_p=0.9, do_sample=False)

    text = ""
    if isinstance(result, list):
        if isinstance(result[0], dict):
            gen_text = result[0].get("generated_text", "")
            if isinstance(gen_text, list) and len(gen_text) > 0:
                last_msg = gen_text[-1]
                if isinstance(last_msg, dict) and "content" in last_msg:
                    text = last_msg["content"]
                else:
                    text = str(last_msg)
            else:
                text = str(gen_text)
    elif isinstance(result, dict):
        text = result.get("generated_text", "")
    elif isinstance(result, str):
        text = result

    if not isinstance(text, str):
        text = str(text)

    comment = text.strip().split("\n")[0].replace("�", "").strip()
    if len(comment) < 5:
        comment = "대출 상환이 안정적으로 진행되고 있습니다."

    return comment

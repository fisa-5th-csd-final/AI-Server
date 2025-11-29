from app.services.llm.llm_loader import safe_generate

def generate_loan_comment(data: dict) -> str:
    # 안전한 값 세팅
    loan_name = str(data.get("loan_name", "대출 상품"))
    rate = float(data.get("interest_rate", 0) or 0)
    repay = float(data.get("repayment_ratio", 0) or 0)
    delinquency = float(data.get("delinquency_probability", 0) or 0)
    due = data.get("next_due_date") or ""
    remain = float(data.get("remaining_principal", 0) or 0)
    total = float(data.get("principal_amount", 0) or 0)

    messages = [
        {
            "role": "system",
            "content": (
                "You are a financial assistant for a Korean retail banking app. "
                "Write a short, professional, concise financial comment in Korean (~습니다). "
                "Avoid redundant connectors such as '즉', '따라서', '결과적으로'. "
                "Output must be natural, factual, and limited to one or two sentences."
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
                "1) Respond only in Korean.\n"
                "2) Output must be exactly one or two sentences.\n"
                "3) Avoid repetitive or filler words.\n"
                "4) Use a professional tone (~습니다).\n"
                "5) Do NOT use '즉', '따라서', '결과적으로'.\n"
                "6) End with a complete Korean sentence.\n\n"
                "Example outputs:\n"
                "- 상환 진척률이 높아 안정적인 상태입니다.\n"
                "- 연체 확률이 다소 있어 납입 일정을 유지하는 것이 좋습니다.\n\n"
                "Answer:"
            ),
        },
    ]

    # LLM 호출
    try:
        result = safe_generate(
            messages, 
            max_new_tokens=150,
            temperature=0.4,
            top_p=0.9,
            do_sample=False
        )
    except Exception:
        return "대출 정보를 분석하는 중 오류가 발생했습니다."

    # 반환 파싱 단순화
    text = extract_text_from_llm_result(result)

    # 후처리
    comment = (text or "").strip().split("\n")[0].strip()
    comment = comment.replace("�", "")  # 깨진 문자 제거

    # 너무 짧으면 fallback
    if len(comment) < 5:
        comment = "대출 상환이 안정적으로 진행되고 있습니다."

    return comment


def extract_text_from_llm_result(result):
    """
    safe_generate() 반환 형태가 리스트/딕셔너리/문자열 등 다양할 수 있으므로
    이를 안전하게 문자열만 추출하는 헬퍼 함수.
    """
    # 문자열이면 바로 반환
    if isinstance(result, str):
        return result

    # 딕셔너리 형태: {"generated_text": "..."} 또는 {"generated_text": [{"content": "..."}]}
    if isinstance(result, dict):
        gen = result.get("generated_text")
        if isinstance(gen, str):
            return gen
        if isinstance(gen, list) and len(gen) > 0:
            last = gen[-1]
            if isinstance(last, dict) and "content" in last:
                return last["content"]
            return str(last)

    # 리스트 형태
    if isinstance(result, list) and len(result) > 0:
        first = result[0]

        if isinstance(first, str):
            return first
        if isinstance(first, dict):
            gen = first.get("generated_text")
            if isinstance(gen, str):
                return gen
            if isinstance(gen, list) and len(gen) > 0:
                last = gen[-1]
                if isinstance(last, dict) and "content" in last:
                    return last["content"]
                return str(last)

    # 모두 실패 → 빈 문자열
    return ""

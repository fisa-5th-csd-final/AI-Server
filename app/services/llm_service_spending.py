from app.services.llm_loader import safe_generate

def generate_spending_comment(
    spending_data: dict,
    avg_spending_data: dict,
    peer_age: str = "20대 후반",
    peer_income_range: str = "월 300~400만 원대"
) -> str:
    """
    사용자 소비 데이터를 또래 평균 소비 데이터와 비교하여 코멘트를 생성합니다.
    예: '20대 후반, 월 300~400만 원대 소비자 평균보다 식비를 12% 더 많이 쓰셨습니다.'
    """

    # 수입 및 소비 항목 분리
    salary = spending_data.get("income", 0)
    spending = {k: v for k, v in spending_data.items() if k != "income"}
    peer_spending = avg_spending_data or {}

    total_spend = sum(spending.values())
    ratio = round(total_spend / salary, 2) if salary else 0

    # 전체 소비 비교
    peer_total = sum(peer_spending.values()) if peer_spending else 0
    peer_info = ""
    if peer_total > 0:
        diff = total_spend - peer_total
        pct_diff = (diff / peer_total * 100)
        peer_info = f"또래 평균 대비 {abs(pct_diff):.1f}% {'많이' if pct_diff > 0 else '적게'} 소비"

    # 카테고리별 비교
    category_diffs = {}
    for cat, val in spending.items():
        peer_val = peer_spending.get(cat, 0)
        if peer_val > 0:
            pct = (val - peer_val) / peer_val * 100
            category_diffs[cat] = pct

    if category_diffs:
        top_diff_cat = max(category_diffs, key=lambda k: abs(category_diffs[k]))
        top_diff_val = category_diffs[top_diff_cat]
        peer_summary = f"{top_diff_cat} 항목에서 또래보다 {abs(top_diff_val):.1f}% {'많이' if top_diff_val > 0 else '적게'} 사용"
    else:
        peer_summary = "카테고리 비교 정보 없음"

    # 가장 지출 많은 항목
    top_category = max(spending, key=spending.get)
    top_amount = spending[top_category]

    # LLM 프롬프트
    messages = [
        {
            "role": "system",
            "content": (
                "You are a financial advisor for a Korean personal finance app. "
                "Write short, polite, and natural comments in Korean (~습니다 style). "
                "Summarize how the user's spending compares to their peer group. "
                "Avoid redundant connectors like '즉', '따라서', '결과적으로'. "
                "Keep the tone factual, clear, and concise — similar to a banking app insight."
            ),
        },
        {
            "role": "user",
            "content": (
                f"[User Info]\n"
                f"- Monthly Income: {salary:,.0f}원\n"
                f"- Total Spending: {total_spend:,.0f}원 ({ratio*100:.1f}% of income)\n"
                f"- Top Spending Category: {top_category} ({top_amount:,.0f}원)\n"
                f"- Peer Group: {peer_age}, {peer_income_range}\n"
                f"- Peer Comparison: {peer_info or '정보 없음'}\n"
                f"- Key Peer Category: {peer_summary or '정보 없음'}\n\n"
                "[User Category Breakdown]\n" +
                "\n".join([f"- {cat}: {val:,.0f}원" for cat, val in spending.items()]) +
                ("\n\n[Peer Average Spending]\n" + "\n".join(
                    [f"- {cat}: {val:,.0f}원" for cat, val in peer_spending.items()]
                ) if peer_spending else "") +
                "\n\nOutput Rules:\n"
                "1. Respond only in Korean.\n"
                "2. Write 1–2 sentences.\n"
                "3. Always include the peer group in the sentence (예: '20대 후반, 월 300~400만 원대 소비자 평균보다...').\n"
                "4. Mention categories that stand out (높거나 낮은 항목).\n"
                "5. Use a polite and factual tone (~습니다 style).\n"
                "6. Avoid '즉', '따라서', '결과적으로'.\n\n"
                "Example outputs:\n"
                "- 20대 후반, 월 300~400만 원대 소비자 평균과 비슷한 수준입니다.\n"
                "- 20대 후반, 월 300~400만 원대 평균보다 식비가 10% 높으며, 교통비는 평균보다 낮습니다.\n\n"
                "Answer:"
            ),
        },
    ]

    # LLM 호출
    result = safe_generate(messages, max_new_tokens=250, temperature=0.4, top_p=0.9, do_sample=False)

    # 결과 정제
    text = ""
    if isinstance(result, list):
        if isinstance(result[0], dict):
            gen_text = result[0].get("generated_text", "")
            if isinstance(gen_text, list) and len(gen_text) > 0:
                last_msg = gen_text[-1]
                text = last_msg.get("content", str(last_msg)) if isinstance(last_msg, dict) else str(last_msg)
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
        comment = f"{peer_age}, {peer_income_range} 소비자 평균과 유사한 수준입니다."

    return comment

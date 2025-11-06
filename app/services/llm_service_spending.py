from app.services.llm_loader import safe_generate

def generate_spending_comment(salary: float, spending: dict, prev_spending: dict = None) -> str:
    total_spend = sum(spending.values())
    ratio = round(total_spend / salary, 2) if salary else 0

    prev_info = ""
    if prev_spending:
        prev_total = sum(prev_spending.values())
        diff = total_spend - prev_total
        pct_change = (diff / prev_total * 100) if prev_total else 0
        prev_info = f"전월 대비 {abs(pct_change):.1f}% {'증가' if diff > 0 else '감소'}"

    top_category = max(spending, key=spending.get)
    top_amount = spending[top_category]

    messages = [
        {
            "role": "system",
            "content": (
                "You are a financial advisor for a Korean personal finance app. "
                "Write short, polite, and natural comments in Korean (~습니다 style). "
                "The goal is to summarize spending trends briefly. "
                "Avoid redundant connectors like '즉', '따라서', '결과적으로'. "
                "Keep the tone factual and concise, like a mobile banking insight."
            ),
        },
        {
            "role": "user",
            "content": (
                f"[User Info]\n"
                f"- Monthly Income: {salary:,.0f}원\n"
                f"- Total Spending: {total_spend:,.0f}원 ({ratio*100:.1f}% of income)\n"
                f"- Top Spending Category: {top_category} ({top_amount:,.0f}원)\n"
                f"- Change from Last Month: {prev_info or '정보 없음'}\n\n"
                "[Category Breakdown]\n" +
                "\n".join([f"- {cat}: {val:,.0f}원" for cat, val in spending.items()]) +
                "\n\nOutput Rules:\n"
                "1. Respond only in Korean.\n"
                "2. Write 1–2 sentences.\n"
                "3. Mention key categories that increased or decreased.\n"
                "4. Avoid '즉', '따라서', '결과적으로' and repetitive expressions.\n"
                "5. Use a polite and factual tone (~습니다 style).\n\n"
                "Example outputs:\n"
                "- 외식비가 지난달보다 다소 늘었지만 교통비는 안정적인 수준입니다.\n"
                "- 소비가 안정적으로 유지되고 있습니다. 외식비는 다소 줄었습니다.\n\n"
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
        comment = "소비 패턴이 안정적으로 유지되고 있습니다."

    return comment

from app.services.llm_loader import get_generator

generator = get_generator()

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

    # ===== 영어 기반 prompt =====
    prompt = f"""
You are a smart financial assistant for a Korean banking app.
Analyze the user's monthly spending pattern and write a short comment in **Korean** (1–2 sentences).
Be natural, clear, and slightly friendly — like an app insight message.

[User Information]
- Monthly Income: {salary:,.0f}원
- Total Spending: {total_spend:,.0f}원 ({ratio*100:.1f}% of income)
- Top Spending Category: {top_category} ({top_amount:,.0f}원)
- Change from Last Month: {prev_info or "정보 없음"}

[Category Breakdown]
""" + "\n".join([f"- {cat}: {val:,.0f}원" for cat, val in spending.items()]) + """

Instructions:
1. Write 1–2 short sentences in Korean.
2. Mention key categories that changed (e.g., 외식, 교통비, 쇼핑).
3. Avoid markdown, bullet points, or English words.
4. If spending increased significantly, include a mild advisory tone.
5. If spending is stable, write a positive, encouraging comment.

Example outputs:
- 외식비가 지난달보다 다소 늘었어요. 교통비는 안정적인 수준이에요.
- 소비가 안정적으로 유지되고 있습니다. 외식비는 다소 줄었어요.

Output:
Comment (in Korean):
""".strip()

    result = generator(
        prompt,
        max_new_tokens=70,
        temperature=0.6,  # 낮출수록 문체 안정적
        top_p=0.9,
        do_sample=True,
    )

    # ===== 결과 정제 =====
    text = result[0]["generated_text"]
    comment = text.split("Comment (in Korean):")[-1].strip().split("\n")[0]

    if not comment or len(comment) < 5:
        comment = "소비 패턴이 안정적으로 유지되고 있습니다."

    return comment

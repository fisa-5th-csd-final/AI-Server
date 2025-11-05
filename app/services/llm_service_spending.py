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
        prev_info = f"전월 대비 {pct_change:.1f}% {'증가' if diff > 0 else '감소'}했습니다.\n"

    top_category = max(spending, key=spending.get)
    top_amount = spending[top_category]

    prompt = (
        f"다음 사용자의 소비 내역을 분석하여 짧고 구체적인 코멘트를 작성하세요. "
        f"전체 소비 비중과 주요 카테고리를 함께 언급하세요.\n\n"
        f"[소득] {salary}원\n"
        f"[총 소비] {total_spend}원 (소득 대비 {ratio*100:.1f}%)\n"
        f"[카테고리별 소비]\n"
    )
    for cat, val in spending.items():
        prompt += f"- {cat}: {val}원\n"
    if prev_info:
        prompt += f"\n{prev_info}\n"

    prompt += (
        f"[출력 예시]\n"
        f"- 외식비 비중이 지난달보다 다소 높습니다. 교통비는 안정적이라 예산을 조정해도 괜찮습니다.\n"
        f"- 식비가 전체 지출의 {ratio*100:.0f}%로 높지만, 저축 여력은 유지되고 있습니다.\n\n"
        f"코멘트:"
    )

    result = generator(prompt, max_new_tokens=70, temperature=0.7, do_sample=True)
    comment = result[0]["generated_text"].split("코멘트:")[-1].strip()
    return comment

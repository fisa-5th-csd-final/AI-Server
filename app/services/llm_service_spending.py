from app.services.llm_loader import safe_generate
from decimal import Decimal

def generate_spending_comment(
    spending_ratio: dict,
    age_group_ratio: dict,
    user_limit_ratio: dict,
    income: float = None,
) -> str:

    # Decimal → float 변환
    def to_float_map(data):
        return {k: float(v) if isinstance(v, Decimal) else float(v) for k, v in data.items()}

    spending = to_float_map(spending_ratio)
    age_norm = to_float_map(age_group_ratio)
    limit = to_float_map(user_limit_ratio)

    # 연령대 대비 차이 계산
    age_diff = {}
    for cat, user_v in spending.items():
        base_v = age_norm.get(cat, 0)
        if base_v > 0:
            pct = (user_v - base_v) / base_v * 100
            age_diff[cat] = pct

    top_age_cat = max(age_diff, key=lambda k: abs(age_diff[k])) if age_diff else None
    top_age_val = age_diff.get(top_age_cat, 0) if top_age_cat else 0

    # 한도 대비 차이 계산
    limit_diff = {}
    for cat, user_v in spending.items():
        limit_v = limit.get(cat)
        if limit_v is not None and limit_v > 0:
            pct = (user_v - limit_v) / limit_v * 100
            limit_diff[cat] = pct

    top_limit_cat = max(limit_diff, key=lambda k: abs(limit_diff[k])) if limit_diff else None
    top_limit_val = limit_diff.get(top_limit_cat, 0) if top_limit_cat else 0

    # -------------------------
    # LLM 프롬프트
    # -------------------------
    messages = [
        {
            "role": "system",
            "content": (
                "You are a Korean financial insight generator. "
                "Always respond in Korean using the polite '~습니다' tone. "
                "You MUST follow one of these templates:\n\n"
                "1) \"{A_list}에서 지출이 기준보다 높고, {B_list}에서도 높습니다.\"\n"
                "2) \"{A_list}에서 지출이 기준보다 낮고, {B_list}에서도 낮습니다.\"\n"
                "3) \"{A_list}에서 지출이 기준보다 높고, {B_list}에서는 낮습니다.\"\n\n"
                "Rules:\n"
                "- DO NOT output any numbers.\n"
                "- DO NOT output lists, bullet points, or raw data.\n"
                "- Only produce ONE sentence.\n"
                "- Fill A_list with age-group deviations (>=5%).\n"
                "- Fill B_list with user-limit deviations (>=5%)."
            )
        },
        {
            "role": "user",
            "content": (
                f"The category with the largest age-group difference is {top_age_cat} "
                f"with {top_age_val:+.1f}%. "
                f"The category with the largest limit difference is {top_limit_cat} "
                f"with {top_limit_val:+.1f}%. "
                "Based on this, generate one Korean sentence describing the key issue."
            ),
        },
    ]

    result = safe_generate(
        messages,
        max_new_tokens=120,
        temperature=0.4,
        top_p=0.9,
        do_sample=False
    )

    # LLM 결과 파싱 함수
    def extract_text(result):
        # result 가 list
        if isinstance(result, list):
            # 첫 번째 요소는 dict → 그 안의 generated_text 접근
            first = result[0]
            if isinstance(first, dict):
                gen = first.get("generated_text")
                if isinstance(gen, list):
                    # generated_text 내부에서 assistant role 찾기
                    for msg in gen:
                        if isinstance(msg, dict) and msg.get("role") == "assistant":
                            return msg.get("content") or msg.get("text") or ""
                    # fallback: 마지막 요소 content
                    last = gen[-1]
                    if isinstance(last, dict):
                        return last.get("content") or last.get("text") or ""
                    return str(last)
            # fallback: list 마지막 요소 문자화
            return str(result[-1])

        # dict 구조
        if isinstance(result, dict):
            gen = result.get("generated_text")
            if isinstance(gen, list):
                for msg in gen:
                    if msg.get("role") == "assistant":
                        return msg.get("content") or msg.get("text") or ""
                return str(gen[-1])
            if isinstance(gen, str):
                return gen

        # string
        if isinstance(result, str):
            return result

        # fallback
        return str(result)
    
    text = extract_text(result)

    if not isinstance(text, str):
        text = str(text)

    comment = text.strip().replace("�", "")

    if len(comment) < 3:
        comment = "소비 비율 분석 결과를 생성하지 못했습니다."

    return comment
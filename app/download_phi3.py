from transformers import AutoTokenizer, AutoModelForCausalLM

MODEL_ID = "microsoft/phi-3-mini-4k-instruct"
SAVE_PATH = "./app/models/phi3-mini-4k-instruct"

print("Phi-3-mini 모델 다운로드 중...")

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    device_map="auto",      # GPU 있으면 자동 할당
    dtype="auto",     # mixed precision 자동
)

tokenizer.save_pretrained(SAVE_PATH)
model.save_pretrained(SAVE_PATH)

print(f"모델 다운로드 완료: {SAVE_PATH}")

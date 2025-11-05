from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch

MODEL_PATH = "./app/models/phi3-mini-4k-instruct"

print("[LLM Loader] Loading Phi-3 model into memory...")

try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        device_map="auto" if torch.cuda.is_available() else None
    )

    generator = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        device=0 if torch.cuda.is_available() else -1
    )

    print("[LLM Loader] Phi-3 model loaded successfully.")
except Exception as e:
    print(f"[LLM Loader] Failed to load model: {e}")
    generator = None

def get_generator():
    """다른 서비스에서 pipeline 재사용"""
    if generator is None:
        raise RuntimeError("LLM generator is not initialized.")
    return generator

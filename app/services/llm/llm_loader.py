from transformers import pipeline
import logging

logger = logging.getLogger(__name__)

MODEL_PATH = "/app/models"

try:
    logger.info("Loading Phi-3 model pipeline (this may take a while)...")

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_PATH,
        local_files_only=True
    )

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        local_files_only=True
    )

    generator = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        device_map="auto",
        model_kwargs={"dtype": "auto"}
    )

    logger.info("Phi-3 model successfully loaded and ready to use.")

except Exception as e:
    logger.exception("Failed to load Phi-3 model.")
    raise RuntimeError(f"Failed to initialize Phi-3 model: {e}")

def safe_generate(prompt: str, **kwargs):
    try:
        result = generator(prompt, **kwargs)
        text = result[0]["generated_text"]

        if isinstance(text, bytes):
            text = text.decode("utf-8", errors="ignore")

        result[0]["generated_text"] = text
        return result

    except Exception as e:
        logger.exception("LLM generation error")
        return [{"generated_text": f"[LLM Error] {str(e)}"}]

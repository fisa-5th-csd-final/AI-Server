from transformers import pipeline
import logging

logger = logging.getLogger(__name__)

try:
    logger.info("Loading Phi-3 model pipeline (this may take a while)...")

    generator = pipeline(
        "text-generation",
        model="./app/models/phi3-mini-4k-instruct",
        model_kwargs={"dtype": "auto"},
        device_map="auto"
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

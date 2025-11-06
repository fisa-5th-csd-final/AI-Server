from transformers import pipeline

def get_generator():
    generator = pipeline(
        "text-generation",
        model="./app/models/phi3-mini-4k-instruct",
        model_kwargs={
            "torch_dtype": "auto"
        },
        device_map="auto"
    )

    def safe_generate(prompt, **kwargs):
        result = generator(prompt, **kwargs)
        text = result[0]["generated_text"]
        if isinstance(text, bytes):
            text = text.decode("utf-8", errors="ignore")
        result[0]["generated_text"] = text
        return result

    return safe_generate

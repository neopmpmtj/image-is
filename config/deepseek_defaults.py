"""DeepSeek vision defaults and eval prompt presets (not loaded from .env)."""

DEFAULT_EVAL_PROMPT = (
    "Describe this image carefully. Identify the main objects, their relationships, "
    "any visible text, and anything uncertain."
)

EVAL_PROMPT_DEFAULT_ID = "describe"

EVAL_PROMPT_PRESETS = {
    "describe": {
        "label": "Describe (default)",
        "text": DEFAULT_EVAL_PROMPT,
    },
    "ocr": {
        "label": "OCR / text extraction",
        "text": (
            "Transcribe all visible text in this image. Preserve layout where helpful. "
            "Note language, handwriting or print, and anything unreadable or uncertain."
        ),
    },
    "inventory": {
        "label": "Object inventory",
        "text": (
            "List the main objects in this image. Include counts where possible and "
            "describe spatial relationships between them."
        ),
    },
    "uncertainty": {
        "label": "Uncertainty focus",
        "text": (
            "Describe this image, emphasizing what is occluded, ambiguous, low resolution, "
            "or otherwise uncertain. Do not guess beyond what the image supports."
        ),
    },
}

DEEPSEEK_DEFAULT_MODEL = "deepseek-v4-flash-vision-exp"
DEEPSEEK_DEFAULT_REASONING_EFFORT = "high"
DEEPSEEK_DEFAULT_MAX_OUTPUT_TOKENS = 1600
DEEPSEEK_DEFAULT_IMAGE_DETAIL = "auto"

DEEPSEEK_REQUIRED_MODELS = [DEEPSEEK_DEFAULT_MODEL]

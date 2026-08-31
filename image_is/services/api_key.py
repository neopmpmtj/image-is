"""DeepSeek API key validation."""

from __future__ import annotations

from dataclasses import dataclass, field

from django.conf import settings
from openai import APIConnectionError, AuthenticationError, OpenAI, PermissionDeniedError, RateLimitError

from .deepseek_eval import DEEPSEEK_BASE_URL

SETTING_NAME = "DEEPSEEK_API_KEY"
LAB_LABEL = "DeepSeek"


@dataclass(frozen=True)
class ApiKeyStatus:
    ok: bool
    message: str
    missing_models: list[str] = field(default_factory=list)
    checked_models: list[str] = field(default_factory=list)


def api_key_context() -> dict[str, str]:
    return {
        "setting_name": SETTING_NAME,
        "lab_label": LAB_LABEL,
    }


def validate_deepseek_api_key(api_key: str | None = None) -> ApiKeyStatus:
    key = (api_key if api_key is not None else settings.DEEPSEEK_API_KEY) or ""
    if not key.strip():
        return ApiKeyStatus(ok=False, message="DEEPSEEK_API_KEY is not set.")

    required_models = list(settings.DEEPSEEK_REQUIRED_MODELS)
    try:
        client = OpenAI(api_key=key, base_url=DEEPSEEK_BASE_URL)
        available_ids = {model.id for model in client.models.list()}
    except AuthenticationError:
        return ApiKeyStatus(
            ok=False,
            message="DEEPSEEK_API_KEY was rejected by DeepSeek (invalid or revoked).",
            checked_models=required_models,
        )
    except PermissionDeniedError:
        return ApiKeyStatus(
            ok=False,
            message="DEEPSEEK_API_KEY is valid but lacks permission to list models.",
            checked_models=required_models,
        )
    except RateLimitError:
        return ApiKeyStatus(
            ok=False,
            message="DeepSeek rate limit reached while validating the API key. Try again shortly.",
            checked_models=required_models,
        )
    except APIConnectionError:
        return ApiKeyStatus(
            ok=False,
            message="Could not reach DeepSeek while validating the API key. Check your network.",
            checked_models=required_models,
        )
    except Exception as exc:
        return ApiKeyStatus(
            ok=False,
            message=f"Unexpected error while validating the API key: {exc}",
            checked_models=required_models,
        )

    missing_models = [model for model in required_models if model not in available_ids]
    if missing_models:
        return ApiKeyStatus(
            ok=False,
            message=(
                "API key is valid, but these configured models are not available on your account: "
                + ", ".join(missing_models)
            ),
            missing_models=missing_models,
            checked_models=required_models,
        )

    return ApiKeyStatus(
        ok=True,
        message="API key is valid and all configured models are listed.",
        checked_models=required_models,
    )

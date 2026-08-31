import time
from datetime import datetime, timezone

from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View

from image_is.forms import NewAnalysisForm
from image_is.image_utils import extract_image_metadata
from image_is.models import AnalysisStatus, ImageAnalysis
from image_is.services import (
    analyze_image,
    api_key_context,
    build_api_request_dict,
    save_error_analysis,
    save_success_analysis,
    validate_deepseek_api_key,
)
from image_is.services.api_key import ApiKeyStatus
from image_is.services.deepseek_eval import DeepSeekApiRequestConfig


def _status_from_session(data: dict) -> ApiKeyStatus:
    return ApiKeyStatus(
        ok=data["ok"],
        message=data["message"],
        missing_models=data.get("missing_models", []),
        checked_models=data.get("checked_models", []),
    )


def _get_api_key_status(request) -> ApiKeyStatus:
    key = settings.DEEPSEEK_API_KEY
    if not key:
        return validate_deepseek_api_key()

    session_key = settings.API_KEY_SESSION_KEY
    if request.GET.get("recheck") == "1":
        request.session.pop(session_key, None)

    cached = request.session.get(session_key)
    if cached and cached.get("key") == key:
        return _status_from_session(cached)

    status = validate_deepseek_api_key()
    request.session[session_key] = {
        "key": key,
        "ok": status.ok,
        "message": status.message,
        "missing_models": status.missing_models,
        "checked_models": status.checked_models,
    }
    return status


def _check_api_key(request) -> HttpResponse | None:
    if not settings.DEEPSEEK_API_KEY:
        return render(
            request,
            "image_is/missing_api_key.html",
            {"lab": api_key_context()},
            status=503,
        )

    status = _get_api_key_status(request)
    if not status.ok:
        return render(
            request,
            "image_is/invalid_api_key.html",
            {"status": status, "lab": api_key_context()},
            status=503,
        )
    return None


def _default_api_snapshot(*, omit_instructions: bool, prompt_preset: str) -> dict:
    config = DeepSeekApiRequestConfig.from_settings()
    return {
        "model": settings.DEEPSEEK_DEFAULT_MODEL,
        "omit_instructions": omit_instructions,
        "prompt_preset": prompt_preset,
        **config.to_dict(),
    }


class HistoryView(View):
    def get(self, request):
        analyses = ImageAnalysis.objects.all()[:200]
        return render(request, "image_is/history.html", {"analyses": analyses})


class NewAnalysisView(View):
    def get(self, request):
        status = validate_deepseek_api_key()
        form = NewAnalysisForm()
        return render(
            request,
            "image_is/new.html",
            {
                "form": form,
                "key_status": status,
                "key_ok": status.ok,
            },
        )

    def post(self, request):
        blocked = _check_api_key(request)
        if blocked:
            return blocked

        form = NewAnalysisForm(request.POST, request.FILES)
        if not form.is_valid():
            status = validate_deepseek_api_key()
            return render(
                request,
                "image_is/new.html",
                {
                    "form": form,
                    "key_status": status,
                    "key_ok": status.ok,
                },
                status=400,
            )

        uploaded = form.cleaned_data["image"]
        omit_instructions = form.cleaned_data["omit_instructions"]
        prompt_preset = form.cleaned_data["prompt_preset"]
        instructions = form.cleaned_data["instructions"]
        user_prompt = form.cleaned_data["user_prompt"]
        description = form.cleaned_data["description"]

        size_bytes, width, height = extract_image_metadata(uploaded)
        api_defaults = _default_api_snapshot(
            omit_instructions=omit_instructions,
            prompt_preset=prompt_preset,
        )
        model = settings.DEEPSEEK_DEFAULT_MODEL
        api_config = DeepSeekApiRequestConfig.from_dict(api_defaults)

        analysis = ImageAnalysis.objects.create(
            image=uploaded,
            image_name=uploaded.name,
            image_content_type=getattr(uploaded, "content_type", None) or "image/jpeg",
            image_size_bytes=size_bytes,
            image_width=width,
            image_height=height,
            instructions=instructions,
            user_prompt=user_prompt,
            description=description,
            api_defaults=api_defaults,
            model=model,
            status=AnalysisStatus.IN_PROGRESS,
        )

        api_request = build_api_request_dict(
            model=model,
            instructions=instructions,
            user_prompt=user_prompt,
            api_config=api_config,
        )
        request_started_at = datetime.now(timezone.utc)
        started_perf = time.perf_counter()

        try:
            result = analyze_image(
                model=model,
                instructions=instructions,
                user_prompt=user_prompt,
                image_path=analysis.image.path,
                image_content_type=analysis.image_content_type,
                api_config=api_config,
            )
            save_success_analysis(analysis=analysis, result=result)
            messages.success(request, "Analysis completed.")
        except Exception as exc:
            finished_perf = time.perf_counter()
            save_error_analysis(
                analysis=analysis,
                error=exc,
                request_started_at=request_started_at,
                request_finished_at=datetime.now(timezone.utc),
                latency_wall_seconds=round(finished_perf - started_perf, 3),
                api_request=api_request,
            )
            messages.error(request, f"Analysis failed: {exc}")

        return redirect(reverse("image_is:detail", kwargs={"analysis_id": analysis.id}))


class DetailView(View):
    def get(self, request, analysis_id):
        analysis = get_object_or_404(ImageAnalysis, id=analysis_id)
        return render(request, "image_is/detail.html", {"analysis": analysis})

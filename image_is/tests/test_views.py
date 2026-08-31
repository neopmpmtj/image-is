from datetime import datetime, timezone
from io import BytesIO
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from image_is.models import AnalysisStatus, ImageAnalysis
from image_is.services.analysis import AnalysisResult
from image_is.services.persistence import save_error_analysis, save_success_analysis


def _test_image_file(name: str = "sample.png") -> SimpleUploadedFile:
    buffer = BytesIO()
    Image.new("RGB", (8, 8), color="red").save(buffer, format="PNG")
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.read(), content_type="image/png")


def _sample_result() -> AnalysisResult:
    now = datetime.now(timezone.utc)
    return AnalysisResult(
        response_text="A red square.",
        request_started_at=now,
        request_finished_at=now,
        latency_wall_seconds=1.234,
        latency_openai_seconds=1.1,
        input_tokens=100,
        output_tokens=50,
        total_tokens=150,
        reasoning_tokens=10,
        cached_tokens=0,
        cache_write_tokens=0,
        usage_raw={"input_tokens": 100},
        api_request={"model": "deepseek-v4-flash-vision-exp"},
        api_response={"id": "resp_123"},
        openai_response_id="resp_123",
        response_model="deepseek-v4-flash-vision-exp",
        openai_status="completed",
    )


class PersistenceTests(TestCase):
    def _create_analysis(self) -> ImageAnalysis:
        image = SimpleUploadedFile("test.png", b"fake", content_type="image/png")
        return ImageAnalysis.objects.create(
            image=image,
            image_name="test.png",
            status=AnalysisStatus.IN_PROGRESS,
            model="deepseek-v4-flash-vision-exp",
        )

    def test_save_success_analysis(self):
        analysis = self._create_analysis()
        save_success_analysis(analysis=analysis, result=_sample_result())
        analysis.refresh_from_db()
        self.assertEqual(analysis.status, AnalysisStatus.COMPLETED)
        self.assertEqual(analysis.response_text, "A red square.")
        self.assertEqual(analysis.openai_response_id, "resp_123")
        self.assertEqual(analysis.input_tokens, 100)

    def test_save_error_analysis(self):
        analysis = self._create_analysis()
        save_error_analysis(
            analysis=analysis,
            error=RuntimeError("API failed"),
            api_request={"model": "deepseek-v4-flash-vision-exp"},
        )
        analysis.refresh_from_db()
        self.assertEqual(analysis.status, AnalysisStatus.ERROR)
        self.assertEqual(analysis.error_type, "RuntimeError")
        self.assertIn("API failed", analysis.error_message)


@override_settings(DEEPSEEK_API_KEY="")
class ViewTests(TestCase):
    def test_history_page(self):
        response = self.client.get(reverse("image_is:history"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "History")

    def test_new_page_renders_form(self):
        response = self.client.get(reverse("image_is:new"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "New analysis")
        self.assertContains(response, "DEEPSEEK_API_KEY is not set")

    @patch("image_is.views.analyze_image")
    @patch("image_is.views._check_api_key", return_value=None)
    @override_settings(DEEPSEEK_API_KEY="ds-test")
    def test_new_post_creates_analysis(self, _mock_key, mock_analyze):
        mock_analyze.return_value = _sample_result()
        image = _test_image_file()
        response = self.client.post(
            reverse("image_is:new"),
            {
                "image": image,
                "description": "Test session",
                "omit_instructions": False,
                "prompt_preset": "describe",
                "additional": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        analysis = ImageAnalysis.objects.get()
        self.assertEqual(analysis.status, AnalysisStatus.COMPLETED)
        self.assertEqual(analysis.description, "Test session")

    def test_detail_page(self):
        analysis = ImageAnalysis.objects.create(
            image=SimpleUploadedFile("x.png", b"x", content_type="image/png"),
            image_name="x.png",
            status=AnalysisStatus.COMPLETED,
            response_text="Done.",
            model="deepseek-v4-flash-vision-exp",
        )
        response = self.client.get(
            reverse("image_is:detail", kwargs={"analysis_id": analysis.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Done.")

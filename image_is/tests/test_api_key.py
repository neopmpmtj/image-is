from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, override_settings

from image_is.services.api_key import validate_deepseek_api_key
from image_is.services.deepseek_eval import DeepSeekApiRequestConfig


class DeepSeekConfigTests(SimpleTestCase):
    @override_settings(
        DEEPSEEK_DEFAULT_REASONING_EFFORT="high",
        DEEPSEEK_DEFAULT_MAX_OUTPUT_TOKENS=1600,
        DEEPSEEK_DEFAULT_IMAGE_DETAIL="auto",
    )
    def test_from_settings(self):
        config = DeepSeekApiRequestConfig.from_settings()
        self.assertEqual(config.reasoning_effort, "high")
        self.assertEqual(config.max_output_tokens, 1600)
        self.assertEqual(config.image_detail, "auto")

    def test_from_dict_overrides(self):
        config = DeepSeekApiRequestConfig.from_dict(
            {
                "reasoning": {"effort": "max"},
                "max_output_tokens": 900,
                "image_detail": "low",
            }
        )
        self.assertEqual(config.reasoning_effort, "max")
        self.assertEqual(config.max_output_tokens, 900)
        self.assertEqual(config.image_detail, "low")


class ApiKeyValidationTests(SimpleTestCase):
    def test_missing_key(self):
        status = validate_deepseek_api_key("")
        self.assertFalse(status.ok)
        self.assertIn("not set", status.message)

    @patch("image_is.services.api_key.OpenAI")
    @override_settings(DEEPSEEK_REQUIRED_MODELS=["deepseek-v4-flash-vision-exp"])
    def test_valid_key_lists_models(self, mock_openai):
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.models.list.return_value = [MagicMock(id="deepseek-v4-flash-vision-exp")]

        status = validate_deepseek_api_key("ds-test")
        self.assertTrue(status.ok)

    @patch("image_is.services.api_key.OpenAI")
    @override_settings(DEEPSEEK_REQUIRED_MODELS=["deepseek-v4-flash-vision-exp"])
    def test_missing_configured_model(self, mock_openai):
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.models.list.return_value = [MagicMock(id="other-model")]

        status = validate_deepseek_api_key("ds-test")
        self.assertFalse(status.ok)
        self.assertEqual(status.missing_models, ["deepseek-v4-flash-vision-exp"])

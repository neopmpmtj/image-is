# Session handoff

Last updated: 2026-08-31

## Project

**image-is** — Django app for single-image DeepSeek vision analysis. One upload, one API call, full metadata in SQLite. No auth.

## Done

- `ImageAnalysis` model with legacy metadata field names (`openai_response_id`, `latency_openai_seconds`, etc.)
- DeepSeek Responses API via `image_is/services/deepseek_eval.py`
- Prompt presets + `compose_eval_text()` (describe, OCR, inventory, uncertainty)
- API key validation (`models.list()`), session cache
- Views: history `/`, new `/new/`, detail `/analysis/<uuid>/`
- Only `DEEPSEEK_API_KEY` in `.env`; other settings in `config/settings/` and `config/deepseek_defaults.py`
- Unit tests in `image_is/tests/`

## Not done

- Streaming / TTFB
- Auth, production deploy
- UI controls for API parameters (defaults used from settings)
- Re-run on detail page (`/new/` is the re-run path)

## Commands

```bash
source .venv/bin/activate
cp .env.example .env
python manage.py migrate
python manage.py runserver
.venv/bin/python manage.py test image_is.tests
```

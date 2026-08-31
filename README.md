# Image Analysis

Django app for **single-image analysis** with **DeepSeek vision**. Upload an image, run one API call, and persist the full response and metadata in SQLite.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set your key in `.env` (this is the **only** value read from `.env`):

```
DEEPSEEK_API_KEY=your-key-here
```

All other configuration (model, API defaults, prompt presets, `SECRET_KEY`, etc.) lives in `config/settings/` and `config/deepseek_defaults.py`.

## Run

```bash
python manage.py migrate
python manage.py runserver
```

Open http://127.0.0.1:8000/

| Path | Purpose |
|------|---------|
| `/` | History — past analyses |
| `/new/` | New analysis — upload + presets |
| `/analysis/<uuid>/` | Detail — response + metadata |

## Prompt presets

On `/new/`:

| Control | Sent to API |
|---------|-------------|
| System instructions preset | Responses `instructions` |
| Omit system instructions | No `instructions`; additional text required as user prompt |
| Additional instructions | Appended to preset, or sole user text when omitted |
| Session description | Not sent — metadata only |

## Tests

```bash
.venv/bin/python manage.py test image_is.tests
```

## Defaults

| Setting | Value |
|---------|-------|
| Model | `deepseek-v4-flash-vision-exp` |
| Reasoning effort | `high` |
| Max output tokens | `1600` |
| Image detail | `auto` |

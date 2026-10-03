# PocketSmart AI

AI-powered budget planner for:
- Home Interior
- Party Planning
- Jewelry Recommendations

## Stack
FastAPI + Jinja2 + HTML/CSS/JavaScript + SQLite + Gemini API

## Local setup

```bash
python -m venv .venv
```

Windows:
```bash
.venv\Scripts\activate
```

Install:
```bash
pip install -r requirements.txt
```

Create `.env` from `.env.example` and add your Gemini API key.

Run:
```bash
uvicorn app:app --reload
```

Open:
http://127.0.0.1:8000

## Render

Build:
```bash
pip install -r requirements.txt
```

Start:
```bash
uvicorn app:app --host 0.0.0.0 --port $PORT
```

Add `GEMINI_API_KEY` as a Render environment variable.

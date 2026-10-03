import os
import json
import secrets
import hashlib
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from database import init_db, create_user, verify_user, save_history, get_history, get_user

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-key")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

app = FastAPI(title="PocketSmart AI")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

init_db()

try:
    from services.gemini_utils import generate_recommendations
except Exception:
    generate_recommendations = None


def get_current_user(request: Request):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return None
    return get_user(int(user_id))


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "user": get_current_user(request)}
    )


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse(
        "register.html",
        {"request": request, "user": get_current_user(request)}
    )


@app.post("/register")
async def register(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...)
):
    if len(password) < 6:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "user": None,
             "error": "Password must contain at least 6 characters."},
            status_code=400
        )

    if not create_user(name.strip(), email.strip().lower(), password):
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "user": None,
             "error": "Email already registered."},
            status_code=400
        )

    return RedirectResponse("/login?registered=1", status_code=303)


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "user": get_current_user(request)}
    )


@app.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    user = verify_user(email.strip().lower(), password)

    if not user:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "user": None,
             "error": "Invalid email or password."},
            status_code=401
        )

    response = RedirectResponse("/dashboard", status_code=303)
    response.set_cookie(
        "user_id",
        str(user["id"]),
        httponly=True,
        samesite="lax",
        secure=False
    )
    return response


@app.get("/logout")
async def logout():
    response = RedirectResponse("/", status_code=303)
    response.delete_cookie("user_id")
    return response


@app.post("/token")
async def token(email: str = Form(...), password: str = Form(...)):
    user = verify_user(email.strip().lower(), password)
    if not user:
        return JSONResponse({"detail": "Invalid credentials"}, status_code=401)

    token_value = secrets.token_urlsafe(32)
    return {
        "access_token": token_value,
        "token_type": "bearer",
        "user_id": user["id"]
    }


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    history = get_history(user["id"], 5)
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "user": user, "history": history}
    )


@app.get("/history", response_class=HTMLResponse)
async def history_page(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    history = get_history(user["id"], 50)
    return templates.TemplateResponse(
        "history.html",
        {"request": request, "user": user, "history": history}
    )


@app.get("/session-info")
async def session_info(request: Request):
    user = get_current_user(request)
    return {
        "logged_in": user is not None,
        "user": {"id": user["id"], "name": user["name"], "email": user["email"]}
        if user else None
    }


@app.get("/session-data")
async def session_data(request: Request):
    user = get_current_user(request)
    if not user:
        return JSONResponse({"detail": "Not logged in"}, status_code=401)

    return {"user": user, "history": get_history(user["id"], 20)}


async def run_planner(request: Request, planner: str, payload: dict, image: Optional[UploadFile] = None):
    user = get_current_user(request)
    if not user:
        return JSONResponse({"detail": "Please login first."}, status_code=401)

    image_bytes = None
    image_mime = None

    if image and image.filename:
        image_bytes = await image.read()
        image_mime = image.content_type or "image/jpeg"

        if len(image_bytes) > 5 * 1024 * 1024:
            return JSONResponse(
                {"detail": "Image must be smaller than 5 MB."},
                status_code=400
            )

    try:
        result = await generate_recommendations(
            planner=planner,
            data=payload,
            api_key=GEMINI_API_KEY,
            model_name=GEMINI_MODEL,
            image_bytes=image_bytes,
            image_mime=image_mime,
        )
    except Exception as exc:
        result = {
            "title": f"{planner.title()} Planner Recommendations",
            "summary": "AI service is not available. Showing a safe demo response.",
            "budget_plan": [],
            "recommendations": [],
            "tips": [
                "Add GEMINI_API_KEY to your .env file.",
                "Check that the selected Gemini model is available for your API key."
            ],
            "error": str(exc)
        }

    save_history(
        user["id"],
        planner,
        json.dumps(payload, ensure_ascii=False),
        json.dumps(result, ensure_ascii=False)
    )

    return JSONResponse(result)


@app.post("/generate-home")
async def generate_home(
    request: Request,
    budget: float = Form(...),
    room: str = Form(...),
    style: str = Form(...),
    lights: int = Form(0),
    fans: int = Form(0),
    tables: int = Form(0),
    extras: str = Form("")
):
    if budget <= 0:
        return JSONResponse({"detail": "Budget must be greater than 0."}, status_code=400)

    return await run_planner(
        request,
        "home",
        {
            "budget": budget,
            "room": room,
            "style": style,
            "lights": lights,
            "fans": fans,
            "tables": tables,
            "extras": extras
        }
    )


@app.post("/generate-party")
async def generate_party(
    request: Request,
    budget: float = Form(...),
    guests: int = Form(...),
    event_type: str = Form(...),
    venue: str = Form(...),
    food: str = Form(...),
    decoration: str = Form(...),
    extras: str = Form("")
):
    if budget <= 0 or guests <= 0:
        return JSONResponse({"detail": "Budget and guests must be greater than 0."}, status_code=400)

    return await run_planner(
        request,
        "party",
        {
            "budget": budget,
            "guests": guests,
            "event_type": event_type,
            "venue": venue,
            "food": food,
            "decoration": decoration,
            "extras": extras
        }
    )


@app.post("/generate-jewelry")
async def generate_jewelry(
    request: Request,
    budget: float = Form(...),
    occasion: str = Form(...),
    style: str = Form(...),
    metal: str = Form(...),
    outfit_color: str = Form(""),
    extras: str = Form(""),
    image: Optional[UploadFile] = File(None)
):
    if budget <= 0:
        return JSONResponse({"detail": "Budget must be greater than 0."}, status_code=400)

    return await run_planner(
        request,
        "jewelry",
        {
            "budget": budget,
            "occasion": occasion,
            "style": style,
            "metal": metal,
            "outfit_color": outfit_color,
            "extras": extras
        },
        image
    )


@app.get("/recommendations-details")
async def recommendations_details(request: Request):
    user = get_current_user(request)
    if not user:
        return JSONResponse({"detail": "Please login first."}, status_code=401)
    return {"history": get_history(user["id"], 1)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)

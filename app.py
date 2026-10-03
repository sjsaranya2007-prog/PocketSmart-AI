import os
import sqlite3
from pathlib import Path

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse

app = FastAPI(title="PocketSmart AI")

BASE_DIR = Path(__file__).resolve().parent
DB_FILE = BASE_DIR / "pocketsmart.db"


# ---------------- DATABASE ----------------

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def get_user(email, password):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, name, email FROM users WHERE email=? AND password=?",
        (email, password)
    )

    user = cursor.fetchone()
    conn.close()

    return user


def create_user(name, email, password):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            (name, email, password)
        )

        conn.commit()
        conn.close()
        return True

    except sqlite3.IntegrityError:
        return False


init_db()


# ---------------- HOME PAGE ----------------

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>PocketSmart AI</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: Arial, sans-serif;
                background: #f4f7fb;
                margin: 0;
                padding: 0;
            }

            .container {
                max-width: 900px;
                margin: 60px auto;
                padding: 30px;
                text-align: center;
            }

            h1 {
                color: #222;
                font-size: 42px;
            }

            p {
                color: #555;
                font-size: 18px;
            }

            .card {
                background: white;
                padding: 30px;
                margin: 25px 0;
                border-radius: 15px;
                box-shadow: 0 5px 20px rgba(0,0,0,0.08);
            }

            a, button {
                display: inline-block;
                padding: 13px 22px;
                margin: 8px;
                border-radius: 8px;
                text-decoration: none;
                border: none;
                cursor: pointer;
                background: #2563eb;
                color: white;
                font-size: 16px;
            }

            .secondary {
                background: #64748b;
            }
        </style>
    </head>

    <body>
        <div class="container">

            <div class="card">

                <h1>💡 PocketSmart AI</h1>

                <p>
                    Your AI-powered smart budget and planning assistant.
                </p>

                <p>
                    Plan your home, party and jewelry budget easily.
                </p>

                <a href="/register">Create Account</a>

                <a href="/login" class="secondary">Login</a>

            </div>

        </div>
    </body>
    </html>
    """


# ---------------- REGISTER ----------------

@app.get("/register", response_class=HTMLResponse)
async def register_page():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Register - PocketSmart AI</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">

        <style>
            body {
                font-family: Arial;
                background: #f4f7fb;
            }

            .box {
                max-width: 450px;
                margin: 60px auto;
                background: white;
                padding: 30px;
                border-radius: 15px;
                box-shadow: 0 5px 20px rgba(0,0,0,0.1);
            }

            input {
                width: 100%;
                padding: 12px;
                margin: 10px 0;
                box-sizing: border-box;
                border: 1px solid #ccc;
                border-radius: 7px;
            }

            button {
                width: 100%;
                padding: 13px;
                background: #2563eb;
                color: white;
                border: none;
                border-radius: 7px;
                cursor: pointer;
            }

            a {
                display: block;
                margin-top: 20px;
                text-align: center;
            }
        </style>
    </head>

    <body>

        <div class="box">

            <h2>Create Account</h2>

            <form method="post" action="/register">

                <input
                    type="text"
                    name="name"
                    placeholder="Name"
                    required
                >

                <input
                    type="email"
                    name="email"
                    placeholder="Email"
                    required
                >

                <input
                    type="password"
                    name="password"
                    placeholder="Password"
                    required
                >

                <button type="submit">
                    Register
                </button>

            </form>

            <a href="/login">
                Already have an account? Login
            </a>

        </div>

    </body>
    </html>
    """


@app.post("/register")
async def register(
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...)
):

    success = create_user(
        name.strip(),
        email.strip().lower(),
        password
    )

    if not success:
        return HTMLResponse(
            "<h2>Email already registered.</h2>"
            "<a href='/register'>Go Back</a>",
            status_code=400
        )

    return RedirectResponse(
        "/login",
        status_code=303
    )


# ---------------- LOGIN ----------------

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Login - PocketSmart AI</title>

        <style>
            body {
                font-family: Arial;
                background: #f4f7fb;
            }

            .box {
                max-width: 450px;
                margin: 60px auto;
                background: white;
                padding: 30px;
                border-radius: 15px;
                box-shadow: 0 5px 20px rgba(0,0,0,0.1);
            }

            input {
                width: 100%;
                padding: 12px;
                margin: 10px 0;
                box-sizing: border-box;
                border: 1px solid #ccc;
                border-radius: 7px;
            }

            button {
                width: 100%;
                padding: 13px;
                background: #2563eb;
                color: white;
                border: none;
                border-radius: 7px;
            }

            a {
                display: block;
                margin-top: 20px;
                text-align: center;
            }
        </style>
    </head>

    <body>

        <div class="box">

            <h2>Login</h2>

            <form method="post" action="/login">

                <input
                    type="email"
                    name="email"
                    placeholder="Email"
                    required
                >

                <input
                    type="password"
                    name="password"
                    placeholder="Password"
                    required
                >

                <button type="submit">
                    Login
                </button>

            </form>

            <a href="/register">
                Create new account
            </a>

        </div>

    </body>
    </html>
    """


@app.post("/login")
async def login(
    email: str = Form(...),
    password: str = Form(...)
):

    user = get_user(
        email.strip().lower(),
        password
    )

    if not user:
        return HTMLResponse(
            "<h2>Invalid email or password.</h2>"
            "<a href='/login'>Try Again</a>",
            status_code=401
        )

    response = RedirectResponse(
        "/dashboard",
        status_code=303
    )

    response.set_cookie(
        key="user_id",
        value=str(user[0]),
        httponly=True
    )

    return response


# ---------------- DASHBOARD ----------------

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():

    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dashboard - PocketSmart AI</title>

        <style>
            body {
                font-family: Arial;
                background: #f4f7fb;
                margin: 0;
            }

            header {
                background: #2563eb;
                color: white;
                padding: 20px;
                text-align: center;
            }

            .container {
                max-width: 900px;
                margin: 40px auto;
                padding: 20px;
            }

            .card {
                background: white;
                padding: 25px;
                margin: 20px 0;
                border-radius: 15px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.08);
            }

            a {
                display: inline-block;
                background: #2563eb;
                color: white;
                padding: 12px 20px;
                margin: 5px;
                border-radius: 7px;
                text-decoration: none;
            }
        </style>
    </head>

    <body>

        <header>
            <h1>💡 PocketSmart AI Dashboard</h1>
        </header>

        <div class="container">

            <div class="card">

                <h2>Smart Budget Planner</h2>

                <p>
                    Choose a planner to start.
                </p>

                <a href="/home-planner">
                    🏠 Home Planner
                </a>

                <a href="/party-planner">
                    🎉 Party Planner
                </a>

                <a href="/jewelry-planner">
                    💎 Jewelry Planner
                </a>

            </div>

        </div>

    </body>
    </html>
    """


# ---------------- HOME PLANNER ----------------

@app.get("/home-planner", response_class=HTMLResponse)
async def home_planner():

    return """
    <html>
    <head>
        <title>Home Planner</title>
    </head>

    <body style="font-family:Arial;max-width:600px;margin:50px auto">

        <h1>🏠 Home Budget Planner</h1>

        <form method="post" action="/generate-home">

            <p>Budget</p>
            <input name="budget" type="number" required>

            <p>Room</p>
            <input name="room" required>

            <p>Style</p>
            <input name="style" required>

            <br><br>

            <button type="submit">
                Generate Plan
            </button>

        </form>

    </body>
    </html>
    """


@app.post("/generate-home", response_class=HTMLResponse)
async def generate_home(
    budget: float = Form(...),
    room: str = Form(...),
    style: str = Form(...)
):

    return f"""
    <html>
    <body style="font-family:Arial;max-width:700px;margin:50px auto">

        <h1>🏠 Home Plan</h1>

        <h3>Budget: ₹{budget:,.2f}</h3>

        <p>
            Room: {room}
        </p>

        <p>
            Style: {style}
        </p>

        <hr>

        <h2>Suggested Budget</h2>

        <p>🪑 Furniture: ₹{budget * 0.40:,.2f}</p>

        <p>💡 Lighting: ₹{budget * 0.20:,.2f}</p>

        <p>🎨 Decoration: ₹{budget * 0.20:,.2f}</p>

        <p>📦 Extra items: ₹{budget * 0.20:,.2f}</p>

        <br>

        <a href="/dashboard">
            Back to Dashboard
        </a>

    </body>
    </html>
    """


# ---------------- PARTY PLANNER ----------------

@app.get("/party-planner", response_class=HTMLResponse)
async def party_planner():

    return """
    <html>
    <body style="font-family:Arial;max-width:600px;margin:50px auto">

        <h1>🎉 Party Budget Planner</h1>

        <form method="post" action="/generate-party">

            <p>Budget</p>
            <input name="budget" type="number" required>

            <p>Number of Guests</p>
            <input name="guests" type="number" required>

            <p>Event Type</p>
            <input name="event_type" required>

            <br><br>

            <button type="submit">
                Generate Plan
            </button>

        </form>

    </body>
    </html>
    """


@app.post("/generate-party", response_class=HTMLResponse)
async def generate_party(
    budget: float = Form(...),
    guests: int = Form(...),
    event_type: str = Form(...)
):

    food_budget = budget * 0.45
    decoration_budget = budget * 0.25
    venue_budget = budget * 0.20
    extra_budget = budget * 0.10

    return f"""
    <html>
    <body style="font-family:Arial;max-width:700px;margin:50px auto">

        <h1>🎉 Party Plan</h1>

        <h3>Event: {event_type}</h3>

        <p>Guests: {guests}</p>

        <p>Total Budget: ₹{budget:,.2f}</p>

        <hr>

        <p>🍽️ Food: ₹{food_budget:,.2f}</p>

        <p>🎈 Decoration: ₹{decoration_budget:,.2f}</p>

        <p>🏛️ Venue: ₹{venue_budget:,.2f}</p>

        <p>📦 Extra: ₹{extra_budget:,.2f}</p>

        <br>

        <a href="/dashboard">
            Back to Dashboard
        </a>

    </body>
    </html>
    """


# ---------------- JEWELRY PLANNER ----------------

@app.get("/jewelry-planner", response_class=HTMLResponse)
async def jewelry_planner():

    return """
    <html>
    <body style="font-family:Arial;max-width:600px;margin:50px auto">

        <h1>💎 Jewelry Budget Planner</h1>

        <form method="post" action="/generate-jewelry">

            <p>Budget</p>
            <input name="budget" type="number" required>

            <p>Occasion</p>
            <input name="occasion" required>

            <p>Style</p>
            <input name="style" required>

            <br><br>

            <button type="submit">
                Generate Plan
            </button>

        </form>

    </body>
    </html>
    """


@app.post("/generate-jewelry", response_class=HTMLResponse)
async def generate_jewelry(
    budget: float = Form(...),
    occasion: str = Form(...),
    style: str = Form(...)
):

    return f"""
    <html>
    <body style="font-family:Arial;max-width:700px;margin:50px auto">

        <h1>💎 Jewelry Plan</h1>

        <p>Occasion: {occasion}</p>

        <p>Style: {style}</p>

        <p>Total Budget: ₹{budget:,.2f}</p>

        <hr>

        <p>💍 Main Jewelry: ₹{budget * 0.60:,.2f}</p>

        <p>✨ Accessories: ₹{budget * 0.20:,.2f}</p>

        <p>🎁 Extra: ₹{budget * 0.20:,.2f}</p>

        <br>

        <a href="/dashboard">
            Back to Dashboard
        </a>

    </body>
    </html>
    """


# ---------------- HEALTH CHECK ----------------

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "application": "PocketSmart AI"
    }


# ---------------- RUN ----------------

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port
    )

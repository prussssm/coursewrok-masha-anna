from fastapi import FastAPI, Request, Form, UploadFile, File, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from passlib.hash import bcrypt
import os, shutil
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

from backend.database import SessionLocal, init_db, engine
from backend import models
from backend.models import MarmeladType, Product
from backend.routers import auth, catalog

# Инициализация базы данных
models.Base.metadata.create_all(bind=engine)
init_db()

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="masha_super_secret_key_123456")

# Подключение шаблонов и статики
templates = Jinja2Templates(directory="frontend/templates")
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# Утилиты
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="course_laba2_veb",
        user="postgres",
        password="1234",
        cursor_factory=RealDictCursor
    )

def get_current_user(request: Request):
    return request.session.get("user")
    
@app.on_event("startup")
def on_startup():
    init_db()

# Подключаем роутеры
app.include_router(auth.router)
app.include_router(catalog.router)

# Главная страница
@app.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    marmelads = db.query(MarmeladType).all()
    # Если в MarmeladType нет image_url, можно добавить вручную
    # например:
    images = {
        "Кислый": "/static/products/sour.jpg",
        "Сладкий": "/static/products/sweet.jpg",
        "Острый": "/static/products/spicy.jpg",
        "Ягодный": "/static/products/berry.jpg",
        "Тропический": "/static/products/tropical.jpg",
    }
    for m in marmelads:
        m.image_url = images.get(m.name, "/static/products/default.jpg")

    user = get_current_user(request)
    return templates.TemplateResponse("index.html", {"request": request, "marmelads": marmelads, "user": user})

# Показ товаров по типу
@app.get("/products/{type_id}", response_class=HTMLResponse)
def products_by_type(type_id: int, request: Request, db: Session = Depends(get_db)):
    marmelad_type = db.query(MarmeladType).get(type_id)
    products = db.query(Product).filter(Product.marmelad_type_id == type_id).all()

    # Присваиваем image_url вручную
    images = {
        "Кислый": "/static/products/sour.jpg",
        "Сладкий": "/static/products/sweet.jpg",
        "Острый": "/static/products/spicy.jpg",
    }
    marmelad_type.image_url = images.get(marmelad_type.name, "/static/products/default.jpg")

    return templates.TemplateResponse("products.html", {
        "request": request,
        "products": products,
        "marmelad_type": marmelad_type
    })

# Другие страницы
@app.get("/about", response_class=HTMLResponse)
def read_about(request: Request):
    user = get_current_user(request)
    return templates.TemplateResponse("about.html", {"request": request, "user": user})

@app.get("/catalog", response_class=HTMLResponse)
def read_catalog(request: Request):
    user = get_current_user(request)
    return templates.TemplateResponse("catalog.html", {"request": request, "user": user})

@app.get("/profile", response_class=HTMLResponse)
def profile_page(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse("profile.html", {"request": request, "user": user})

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "user": None})

@app.post("/login_form")
def login_form(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    password: str = Form(...)
):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM users WHERE first_name = %s AND last_name = %s",
                (first_name, last_name)
            )
            user = cur.fetchone()

    if user and user.get("password") and bcrypt.verify(password, user["password"]):
        request.session["user"] = {
            "id": user["id"],
            "first_name": user["first_name"],
            "last_name": user["last_name"],
            "email": user["email"],
            "phone": user["phone"],
            "avatar_url": user.get("avatar_url", "/static/avatar.png")
        }
        return RedirectResponse("/profile", status_code=302)

    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": "Неверные имя, фамилия или пароль",
        "entered_first_name": first_name,
        "entered_last_name": last_name,
        "user": None
    })

@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register_form")
def register_form(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    password: str = Form(...)
):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE email = %s", (email,))
            existing_user = cur.fetchone()
            if existing_user:
                return templates.TemplateResponse("register.html", {
                    "request": request,
                    "error": "Пользователь с таким email уже существует",
                    "user": None
                })

            hashed_password = bcrypt.hash(password)
            cur.execute("""INSERT INTO users (first_name, last_name, email, phone, password)
                           VALUES (%s, %s, %s, %s, %s) RETURNING id;""",
                        (first_name, last_name, email, phone, hashed_password))
            user_id = cur.fetchone()["id"]
            conn.commit()

    request.session["user"] = {
        "id": user_id,
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "phone": phone,
        "avatar_url": "/static/avatar.png"
    }

    return RedirectResponse("/profile", status_code=302)

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=302)

@app.post("/upload-avatar")
def upload_avatar(request: Request, avatar: UploadFile = File(...)):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=302)

    # Проверка размера (максимум 2 МБ)
    avatar.file.seek(0, os.SEEK_END)
    size = avatar.file.tell()
    avatar.file.seek(0)
    if size > 2 * 1024 * 1024:
        return templates.TemplateResponse("profile.html", {
            "request": request,
            "user": user,
            "error": "Файл слишком большой (максимум 2MB)"
        })

    upload_dir = "frontend/static/uploads"
    os.makedirs(upload_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    ext = avatar.filename.split('.')[-1] if '.' in avatar.filename else 'jpg'
    filename = f"user_{user['id']}_photo_{timestamp}.{ext}"
    file_path = os.path.join(upload_dir, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(avatar.file, buffer)

    avatar_url = f"/static/uploads/{filename}"

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE users SET avatar_url = %s WHERE id = %s", (avatar_url, user["id"]))
            conn.commit()

    request.session["user"]["avatar_url"] = avatar_url
    return RedirectResponse("/profile", status_code=302)

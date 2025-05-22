from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from backend.database import get_session
from sqlmodel import Session, select
from backend.models import User

router = APIRouter()
templates = Jinja2Templates(directory="frontend/templates")

@router.get("/register")
def register_get(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register")
def register_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session)
):
    existing_user = session.exec(select(User).where(User.username == username)).first()
    if existing_user:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Пользователь уже существует"})

    new_user = User(username=username, password=password)
    session.add(new_user)
    session.commit()
    request.session["user"] = username
    return RedirectResponse("/", status_code=302)

@router.get("/login")
def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
def login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session)
):
    user = session.exec(select(User).where(User.username == username)).first()
    if not user or user.password != password:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Неверные данные"})

    request.session["user"] = username
    return RedirectResponse("/", status_code=302)

@router.get("/profile")
def profile(request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login")
    return templates.TemplateResponse("profile.html", {"request": request, "user": user})

@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/")

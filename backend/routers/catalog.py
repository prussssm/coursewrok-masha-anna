from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from backend.database import get_session
from sqlalchemy.orm import Session
from sqlalchemy import select
from backend.models import Product

router = APIRouter()
templates = Jinja2Templates(directory="frontend/templates")

@router.get("/catalog")
def catalog(request: Request, session: Session = Depends(get_session)):
    products = session.exec(select(Product)).all()
    user = request.session.get("user")
    return templates.TemplateResponse("catalog_items.html", {
        "request": request,
        "products": products,
        "user": user
    })

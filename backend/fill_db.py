from backend.database import SessionLocal
from backend.models import MarmeladType, Product

def fill_db():
    db = SessionLocal()
    try:
        types = [
            MarmeladType(name="Кислый"),
            MarmeladType(name="Сладкий"),
            MarmeladType(name="Острый"),
        ]
        db.add_all(types)
        db.commit()

        products = [
            Product(name="Кислый лимон", description="Очень кислый лимонный мармелад", price=50, image_url="/static/lemon.jpg", marmelad_type_id=1),
            Product(name="Сладкая клубника", description="Нежный сладкий мармелад", price=45, image_url="/static/strawberry.jpg", marmelad_type_id=2),
            Product(name="Чили-мармелад", description="Острый, как перец", price=60, image_url="/static/chili.jpg", marmelad_type_id=3),
        ]
        db.add_all(products)
        db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    fill_db()

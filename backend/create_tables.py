from backend.database import Base, engine
from backend.models import User, Product

print("Создание таблиц...")
Base.metadata.create_all(bind=engine)
print("Готово.")

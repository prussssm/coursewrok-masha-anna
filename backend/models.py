from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

class MarmeladType(Base):
    __tablename__ = "marmelad_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    image_url = Column(String)
    description = Column(String)
    price = Column(String)
    marmelad_type_id = Column(Integer, ForeignKey("marmelad_types.id"))

    marmelad_type = relationship("MarmeladType")

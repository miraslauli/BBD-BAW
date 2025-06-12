from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import os

# Ustawienia bazy danych
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./aszwoj_shop.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Model użytkownika
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relacje
    orders = relationship("Order", back_populates="user")
    cart_items = relationship("CartItem", back_populates="user")

# Model kategorii produktów
class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relacje
    products = relationship("Product", back_populates="category")

# Model produktu
class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String)
    price = Column(Float, nullable=False)
    stock_quantity = Column(Integer, nullable=False, default=0)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relacje
    category = relationship("Category", back_populates="products")
    order_items = relationship("OrderItem", back_populates="product")
    cart_items = relationship("CartItem", back_populates="product")

# Model zamówienia
class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    total_amount = Column(Float, nullable=False)
    status = Column(String, nullable=False, default="pending")
    shipping_address = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacje
    user = relationship("User", back_populates="orders")
    order_items = relationship("OrderItem", back_populates="order")

# Model pozycji zamówienia
class OrderItem(Base):
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    
    # Relacje
    order = relationship("Order", back_populates="order_items")
    product = relationship("Product", back_populates="order_items")

# Model koszyka
class CartItem(Base):
    __tablename__ = "cart_items"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relacje
    user = relationship("User", back_populates="cart_items")
    product = relationship("Product", back_populates="cart_items")

# Tworzenie dodatkowych indeksów złożonych dla optymalizacji zapytań
Index('idx_user_email_active', User.email, User.is_active)
Index('idx_product_category_active', Product.category_id, Product.is_active)
Index('idx_product_price_range', Product.price, Product.is_active)
Index('idx_order_user_status', Order.user_id, Order.status)
Index('idx_cart_user_product', CartItem.user_id, CartItem.product_id)

# Tworzenie tabel
def create_tables():
    """Funkcja do bezpiecznego tworzenia tabel"""
    try:
        Base.metadata.create_all(bind=engine)
        print("Tabele utworzone pomyślnie")
    except Exception as e:
        print(f"Błąd podczas tworzenia tabel: {e}")
        raise

def get_db():
    """Generator sesji bazy danych"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 
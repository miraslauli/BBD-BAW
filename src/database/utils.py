import sqlite3
import json
import os
import shutil
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import text, inspect
from sqlalchemy.orm import Session
import random

from .models import engine, SessionLocal, User, Category, Product, Order, OrderItem, CartItem

# Ścieżki dla kopii zapasowych
BACKUP_DIR = "./backups"
DUMPS_DIR = "./dumps"

def ensure_directories():
    """Tworzenie katalogów dla kopii zapasowych i zrzutów"""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    os.makedirs(DUMPS_DIR, exist_ok=True)

def create_backup(backup_name: Optional[str] = None) -> str:
    """Tworzenie kopii zapasowej bazy danych SQLite"""
    ensure_directories()
    
    if not backup_name:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}.db"
    
    backup_path = os.path.join(BACKUP_DIR, backup_name)
    db_path = "aszwoj_shop.db"
    
    try:
        if os.path.exists(db_path):
            shutil.copy2(db_path, backup_path)
            print(f"✅ Kopia zapasowa utworzona: {backup_path}")
            return backup_path
        else:
            print(f"❌ Baza danych nie znaleziona: {db_path}")
            return ""
    except Exception as e:
        print(f"❌ Błąd podczas tworzenia kopii zapasowej: {e}")
        return ""

def restore_backup(backup_path: str) -> bool:
    """Przywracanie bazy danych z kopii zapasowej"""
    db_path = "aszwoj_shop.db"
    
    try:
        if os.path.exists(backup_path):
            # Tworzymy kopię zapasową obecnej bazy danych przed przywróceniem
            if os.path.exists(db_path):
                current_backup = f"before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                shutil.copy2(db_path, os.path.join(BACKUP_DIR, current_backup))
                print(f"📦 Aktualna baza danych zapisana jako: {current_backup}")
            
            shutil.copy2(backup_path, db_path)
            print(f"✅ Baza danych przywrócona z: {backup_path}")
            return True
        else:
            print(f"❌ Plik kopii zapasowej nie znaleziony: {backup_path}")
            return False
    except Exception as e:
        print(f"❌ Błąd podczas przywracania: {e}")
        return False

def create_sql_dump(dump_name: Optional[str] = None) -> str:
    """Создание SQL дампа базы данных"""
    ensure_directories()
    
    if not dump_name:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dump_name = f"dump_{timestamp}.sql"
    
    dump_path = os.path.join(DUMPS_DIR, dump_name)
    
    try:
        conn = sqlite3.connect("aszwoj_shop.db")
        
        with open(dump_path, 'w', encoding='utf-8') as f:
            f.write(f"-- SQL Dump created at {datetime.now()}\n")
            f.write("-- ASzWoj Shop Database\n\n")
            
            # Zrzut schematu i danych
            for line in conn.iterdump():
                f.write(f"{line}\n")
        
        conn.close()
        print(f"✅ Zrzut SQL utworzony: {dump_path}")
        return dump_path
    except Exception as e:
        print(f"❌ Błąd podczas tworzenia zrzutu SQL: {e}")
        return ""

def get_table_info() -> Dict[str, Any]:
    """Pobieranie informacji o tabelach i indeksach"""
    info = {}
    
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        for table in tables:
            columns = inspector.get_columns(table)
            indexes = inspector.get_indexes(table)
            foreign_keys = inspector.get_foreign_keys(table)
            
            info[table] = {
                "columns": [{"name": col["name"], "type": str(col["type"])} for col in columns],
                "indexes": [{"name": idx["name"], "columns": idx["column_names"]} for idx in indexes],
                "foreign_keys": foreign_keys
            }
        
        return info
    except Exception as e:
        print(f"❌ Błąd podczas pobierania informacji o tabelach: {e}")
        return {}

def execute_custom_sql(sql_query: str) -> List[Dict[str, Any]]:
    """Wykonywanie dowolnego zapytania SQL"""
    try:
        with engine.connect() as connection:
            result = connection.execute(text(sql_query))
            
            if result.returns_rows:
                columns = result.keys()
                rows = result.fetchall()
                return [dict(zip(columns, row)) for row in rows]
            else:
                connection.commit()
                return [{"message": "Query executed successfully", "rowcount": result.rowcount}]
    except Exception as e:
        print(f"❌ Błąd podczas wykonywania SQL: {e}")
        return [{"error": str(e)}]

# Operacje CRUD do demonstracji
def create_sample_data():
    """Tworzenie danych testowych"""
    db = SessionLocal()
    try:
        # Tworzenie kategorii
        categories = [
            Category(name="Elektronika", description="Sprzęt AGD i gadżety"),
            Category(name="Odzież", description="Odzież męska i damska"),
            Category(name="Książki", description="Literatura piękna i naukowa"),
            Category(name="Sport", description="Sprzęt sportowy i wyposażenie")
        ]
        
        for category in categories:
            existing = db.query(Category).filter_by(name=category.name).first()
            if not existing:
                db.add(category)
        
        db.commit()
        
        # Tworzenie produktów
        products_data = [
            {"name": "iPhone 15", "price": 999.99, "category": "Elektronika", "stock": 50},
            {"name": "MacBook Pro", "price": 2499.99, "category": "Elektronika", "stock": 20},
            {"name": "Koszulka Nike", "price": 29.99, "category": "Odzież", "stock": 100},
            {"name": "Jeans Levi's", "price": 89.99, "category": "Odzież", "stock": 75},
            {"name": "Harry Potter", "price": 15.99, "category": "Książki", "stock": 200},
            {"name": "Podręcznik Python", "price": 45.99, "category": "Książki", "stock": 80},
            {"name": "Buty Adidas", "price": 129.99, "category": "Sport", "stock": 60},
            {"name": "Piłka nożna", "price": 25.99, "category": "Sport", "stock": 40}
        ]
        
        for prod_data in products_data:
            existing = db.query(Product).filter_by(name=prod_data["name"]).first()
            if not existing:
                category = db.query(Category).filter_by(name=prod_data["category"]).first()
                product = Product(
                    name=prod_data["name"],
                    price=prod_data["price"],
                    category_id=category.id,
                    stock_quantity=prod_data["stock"],
                    description=f"Opis produktu {prod_data['name']}"
                )
                db.add(product)
        
        db.commit()
        print("✅ Dane testowe zostały utworzone")
        
    except Exception as e:
        print(f"❌ Błąd podczas tworzenia danych testowych: {e}")
        db.rollback()
    finally:
        db.close()

def get_random_crud_operations() -> List[Dict[str, Any]]:
    """Wykonywanie losowych operacji CRUD"""
    operations = []
    db = SessionLocal()
    
    try:
        # CREATE - tworzenie losowego produktu
        categories = db.query(Category).all()
        if categories:
            random_category = random.choice(categories)
            random_product = Product(
                name=f"Produkt_{random.randint(1000, 9999)}",
                price=round(random.uniform(10, 1000), 2),
                category_id=random_category.id,
                stock_quantity=random.randint(1, 100),
                description="Losowo utworzony produkt"
            )
            db.add(random_product)
            db.commit()
            operations.append({
                "operation": "CREATE",
                "table": "products",
                "data": {"name": random_product.name, "price": random_product.price}
            })
        
        # READ - odczyt losowych produktów
        products = db.query(Product).limit(5).all()
        operations.append({
            "operation": "READ",
            "table": "products",
            "count": len(products),
            "data": [{"id": p.id, "name": p.name, "price": p.price} for p in products]
        })
        
        # UPDATE - aktualizacja losowego produktu
        random_product = db.query(Product).order_by(Product.id.desc()).first()
        if random_product:
            old_price = random_product.price
            random_product.price = round(random.uniform(10, 1000), 2)
            db.commit()
            operations.append({
                "operation": "UPDATE",
                "table": "products",
                "id": random_product.id,
                "old_price": old_price,
                "new_price": random_product.price
            })
        
        # DELETE - usuwanie starego produktu (jeśli jest więcej niż 10)
        product_count = db.query(Product).count()
        if product_count > 10:
            old_product = db.query(Product).first()
            db.delete(old_product)
            db.commit()
            operations.append({
                "operation": "DELETE",
                "table": "products",
                "deleted_id": old_product.id,
                "deleted_name": old_product.name
            })
        
        return operations
        
    except Exception as e:
        print(f"❌ Błąd podczas wykonywania operacji CRUD: {e}")
        db.rollback()
        return [{"error": str(e)}]
    finally:
        db.close()

def get_database_statistics() -> Dict[str, Any]:
    """Pobieranie statystyk bazy danych"""
    db = SessionLocal()
    try:
        from sqlalchemy import func
        stats = {
            "users_count": db.query(User).count(),
            "categories_count": db.query(Category).count(),
            "products_count": db.query(Product).count(),
            "active_products_count": db.query(Product).filter_by(is_active=True).count(),
            "orders_count": db.query(Order).count(),
            "cart_items_count": db.query(CartItem).count(),
            "total_orders_value": db.query(func.sum(Order.total_amount)).scalar() or 0,
            "average_product_price": db.query(func.avg(Product.price)).scalar() or 0
        }
        return stats
    except Exception as e:
        print(f"❌ Błąd podczas pobierania statystyk: {e}")
        return {"error": str(e)}
    finally:
        db.close() 
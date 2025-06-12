from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from .utils import (
    create_backup,
    restore_backup,
    create_sql_dump,
    get_table_info,
    execute_custom_sql,
    create_sample_data,
    get_random_crud_operations,
    get_database_statistics,
)
from .models import create_tables, get_db, User

database_router = APIRouter(prefix="/database", tags=["database"])


@database_router.post("/init")
def initialize_database():
    """Inicjalizacja bazy danych - tworzenie tabel"""
    try:
        create_tables()
        return {"message": "Baza danych została pomyślnie zainicjalizowana"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Błąd inicjalizacji bazy danych: {str(e)}"
        )


@database_router.post("/sample-data")
def create_test_data():
    """Tworzenie danych testowych"""
    try:
        create_sample_data()
        return {"message": "Dane testowe zostały pomyślnie utworzone"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Błąd tworzenia danych testowych: {str(e)}"
        )


@database_router.post("/backup")
def create_database_backup(backup_name: Optional[str] = Query(None)):
    """Tworzenie kopii zapasowej bazy danych"""
    try:
        backup_path = create_backup(backup_name)
        if backup_path:
            return {
                "message": "Kopia zapasowa została pomyślnie utworzona",
                "backup_path": backup_path,
            }
        else:
            raise HTTPException(
                status_code=500, detail="Nie udało się utworzyć kopii zapasowej"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Błąd tworzenia kopii zapasowej: {str(e)}"
        )


@database_router.post("/restore")
def restore_database(backup_path: str):
    """Przywracanie bazy danych z kopii zapasowej"""
    try:
        success = restore_backup(backup_path)
        if success:
            return {"message": "Baza danych została pomyślnie przywrócona"}
        else:
            raise HTTPException(
                status_code=400, detail="Nie udało się przywrócić bazy danych"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd przywracania: {str(e)}")


@database_router.post("/dump")
def create_database_dump(dump_name: Optional[str] = Query(None)):
    """Tworzenie zrzutu SQL bazy danych"""
    try:
        dump_path = create_sql_dump(dump_name)
        if dump_path:
            return {
                "message": "Zrzut SQL został utworzony pomyślnie",
                "dump_path": dump_path,
            }
        else:
            raise HTTPException(
                status_code=500, detail="Nie udało się utworzyć zrzutu SQL"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd tworzenia zrzutu: {str(e)}")


@database_router.get("/tables")
def get_tables_info():
    """Pobieranie informacji o tabelach i indeksach"""
    try:
        info = get_table_info()
        return info
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Błąd pobierania informacji o tabelach: {str(e)}"
        )


@database_router.post("/execute-sql")
def execute_sql_query(sql_query: str):
    """Wykonywanie dowolnego zapytania SQL"""
    try:
        result = execute_custom_sql(sql_query)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd wykonywania SQL: {str(e)}")


@database_router.get("/crud-demo")
def perform_crud_operations():
    """Demonstracja losowych operacji CRUD"""
    try:
        operations = get_random_crud_operations()
        return {"operations": operations}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Błąd wykonywania operacji CRUD: {str(e)}"
        )


@database_router.get("/statistics")
def get_db_statistics():
    """Pobieranie statystyk bazy danych"""
    try:
        stats = get_database_statistics()
        return {"statistics": stats}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Błąd pobierania statystyk: {str(e)}"
        )


# Dodatkowe endpointy do demonstracji indeksów
@database_router.get("/test-indexes")
def test_database_indexes():
    """Testowanie wydajności indeksów"""
    try:
        test_queries = [
            "SELECT * FROM products WHERE price > 100",
            "SELECT * FROM users WHERE email LIKE '%example%'",
            "SELECT * FROM orders WHERE status = 'pending'",
            "SELECT p.name, c.name as category FROM products p JOIN categories c ON p.category_id = c.id",
            "SELECT COUNT(*) FROM products WHERE is_active = 1 AND category_id = 1",
        ]

        results = []
        for query in test_queries:
            result = execute_custom_sql(f"EXPLAIN QUERY PLAN {query}")
            results.append({"query": query, "execution_plan": result})

        return {"index_tests": results}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Błąd testowania indeksów: {str(e)}"
        )


@database_router.get("/sample-queries")
def get_sample_queries():
    """Przykłady zapytań SQL do testowania"""
    sample_queries = [
        "SELECT COUNT(*) as total_products FROM products",
        "SELECT c.name, COUNT(p.id) as products_count FROM categories c LEFT JOIN products p ON c.id = p.category_id GROUP BY c.id, c.name",
        "SELECT * FROM products WHERE price BETWEEN 50 AND 200 ORDER BY price DESC",
        "SELECT u.email, COUNT(o.id) as orders_count FROM users u LEFT JOIN orders o ON u.id = o.user_id GROUP BY u.id, u.email",
        "SELECT p.name, p.price, c.name as category FROM products p JOIN categories c ON p.category_id = c.id WHERE p.is_active = 1",
        "INSERT INTO categories (name, description) VALUES ('Nowa kategoria', 'Opis nowej kategorii')",
        "UPDATE products SET price = price * 1.1 WHERE category_id = 1",
        "DELETE FROM products WHERE stock_quantity = 0 AND is_active = 0",
    ]

    return {"sample_queries": sample_queries}


@database_router.post("/make-admin/{user_id}")
def make_user_admin(user_id: int, db: Session = Depends(get_db)):
    """Tymczasowy endpoint do nadania uprawnień administratora użytkownikowi"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Użytkownik nie znaleziony")

    user.is_admin = True
    db.commit()
    db.refresh(user)

    return {
        "message": f"Użytkownik {user.email} otrzymał uprawnienia administratora",
        "user_id": user.id,
        "is_admin": user.is_admin,
    }


@database_router.get("/users")
def list_users(db: Session = Depends(get_db)):
    """Lista wszystkich użytkowników (do debugowania)"""
    users = db.query(User).all()
    return [
        {
            "id": user.id,
            "email": user.email,
            "is_admin": user.is_admin,
            "is_active": user.is_active,
        }
        for user in users
    ]

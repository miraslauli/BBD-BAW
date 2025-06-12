from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from src.database.models import get_db, Product, Category, User
from src.auth.dependencies import get_current_admin_user
from .schemas import (
    ProductResponse,
    CategoryResponse,
    ProductCreate,
    ProductUpdate,
    CategoryCreate,
    CategoryUpdate,
)

products_router = APIRouter(prefix="/products", tags=["products"])


@products_router.get("/", response_model=List[ProductResponse])
def get_products(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category_id: Optional[int] = Query(None),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
):
    """Pobieranie listy produktów z filtrowaniem"""
    query = db.query(Product).filter(Product.is_active == True).join(Category)

    if category_id:
        query = query.filter(Product.category_id == category_id)

    if min_price:
        query = query.filter(Product.price >= min_price)

    if max_price:
        query = query.filter(Product.price <= max_price)

    products = query.order_by(Product.created_at.desc()).offset(skip).limit(limit).all()

    return [
        ProductResponse(
            id=product.id,
            name=product.name,
            description=product.description,
            price=product.price,
            stock_quantity=product.stock_quantity,
            category_id=product.category_id,
            category_name=product.category.name,
            is_active=product.is_active,
            created_at=product.created_at,
        )
        for product in products
    ]


@products_router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """Pobieranie szczegółów produktu"""
    product = (
        db.query(Product)
        .filter(Product.id == product_id, Product.is_active == True)
        .join(Category)
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Produkt nie znaleziony"
        )

    return ProductResponse(
        id=product.id,
        name=product.name,
        description=product.description,
        price=product.price,
        stock_quantity=product.stock_quantity,
        category_id=product.category_id,
        category_name=product.category.name,
        is_active=product.is_active,
        created_at=product.created_at,
    )


@products_router.get("/categories/", response_model=List[CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    """Pobieranie listy kategorii"""
    categories = db.query(Category).order_by(Category.name).all()

    return [
        CategoryResponse(
            id=category.id,
            name=category.name,
            description=category.description,
            created_at=category.created_at,
        )
        for category in categories
    ]


# Funkcje administracyjne do zarządzania produktami
@products_router.post("/admin/", response_model=ProductResponse)
def create_product_admin(
    product_data: ProductCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Tworzenie nowego produktu (tylko dla administratora)"""
    # Sprawdzamy istnienie kategorii
    category = (
        db.query(Category).filter(Category.id == product_data.category_id).first()
    )
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Kategoria nie znaleziona"
        )

    # Sprawdzamy unikalność nazwy produktu
    existing_product = (
        db.query(Product).filter(Product.name == product_data.name).first()
    )
    if existing_product:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Produkt o tej nazwie już istnieje",
        )

    product = Product(
        name=product_data.name,
        description=product_data.description,
        price=product_data.price,
        stock_quantity=product_data.stock_quantity,
        category_id=product_data.category_id,
        is_active=product_data.is_active,
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    return ProductResponse(
        id=product.id,
        name=product.name,
        description=product.description,
        price=product.price,
        stock_quantity=product.stock_quantity,
        category_id=product.category_id,
        category_name=category.name,
        is_active=product.is_active,
        created_at=product.created_at,
    )


@products_router.put("/admin/{product_id}", response_model=ProductResponse)
def update_product_admin(
    product_id: int,
    product_data: ProductUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Aktualizacja produktu (tylko dla administratora)"""
    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Produkt nie znaleziony"
        )

    # Sprawdzamy unikalność nazwy, jeśli jest aktualizowana
    if product_data.name and product_data.name != product.name:
        existing_product = (
            db.query(Product).filter(Product.name == product_data.name).first()
        )
        if existing_product:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Produkt o tej nazwie już istnieje",
            )

    # Sprawdzamy istnienie kategorii, jeśli jest aktualizowana
    if product_data.category_id:
        category = (
            db.query(Category).filter(Category.id == product_data.category_id).first()
        )
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Kategoria nie znaleziona"
            )

    # Aktualizujemy pola
    update_data = product_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)

    return ProductResponse(
        id=product.id,
        name=product.name,
        description=product.description,
        price=product.price,
        stock_quantity=product.stock_quantity,
        category_id=product.category_id,
        category_name=product.category.name,
        is_active=product.is_active,
        created_at=product.created_at,
    )


@products_router.delete("/{product_id}", dependencies=[Depends(get_current_admin_user)])
def delete_product(product_id: int, db: Session = Depends(get_db)):
    """Usuwanie produktu (tylko dla administratora)"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produkt nie znaleziony")
    db.delete(product)
    db.commit()
    return {"message": f"Produkt '{product.name}' został usunięty"}


@products_router.get(
    "/all-admin",
    response_model=List[ProductResponse],
    dependencies=[Depends(get_current_admin_user)],
)
def get_all_products_admin(db: Session = Depends(get_db)):
    """Pobieranie wszystkich produktów, w tym nieaktywnych (tylko dla administratora)"""
    products = db.query(Product).all()
    return products


# Funkcje administracyjne do zarządzania kategoriami
@products_router.post("/categories/admin/", response_model=CategoryResponse)
def create_category_admin(
    category_data: CategoryCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Tworzenie nowej kategorii (tylko dla administratora)"""
    # Sprawdzanie unikalności nazwy kategorii
    existing_category = (
        db.query(Category).filter(Category.name == category_data.name).first()
    )
    if existing_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kategoria o tej nazwie już istnieje",
        )

    category = Category(name=category_data.name, description=category_data.description)

    db.add(category)
    db.commit()
    db.refresh(category)

    return CategoryResponse(
        id=category.id,
        name=category.name,
        description=category.description,
        created_at=category.created_at,
    )


@products_router.put("/categories/admin/{category_id}", response_model=CategoryResponse)
def update_category_admin(
    category_id: int,
    category_data: CategoryUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Aktualizacja kategorii (tylko dla administratora)"""
    category = db.query(Category).filter(Category.id == category_id).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Kategoria nie znaleziona"
        )

    # Sprawdzanie unikalności nazwy, jeśli jest aktualizowana
    if category_data.name and category_data.name != category.name:
        existing_category = (
            db.query(Category).filter(Category.name == category_data.name).first()
        )
        if existing_category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Kategoria o tej nazwie już istnieje",
            )

    # Aktualizujemy pola
    update_data = category_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)

    db.commit()
    db.refresh(category)

    return CategoryResponse(
        id=category.id,
        name=category.name,
        description=category.description,
        created_at=category.created_at,
    )


@products_router.delete(
    "/categories/admin/{category_id}", dependencies=[Depends(get_current_admin_user)]
)
def delete_category_admin(
    category_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Usuwanie kategorii (tylko dla administratora)"""
    category = db.query(Category).filter(Category.id == category_id).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Kategoria nie znaleziona"
        )

    # Sprawdzanie, czy są produkty w tej kategorii
    products_count = (
        db.query(Product).filter(Product.category_id == category_id).count()
    )
    if products_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Nie można usunąć kategorii, ponieważ zawiera produkty ({products_count} szt.)",
        )

    db.delete(category)
    db.commit()

    return {"message": f"Kategoria '{category.name}' została usunięta"}

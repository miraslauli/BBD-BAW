from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict

from src.database.models import get_db, User, Product, Category, Order, OrderItem, CartItem
from src.auth.dependencies import get_current_admin_user
from pydantic import BaseModel

stats_router = APIRouter(
    prefix="/stats",
    tags=["statistics"]
)


class StatisticsResponse(BaseModel):
    """Ogólny schemat dla statystyk"""
    period: str
    data: Dict[str, Any]


class SalesStatistics(BaseModel):
    """Statystyki sprzedaży"""
    total_orders: int
    total_revenue: float
    avg_order_value: float
    orders_by_status: Dict[str, int]
    top_products: List[Dict[str, Any]]
    revenue_by_category: List[Dict[str, Any]]
    daily_sales: List[Dict[str, Any]]


class UserStatistics(BaseModel):
    """Statystyki użytkowników"""
    total_users: int
    active_users: int
    new_users_today: int
    new_users_this_week: int
    users_with_orders: int
    avg_orders_per_user: float


class ProductStatistics(BaseModel):
    """Statystyki produktów"""
    total_products: int
    active_products: int
    out_of_stock: int
    low_stock: int
    most_popular: List[Dict[str, Any]]
    least_popular: List[Dict[str, Any]]
    avg_price: float


@stats_router.get("/overview", response_model=Dict[str, Any])
def get_overview_statistics(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Ogólny przegląd statystyk dla dashboardu"""
    # Metryki ogólne
    total_users = db.query(User).count()
    total_products = db.query(Product).count()
    total_orders = db.query(Order).count()
    total_revenue = db.query(func.sum(Order.total_amount)).scalar() or 0.0
    
    # Metryki aktywne
    active_products = db.query(Product).filter(Product.is_active == True).count()
    pending_orders = db.query(Order).filter(Order.status == 'pending').count()
    
    # Metryki dzisiejsze
    today = datetime.utcnow().date()
    today_orders = db.query(Order).filter(
        func.date(Order.created_at) == today
    ).count()
    
    today_revenue = db.query(func.sum(Order.total_amount)).filter(
        func.date(Order.created_at) == today
    ).scalar() or 0.0
    
    return {
        "general": {
            "total_users": total_users,
            "total_products": total_products,
            "total_orders": total_orders,
            "total_revenue": round(total_revenue, 2)
        },
        "active": {
            "active_products": active_products,
            "pending_orders": pending_orders
        },
        "today": {
            "orders": today_orders,
            "revenue": round(today_revenue, 2)
        }
    }


@stats_router.get("/sales", response_model=SalesStatistics)
def get_sales_statistics(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
    days: int = Query(30, ge=1, le=365, description="Liczba dni do analizy")
):
    """Statystyki sprzedaży"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Ogólne metryki sprzedaży
    orders_query = db.query(Order).filter(Order.created_at >= start_date)
    total_orders = orders_query.count()
    total_revenue = orders_query.with_entities(func.sum(Order.total_amount)).scalar() or 0.0
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0.0
    
    # Zamówienia według statusów
    orders_by_status = dict(
        db.query(Order.status, func.count(Order.id))
        .filter(Order.created_at >= start_date)
        .group_by(Order.status)
        .all()
    )
    
    # Najpopularniejsze produkty
    top_products = db.query(
        Product.name,
        func.sum(OrderItem.quantity).label('total_sold'),
        func.sum(OrderItem.total_price).label('total_revenue')
    ).join(OrderItem).join(Order).filter(
        Order.created_at >= start_date
    ).group_by(Product.id, Product.name).order_by(
        desc('total_sold')
    ).limit(10).all()
    
    top_products_list = [
        {
            "name": name,
            "total_sold": int(total_sold),
            "total_revenue": float(total_revenue)
        }
        for name, total_sold, total_revenue in top_products
    ]
    
    # Przychody według kategorii
    revenue_by_category = db.query(
        Category.name,
        func.sum(OrderItem.total_price).label('revenue')
    ).join(Product).join(OrderItem).join(Order).filter(
        Order.created_at >= start_date
    ).group_by(Category.id, Category.name).order_by(
        desc('revenue')
    ).all()
    
    revenue_by_category_list = [
        {"category": name, "revenue": float(revenue)}
        for name, revenue in revenue_by_category
    ]
    
    # Dzienne sprzedaże za ostatnie 7 dni
    last_week = datetime.utcnow() - timedelta(days=7)
    daily_sales = db.query(
        func.date(Order.created_at).label('date'),
        func.count(Order.id).label('orders'),
        func.sum(Order.total_amount).label('revenue')
    ).filter(Order.created_at >= last_week).group_by(
        func.date(Order.created_at)
    ).order_by('date').all()
    
    daily_sales_list = [
        {
            "date": str(date),
            "orders": orders,
            "revenue": float(revenue or 0)
        }
        for date, orders, revenue in daily_sales
    ]
    
    return SalesStatistics(
        total_orders=total_orders,
        total_revenue=round(total_revenue, 2),
        avg_order_value=round(avg_order_value, 2),
        orders_by_status=orders_by_status,
        top_products=top_products_list,
        revenue_by_category=revenue_by_category_list,
        daily_sales=daily_sales_list
    )


@stats_router.get("/users", response_model=UserStatistics)
def get_user_statistics(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Statystyki użytkowników"""
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    
    # Nowi użytkownicy dzisiaj
    today = datetime.utcnow().date()
    new_users_today = db.query(User).filter(
        func.date(User.created_at) == today
    ).count()
    
    # Nowi użytkownicy w tym tygodniu
    week_ago = datetime.utcnow() - timedelta(days=7)
    new_users_this_week = db.query(User).filter(
        User.created_at >= week_ago
    ).count()
    
    # Użytkownicy z zamówieniami
    users_with_orders = db.query(func.count(func.distinct(Order.user_id))).scalar() or 0
    
    # Średnia liczba zamówień na użytkownika
    total_orders = db.query(Order).count()
    avg_orders_per_user = total_orders / users_with_orders if users_with_orders > 0 else 0.0
    
    return UserStatistics(
        total_users=total_users,
        active_users=active_users,
        new_users_today=new_users_today,
        new_users_this_week=new_users_this_week,
        users_with_orders=users_with_orders,
        avg_orders_per_user=round(avg_orders_per_user, 2)
    )


@stats_router.get("/products", response_model=ProductStatistics)
def get_product_statistics(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
    low_stock_threshold: int = Query(10, ge=1, description="Próg dla produktów o niskim stanie")
):
    """Statystyki produktów"""
    total_products = db.query(Product).count()
    active_products = db.query(Product).filter(Product.is_active == True).count()
    out_of_stock = db.query(Product).filter(Product.stock_quantity == 0).count()
    low_stock = db.query(Product).filter(
        and_(Product.stock_quantity > 0, Product.stock_quantity <= low_stock_threshold)
    ).count()
    
    # Średnia cena
    avg_price = db.query(func.avg(Product.price)).scalar() or 0.0
    
    # Najpopularniejsze produkty (według liczby zamówień)
    most_popular = db.query(
        Product.name,
        func.count(OrderItem.id).label('order_count'),
        func.sum(OrderItem.quantity).label('total_sold')
    ).join(OrderItem).group_by(Product.id, Product.name).order_by(
        desc('order_count')
    ).limit(10).all()
    
    most_popular_list = [
        {
            "name": name,
            "order_count": order_count,
            "total_sold": int(total_sold)
        }
        for name, order_count, total_sold in most_popular
    ]
    
    # Najmniej popularne produkty
    least_popular = db.query(Product.name, Product.stock_quantity).filter(
        Product.is_active == True
    ).outerjoin(OrderItem).group_by(Product.id, Product.name, Product.stock_quantity).having(
        func.count(OrderItem.id) == 0
    ).limit(10).all()
    
    least_popular_list = [
        {
            "name": name,
            "stock_quantity": stock_quantity,
            "order_count": 0
        }
        for name, stock_quantity in least_popular
    ]
    
    return ProductStatistics(
        total_products=total_products,
        active_products=active_products,
        out_of_stock=out_of_stock,
        low_stock=low_stock,
        most_popular=most_popular_list,
        least_popular=least_popular_list,
        avg_price=round(avg_price, 2)
    )


@stats_router.get("/inventory/alerts")
def get_inventory_alerts(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
    low_stock_threshold: int = Query(10, ge=1)
):
    """Powiadomienia o stanie magazynu"""
    # Produkty się skończyły
    out_of_stock = db.query(Product).filter(
        Product.stock_quantity == 0,
        Product.is_active == True
    ).all()
    
    # Produkty o niskim stanie
    low_stock = db.query(Product).filter(
        and_(
            Product.stock_quantity > 0,
            Product.stock_quantity <= low_stock_threshold,
            Product.is_active == True
        )
    ).all()
    
    return {
        "out_of_stock": [
            {
                "id": product.id,
                "name": product.name,
                "stock_quantity": product.stock_quantity
            }
            for product in out_of_stock
        ],
        "low_stock": [
            {
                "id": product.id,
                "name": product.name,
                "stock_quantity": product.stock_quantity,
                "threshold": low_stock_threshold
            }
            for product in low_stock
        ]
    }
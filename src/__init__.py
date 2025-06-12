from fastapi import APIRouter

from src.users.views import users_router
from src.products.views import products_router
from src.auth.views import auth_router
from src.orders.views import orders_router
from src.stats.views import stats_router
from src.admins.views import admins_router
from src.database.views import database_router
from src.cart.views import cart_router

router = APIRouter()

router.include_router(users_router)
router.include_router(products_router)
router.include_router(auth_router)
router.include_router(orders_router)
router.include_router(stats_router)
router.include_router(admins_router)
router.include_router(database_router)
router.include_router(cart_router)
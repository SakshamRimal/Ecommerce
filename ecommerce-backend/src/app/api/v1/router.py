from fastapi import APIRouter
from app.api.v1.health.controller import router as health_router
from app.api.v1.auth.controller import router as auth_router
from app.api.v1.categories.controller import router as categories_router
from app.api.v1.products.controller import router as products_router
from app.api.v1.cart.controller import router as cart_router
from app.api.v1.orders.controller import router as orders_router
from app.api.v1.search.controller import router as search_router
from app.api.v1.chat.controller import router as chat_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(categories_router)
api_router.include_router(products_router)
api_router.include_router(cart_router)
api_router.include_router(orders_router)
api_router.include_router(search_router)
api_router.include_router(chat_router)
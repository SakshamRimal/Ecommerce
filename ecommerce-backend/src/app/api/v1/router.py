from fastapi import APIRouter, Depends
from app.api.v1.health.controller import router as health_router
from app.api.v1.auth.controller import router as auth_router
from app.api.v1.categories.controller import router as categories_router
from app.api.v1.products.controller import router as products_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(categories_router)
api_router.include_router(products_router)
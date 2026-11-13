from fastapi import APIRouter
from app.api.v1.endpoints import auth, health, products, ingredients, categories, scans, analysis, suitability, journal, admin

api_router = APIRouter()
api_router.include_router(health.router, prefix="", tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(products.router, prefix="/products", tags=["Products"])
api_router.include_router(ingredients.router, prefix="/ingredients", tags=["Ingredients"])
api_router.include_router(categories.router, prefix="/categories", tags=["Categories"])
api_router.include_router(scans.router, prefix="", tags=["Food Scanner"])
api_router.include_router(analysis.router, prefix="", tags=["Nutrition Analysis"])
api_router.include_router(suitability.router, prefix="", tags=["Dietary Suitability"])
api_router.include_router(journal.router, prefix="/journal", tags=["Food Journal & Analytics"])
api_router.include_router(admin.router, prefix="/admin", tags=["Administration"])

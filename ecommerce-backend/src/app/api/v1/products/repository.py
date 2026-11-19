import re
import uuid
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.product import Product
from app.core.exceptions import ConflictError

_SEARCH_STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "for",
    "from",
    "how",
    "i",
    "in",
    "is",
    "it",
    "me",
    "my",
    "of",
    "on",
    "or",
    "some",
    "something",
    "someone",
    "that",
    "the",
    "to",
    "want",
    "what",
    "who",
    "with",
}

_SEMANTIC_CONCEPT_SYNONYMS: dict[str, list[str]] = {
    "quiet": ["noise", "cancelling", "headphones", "earbuds", "audio", "purifier", "whisper"],
    "focus": ["headphones", "noise", "desk", "workspace", "keyboard", "lamp"],
    "deep": ["headphones", "noise", "focus", "studio", "work"],
    "work": ["workspace", "keyboard", "mouse", "desk", "lamp", "headphones", "laptop", "backpack"],
    "travel": ["backpack", "power", "bank", "headphones", "earbuds", "camera", "sunglasses", "commute"],
    "commute": ["backpack", "laptop", "waterproof", "earbuds", "mug", "power"],
    "ergonomic": ["mouse", "keyboard", "wrist", "desk", "shelf", "workspace", "comfort"],
    "wrist": ["ergonomic", "mouse", "keyboard", "fatigue", "desk"],
    "fatigue": ["ergonomic", "mouse", "keyboard", "comfort", "recovery", "shoes"],
    "coding": ["keyboard", "mechanical", "mouse", "desk", "lamp", "shelf", "headphones"],
    "minimalist": ["lamp", "desk", "shelf", "light", "watch", "workspace"],
    "lighting": ["lamp", "light", "led", "ambient", "night", "desk"],
    "night": ["lamp", "light", "led", "ambient", "projector"],
    "nights": ["lamp", "light", "led", "ambient", "projector"],
    "late": ["lamp", "light", "led", "coffee", "desk"],
    "waterproof": ["backpack", "trail", "running", "shoes", "watch", "rain"],
    "bag": ["backpack", "pack", "commute", "laptop", "carry"],
    "laptop": ["backpack", "power", "bank", "desk", "shelf", "usb"],
    "rain": ["waterproof", "trail", "backpack", "running", "shoes", "jacket"],
    "hiking": ["trail", "running", "shoes", "backpack", "watch", "waterproof", "outdoor"],
    "running": ["shoes", "nike", "trail", "marathon", "trainers", "sprint"],
    "workout": ["shoes", "trainers", "earbuds", "running", "sports", "fitness"],
    "coffee": ["grinder", "kettle", "mug", "scale", "espresso", "brew", "carafe", "beans"],
    "morning": ["coffee", "grinder", "kettle", "mug", "scale", "running"],
    "gift": ["watch", "headphones", "coffee", "keyboard", "camera", "sunglasses", "speaker"],
    "loves": ["coffee", "music", "headphones", "camera", "watch"],
    "music": ["headphones", "speakers", "earbuds", "microphone", "audio", "studio"],
    "movie": ["projector", "speakers", "light", "ambient"],
    "air": ["purifier", "hepa", "nike", "max", "clean"],
}


class ProductRepository:
    def __init__(self , session:AsyncSession):
        self.session = session
        
    async def get_by_id(self , product_id: uuid.UUID) -> Product | None:
        stmt = (
            select(Product)
            .options(joinedload(Product.category))
            .where(Product.id == product_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def list_products(
        self , limit: int = 50 , offset: int = 0 , category_id: uuid.UUID | None = None
    ) -> list[Product]:
        stmt = select(Product).options(joinedload(Product.category))
        if category_id:
            stmt = stmt.where(Product.category_id == category_id)
        stmt = stmt.order_by(Product.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def search_by_keyword(
        self,
        query: str,
        limit: int = 20,
        offset: int = 0,
        min_price=None,
        max_price=None,
        category_id: uuid.UUID | None = None,
    ) -> list[Product]:
        """Token-aware PostgreSQL search across product name, description, and category."""
        raw_tokens = [
            t for t in re.findall(r"[a-z0-9]+", query.lower()) if len(t) >= 2
        ]
        meaningful_tokens = [
            t for t in raw_tokens if t not in _SEARCH_STOP_WORDS
        ] or raw_tokens

        stmt = (
            select(Product)
            .join(Category, Product.category_id == Category.id, isouter=True)
            .options(joinedload(Product.category))
        )

        clauses = [
            Product.name.ilike(f"%{query.strip()}%"),
            Product.description.ilike(f"%{query.strip()}%"),
        ]
        for tok in meaningful_tokens:
            stem = tok[:-1] if tok.endswith("s") and len(tok) > 4 else tok
            pat = f"%{stem}%"
            clauses.append(Product.name.ilike(pat))
            clauses.append(Product.description.ilike(pat))
            clauses.append(Category.name.ilike(pat))

        stmt = stmt.where(or_(*clauses))

        if min_price is not None:
            stmt = stmt.where(Product.price >= min_price)
        if max_price is not None:
            stmt = stmt.where(Product.price <= max_price)
        if category_id is not None:
            stmt = stmt.where(Product.category_id == category_id)

        result = await self.session.execute(stmt)
        candidates = list(result.scalars().unique().all())

        # Rank candidates by exact phrase match, then name/category/description token hits
        q_low = query.strip().lower()

        def _score(p: Product) -> tuple[int, int]:
            name_low = (p.name or "").lower()
            desc_low = (p.description or "").lower()
            cat_low = (p.category.name if getattr(p, "category", None) else "").lower()
            score = 0
            if q_low and q_low in name_low:
                score += 20
            if q_low and q_low in desc_low:
                score += 10
            for tok in meaningful_tokens:
                stem = tok[:-1] if tok.endswith("s") and len(tok) > 4 else tok
                if stem in name_low:
                    score += 6
                if stem in cat_low:
                    score += 4
                if stem in desc_low:
                    score += 2
            return (score, p.stock_quantity or 0)

        candidates.sort(key=_score, reverse=True)
        return candidates[offset : offset + limit]

    async def semantic_concept_search(
        self,
        query: str,
        limit: int = 10,
        offset: int = 0,
        min_price=None,
        max_price=None,
        category_id: uuid.UUID | None = None,
    ) -> list[Product]:
        """Semantic concept & synonym matcher used when vector embeddings are unavailable."""
        raw_tokens = [
            t for t in re.findall(r"[a-z0-9]+", query.lower()) if len(t) >= 2
        ]
        base_tokens = [
            t for t in raw_tokens if t not in _SEARCH_STOP_WORDS
        ] or raw_tokens

        expanded_weights: dict[str, int] = {}
        for tok in base_tokens:
            stem = tok[:-1] if tok.endswith("s") and len(tok) > 4 else tok
            expanded_weights[stem] = max(expanded_weights.get(stem, 0), 5)
            for syn in _SEMANTIC_CONCEPT_SYNONYMS.get(tok, []) + _SEMANTIC_CONCEPT_SYNONYMS.get(stem, []):
                expanded_weights[syn] = max(expanded_weights.get(syn, 0), 3)

        stmt = select(Product).options(joinedload(Product.category))
        if min_price is not None:
            stmt = stmt.where(Product.price >= min_price)
        if max_price is not None:
            stmt = stmt.where(Product.price <= max_price)
        if category_id is not None:
            stmt = stmt.where(Product.category_id == category_id)

        result = await self.session.execute(stmt)
        all_products = list(result.scalars().all())

        scored: list[tuple[int, Product]] = []
        for p in all_products:
            name_low = (p.name or "").lower()
            desc_low = (p.description or "").lower()
            cat_low = (p.category.name if getattr(p, "category", None) else "").lower()
            score = 0
            for term, weight in expanded_weights.items():
                if term in name_low:
                    score += weight * 3
                if term in cat_low:
                    score += weight * 2
                if term in desc_low:
                    score += weight * 1
            if score > 0:
                scored.append((score, p))

        scored.sort(key=lambda item: (item[0], item[1].stock_quantity or 0), reverse=True)
        matched = [p for _, p in scored]
        if not matched:
            return all_products[offset : offset + limit]
        return matched[offset : offset + limit]
    
    async def create(self , **kwargs) -> Product:
        product = Product(**kwargs)
        self.session.add(product)
        await self.session.commit()
        await self.session.refresh(product , attribute_names=["category"])
        return product
    
    async def update(self, product: Product, expected_version: int, **kwargs) -> Product:
        """Atomically update a product using row locking + an optimistic version check.

        Locking the row before comparing the version serialises concurrent writers,
        which is what makes the version check meaningful.
        """
        stmt = (
            select(Product)
            .where(Product.id == product.id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        result = await self.session.execute(stmt)
        locked = result.scalar_one_or_none()

        if locked is None:
            raise ConflictError("Product no longer exists")

        if locked.version != expected_version:
            raise ConflictError("Product has been modified by another transaction")

        for key, value in kwargs.items():
            if value is not None:
                setattr(locked, key, value)

        locked.version += 1
        await self.session.commit()
        await self.session.refresh(locked, attribute_names=["category"])
        return locked

    async def delete(self , product: Product) -> None:
        try:
            await self.session.delete(product)
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise ConflictError(
                "Cannot delete product: it is still referenced by a cart or order"
            )
            
    async def semantic_search(
        self,
        embedding: list[float],
        limit: int = 10,
        offset: int = 0,
        min_price=None,
        max_price=None,
        category_id: uuid.UUID | None = None,
    ) -> list[Product]:
        stmt = (
            select(Product)
            .options(joinedload(Product.category))
            .where(Product.embedding.is_not(None))
        )
        if min_price is not None:
            stmt = stmt.where(Product.price >= min_price)
        if max_price is not None:
            stmt = stmt.where(Product.price <= max_price)
        if category_id is not None:
            stmt = stmt.where(Product.category_id == category_id)
        stmt = (
            stmt.order_by(Product.embedding.cosine_distance(embedding))
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
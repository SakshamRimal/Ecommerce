import asyncio
from sqlalchemy import select 
from sqlalchemy.orm import joinedload

from app.db.session import AsyncSessionFactory
from app.models.product import Product
from app.jobs.tasks import generate_product_embedding_task

async def backfill():
    async with AsyncSessionFactory() as session:
        stmt = select(Product).where(Product.embedding.is_(None))
        result = await session.execute(stmt)
        products = result.scalars().all()
        
        print(f"Backfilling embeddings for {len(products)} products...")
        for product in products:
            await generate_product_embedding_task(ctx={}, product_id=str(product.id))
        print("Backfill complete.")
        
if __name__ == "__main__":
    asyncio.run(backfill())
    
    
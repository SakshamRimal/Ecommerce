import asyncio
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.db.session import AsyncSessionFactory
from app.models.product import Product
from app.jobs.tasks import index_product_task


async def backfill():
    async with AsyncSessionFactory() as session:
        stmt = select(Product).options(joinedload(Product.category))
        result = await session.execute(stmt)
        products = result.scalars().all()

        print(f"Backfilling {len(products)} products into Elasticsearch...")
        for product in products:
            await index_product_task(ctx={}, product_id=str(product.id))
        print("Backfill complete.")


if __name__ == "__main__":
    asyncio.run(backfill())
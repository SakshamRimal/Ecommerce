"""Command-line entry point.

Installed via ``[project.scripts] ecommerce = "app.cli:main"``.

Usage::

    uv run ecommerce create-admin --email admin@example.com --password secret123
    uv run ecommerce create-admin --email admin@example.com --password secret123 \
        --full-name "Store Admin" --promote-existing
    uv run ecommerce seed-catalog
"""

import argparse
import asyncio
from decimal import Decimal
import sys

from sqlalchemy import select

from app.core.cache import cache_delete_pattern, close_redis_pool
from app.core.security import hash_password_async
from app.db.session import AsyncSessionFactory, engine
from app.models.category import Category
from app.models.product import Product
from app.models.user import User, UserRole

SEED_CATALOG = [
    {
        "category": ("Running Shoes", "running-shoes"),
        "products": [
            {
                "name": "Nike Air Max",
                "description": "Responsive cushioned running shoes engineered for daily road training and marathon comfort.",
                "price": Decimal("119.99"),
                "stock_quantity": 42,
                "image_url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=900&q=80",
            },
            {
                "name": "Apex GTX Alpine Trail Runner",
                "description": "Waterproof GORE-TEX membrane with Vibram Megagrip lugs for technical mountain trails.",
                "price": Decimal("168.50"),
                "stock_quantity": 18,
                "image_url": "https://images.unsplash.com/photo-1608231387042-66d1773070a5?auto=format&fit=crop&w=900&q=80",
            },
            {
                "name": "Velocity Carbon Marathon Racer",
                "description": "Full-length carbon fiber propulsion plate paired with nitrogen-infused supercritical foam for race-day PRs.",
                "price": Decimal("249.00"),
                "stock_quantity": 15,
                "image_url": "https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?auto=format&fit=crop&w=900&q=80",
            },
            {
                "name": "CloudStride Recovery Knit Trainer",
                "description": "Ultra-plush dual-density midsole and breathable engineered mesh upper for effortless everyday miles.",
                "price": Decimal("138.00"),
                "stock_quantity": 31,
                "image_url": "https://images.unsplash.com/photo-1460353581641-37baddab0fa2?auto=format&fit=crop&w=900&q=80",
            },
        ],
    },
    {
        "category": ("Audio & Studio", "audio-studio"),
        "products": [
            {
                "name": "Aether ANC Studio Wireless Headphones",
                "description": "Custom 45mm beryllium drivers, adaptive hybrid active noise cancellation, and 48-hour battery life.",
                "price": Decimal("349.00"),
                "stock_quantity": 14,
                "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=900&q=80",
            },
            {
                "name": "Sonos Era Reference Bookshelf Monitors",
                "description": "Compact nearfield studio monitors with ribbon tweeters and lossless USB-C DAC input.",
                "price": Decimal("279.00"),
                "stock_quantity": 9,
                "image_url": "https://images.unsplash.com/photo-1545454675-3531b543be5d?auto=format&fit=crop&w=900&q=80",
            },
            {
                "name": "Pulse Pro True Wireless Earbuds",
                "description": "Spatial audio head tracking, multipoint Bluetooth 5.4, and IPX5 sweat resistance in a pocketable aluminum case.",
                "price": Decimal("189.00"),
                "stock_quantity": 27,
                "image_url": "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?auto=format&fit=crop&w=900&q=80",
            },
            {
                "name": "Vox Broadcast XLR/USB Condenser Microphone",
                "description": "Cardioid studio capsule with built-in DSP preamp, zero-latency headphone monitoring, and weighted desktop boom.",
                "price": Decimal("159.00"),
                "stock_quantity": 19,
                "image_url": "https://images.unsplash.com/photo-1590602847861-f357a9332bbc?auto=format&fit=crop&w=900&q=80",
            },
        ],
    },
    {
        "category": ("Workspace & Keyboards", "workspace-keyboards"),
        "products": [
            {
                "name": "Chronos 75% CNC Aluminum Mechanical Keyboard",
                "description": "Gasket-mounted 6063 anodized aluminum chassis with hot-swappable tactile switches and PBT keycaps.",
                "price": Decimal("219.00"),
                "stock_quantity": 11,
                "image_url": "https://images.unsplash.com/photo-1511467687858-23d96c32e4ae?auto=format&fit=crop&w=900&q=80",
            },
            {
                "name": "Lumen Architect Cantilever Desk Lamp",
                "description": "CRI 97+ tunable LED task bar with wireless Qi charging base and stepless rotary dimmer.",
                "price": Decimal("145.00"),
                "stock_quantity": 23,
                "image_url": "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?auto=format&fit=crop&w=900&q=80",
            },
            {
                "name": "Vector Pro 8K Wireless Ergonomic Mouse",
                "description": "54g magnesium-alloy shell with 30,000 DPI optical sensor, optical microswitches, and USB-C rapid charging.",
                "price": Decimal("129.00"),
                "stock_quantity": 24,
                "image_url": "https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?auto=format&fit=crop&w=900&q=80",
            },
            {
                "name": "Nordic Merino Felt & Walnut Desk Shelf",
                "description": "Solid American black walnut monitor riser with integrated MagSafe tray and wool felt desk mat.",
                "price": Decimal("175.00"),
                "stock_quantity": 14,
                "image_url": "https://images.unsplash.com/photo-1593642632823-8f785ba67e45?auto=format&fit=crop&w=900&q=80",
            },
        ],
    },
    {
        "category": ("Everyday Carry", "everyday-carry"),
        "products": [
            {
                "name": "Nomad 24L Weatherproof Commuter Pack",
                "description": "Cordura Ballistic nylon backpack with suspended 16-inch laptop vault and magnetic fidlock hardware.",
                "price": Decimal("195.00"),
                "stock_quantity": 16,
                "image_url": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=900&q=80",
            },
            {
                "name": "Horology Field Automatic Titanium Watch",
                "description": "Grade-5 brushed titanium case, sapphire crystal, Japanese automatic movement, and 100m water resistance.",
                "price": Decimal("299.00"),
                "stock_quantity": 7,
                "image_url": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=900&q=80",
            },
            {
                "name": "volt 140W GaN Travel Power Bank 24000mAh",
                "description": "Airline-safe high-output USB-C PD 3.1 battery pack with real-time OLED wattage telemetry.",
                "price": Decimal("115.00"),
                "stock_quantity": 29,
                "image_url": "https://images.unsplash.com/photo-1609091839311-d5365f9ff1c5?auto=format&fit=crop&w=900&q=80",
            },
            {
                "name": "Obsidian Polarized Acetate Sunglasses",
                "description": "Hand-polished Italian Mazzucchelli acetate frames with anti-reflective Carl Zeiss polarized lenses.",
                "price": Decimal("149.00"),
                "stock_quantity": 21,
                "image_url": "https://images.unsplash.com/photo-1511499767150-a48a237f0083?auto=format&fit=crop&w=900&q=80",
            },
        ],
    },
    {
        "category": ("Specialty Coffee", "specialty-coffee"),
        "products": [
            {
                "name": "Fellowship Precision Conical Burr Grinder",
                "description": "64mm flat titanium-coated burrs with 41 stepless grind settings for espresso and pour-over.",
                "price": Decimal("225.00"),
                "stock_quantity": 12,
                "image_url": "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?auto=format&fit=crop&w=900&q=80",
            },
            {
                "name": "Artisan PID Gooseneck Pour-Over Kettle",
                "description": "Degree-accurate PID temperature control with counterbalanced precision spout and 60-minute hold mode.",
                "price": Decimal("165.00"),
                "stock_quantity": 20,
                "image_url": "https://images.unsplash.com/photo-1544787219-7f47ccb76574?auto=format&fit=crop&w=900&q=80",
            },
            {
                "name": "Copper Vacuum Insulated Tasting Carafe",
                "description": "Double-wall borosilicate glass and brushed copper server engineered to preserve single-origin aromatics.",
                "price": Decimal("78.00"),
                "stock_quantity": 34,
                "image_url": "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?auto=format&fit=crop&w=900&q=80",
            },
            {
                "name": "Barista Pro 0.1g Espresso Flow Scale",
                "description": "Water-resistant rechargeable scale with automatic shot timer and real-time flow-rate graph.",
                "price": Decimal("89.00"),
                "stock_quantity": 17,
                "image_url": "https://images.unsplash.com/photo-1517701550927-30cf4ba1dba5?auto=format&fit=crop&w=900&q=80",
            },
        ],
    },
    {
        "category": ("Smart Home & Cameras", "smart-home-cameras"),
        "products": [
            {
                "name": "Leica-Style Compact 4K Rangefinder Camera",
                "description": "APS-C CMOS sensor with fast f/2.0 prime lens, hybrid optical viewfinder, and film-simulation dials.",
                "price": Decimal("899.00"),
                "stock_quantity": 5,
                "image_url": "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?auto=format&fit=crop&w=900&q=80",
            },
            {
                "name": "Halo Matter Smart Ambient Light Bar",
                "description": "16-million color RGBIC bias lighting with Matter-over-Thread support and circadian rhythm automation.",
                "price": Decimal("95.00"),
                "stock_quantity": 26,
                "image_url": "https://images.unsplash.com/photo-1513506003901-1e6a229e2d15?auto=format&fit=crop&w=900&q=80",
            },
            {
                "name": "Atmos HEPA 14 Smart Air Purifier",
                "description": "Whisper-quiet 22dB brushless motor with laser PM2.5 air quality display and activated carbon filter.",
                "price": Decimal("259.00"),
                "stock_quantity": 13,
                "image_url": "https://images.unsplash.com/photo-1585771724684-38269d6639fd?auto=format&fit=crop&w=900&q=80",
            },
            {
                "name": "Zenith Portable 1080p Laser Cinema Projector",
                "description": "Auto-keystone laser projection up to 120 inches with dual Harman Kardon speakers and Wi-Fi 6 casting.",
                "price": Decimal("449.00"),
                "stock_quantity": 8,
                "image_url": "https://images.unsplash.com/photo-1478720568477-152d9b164e26?auto=format&fit=crop&w=900&q=80",
            },
        ],
    },
]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ecommerce")
    subparsers = parser.add_subparsers(dest="command", required=True)

    admin = subparsers.add_parser(
        "create-admin", help="Create an administrator account"
    )
    admin.add_argument("--email", required=True)
    admin.add_argument("--password", required=True)
    admin.add_argument("--full-name", default="Administrator")
    admin.add_argument(
        "--promote-existing",
        action="store_true",
        help="If the email already exists, promote it to admin and reset its password",
    )

    subparsers.add_parser(
        "seed-catalog",
        help="Idempotently seed categories and curated products into PostgreSQL",
    )
    return parser


async def _create_admin(args: argparse.Namespace) -> int:
    email = args.email.strip().lower()

    if len(args.password) < 8:
        print("error: password must be at least 8 characters", file=sys.stderr)
        return 2

    async with AsyncSessionFactory() as session:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if user is not None:
            if not args.promote_existing:
                print(
                    f"error: user '{email}' already exists "
                    "(pass --promote-existing to promote it)",
                    file=sys.stderr,
                )
                return 1
            user.role = UserRole.ADMIN
            user.is_active = True
            user.hashed_password = await hash_password_async(args.password)
            await session.commit()
            print(f"promoted existing user '{email}' to admin")
            return 0

        user = User(
            email=email,
            hashed_password=await hash_password_async(args.password),
            full_name=args.full_name,
            is_active=True,
            role=UserRole.ADMIN,
        )
        session.add(user)
        await session.commit()
        print(f"created admin user '{email}'")
        return 0


FALLBACK_CATEGORY_IMAGES: dict[str, list[str]] = {
    "clothing": [
        "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1556821840-3a63f95609a7?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1591047139829-d91aecb6caea?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1542272604-787c3835535d?auto=format&fit=crop&w=900&q=80",
    ],
    "books": [
        "https://images.unsplash.com/photo-1544947950-fa07a98d237f?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1512820790803-83ca734da794?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1495446815901-a7297e633e8d?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1524578271613-d550eacf6090?auto=format&fit=crop&w=900&q=80",
    ],
    "home-kitchen": [
        "https://images.unsplash.com/photo-1556911220-e15b29be8c8f?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1584990347449-a2d4c2c044c9?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?auto=format&fit=crop&w=900&q=80",
    ],
    "sports-outdoors": [
        "https://images.unsplash.com/photo-1517836357463-d25dfeac3438?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1526506118085-60ce8714f8c5?auto=format&fit=crop&w=900&q=80",
    ],
    "beauty-personal-care": [
        "https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1556228720-195a672e8a03?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1571781926291-c477ebfd024b?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1608248597359-0e6d526a6828?auto=format&fit=crop&w=900&q=80",
    ],
    "toys-games": [
        "https://images.unsplash.com/photo-1511512578047-dfb367046420?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1587654780291-39c9404d746b?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1610890716171-6b1bb98ffd09?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1596461404969-9ae70f2830c1?auto=format&fit=crop&w=900&q=80",
    ],
    "food-beverages": [
        "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1544787219-7f47ccb76574?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1511381939415-e44015466834?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?auto=format&fit=crop&w=900&q=80",
    ],
    "electronics": [
        "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1511467687858-23d96c32e4ae?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?auto=format&fit=crop&w=900&q=80",
    ],
}


async def _seed_catalog() -> int:
    added_categories = 0
    added_products = 0
    updated_products = 0

    async with AsyncSessionFactory() as session:
        for group in SEED_CATALOG:
            cat_name, cat_slug = group["category"]
            cat = (
                await session.execute(
                    select(Category).where(Category.slug == cat_slug)
                )
            ).scalar_one_or_none()

            if cat is None:
                cat = Category(name=cat_name, slug=cat_slug)
                session.add(cat)
                await session.flush()
                added_categories += 1

            for item in group["products"]:
                existing = (
                    await session.execute(
                        select(Product).where(Product.name == item["name"])
                    )
                ).scalar_one_or_none()

                if existing is None:
                    session.add(
                        Product(
                            name=item["name"],
                            description=item["description"],
                            price=item["price"],
                            stock_quantity=item["stock_quantity"],
                            image_url=item["image_url"],
                            category_id=cat.id,
                        )
                    )
                    added_products += 1
                elif not existing.image_url:
                    existing.image_url = item["image_url"]
                    existing.description = item["description"]
                    updated_products += 1

        # Ensure every category in the database has at least 2 products
        all_categories = (await session.execute(select(Category))).scalars().all()
        default_pool = FALLBACK_CATEGORY_IMAGES["electronics"]
        for cat_obj in all_categories:
            cat_products = (
                await session.execute(
                    select(Product).where(Product.category_id == cat_obj.id)
                )
            ).scalars().all()
            pool = FALLBACK_CATEGORY_IMAGES.get(cat_obj.slug, default_pool)
            needed = max(0, 2 - len(cat_products))
            for idx in range(needed):
                tier = "Pro Edition" if idx == 0 else "Studio Series"
                candidate_name = f"{cat_obj.name} {tier}"
                session.add(
                    Product(
                        name=candidate_name,
                        description=f"Premium {cat_obj.name.lower()} engineered for durability, comfort, and daily performance.",
                        price=Decimal("149.00") if idx == 0 else Decimal("199.00"),
                        stock_quantity=18 + idx * 5,
                        image_url=pool[idx % len(pool)],
                        category_id=cat_obj.id,
                    )
                )
                added_products += 1

        # Backfill image_url for any existing products missing images
        cats_by_id = {c.id: c.slug for c in all_categories}
        missing_img_products = (
            await session.execute(
                select(Product).where(Product.image_url.is_(None))
            )
        ).scalars().all()
        for idx, prod in enumerate(missing_img_products):
            slug = cats_by_id.get(prod.category_id, "")
            pool = FALLBACK_CATEGORY_IMAGES.get(slug, default_pool)
            prod.image_url = pool[idx % len(pool)]
            updated_products += 1

        await session.commit()

    await cache_delete_pattern("product:list:*")
    await cache_delete_pattern("products:list:*")
    await close_redis_pool()
    print(
        f"catalog seeded: +{added_categories} categories, "
        f"+{added_products} new products, {updated_products} updated"
    )
    return 0


async def _run(args: argparse.Namespace) -> int:
    try:
        if args.command == "create-admin":
            return await _create_admin(args)
        if args.command == "seed-catalog":
            return await _seed_catalog()
        print(f"error: unknown command '{args.command}'", file=sys.stderr)
        return 2
    finally:
        await engine.dispose()


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    return asyncio.run(_run(args))


if __name__ == "__main__":
    raise SystemExit(main())

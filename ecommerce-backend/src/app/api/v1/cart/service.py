import uuid
from decimal import Decimal
from sqlalchemy.exc import IntegrityError

from app.api.v1.cart.repository import CartRepository
from app.api.v1.cart.schema import CartItemRequest, CartResponse, CartItemResponse
from app.core.exceptions import NotFoundError, ConflictError


class CartService:
    def __init__(self, repository: CartRepository):
        self.repository = repository

    async def get_cart(self, user_id: uuid.UUID) -> CartResponse:
        cart = await self.repository.get_or_create_cart(user_id)
        return self._build_response(cart)

    async def add_item(
        self, user_id: uuid.UUID, data: CartItemRequest
    ) -> CartResponse:
        cart = await self.repository.get_or_create_cart(user_id)

        product = await self.repository.get_product(data.product_id)
        if not product:
            raise NotFoundError(f"Product '{data.product_id}' not found")

        if product.stock_quantity < data.quantity:
            raise ConflictError(
                f"Insufficient stock for '{product.name}' "
                f"(requested {data.quantity}, available {product.stock_quantity})"
            )

        existing_item = await self.repository.get_cart_item(
            cart.id, data.product_id
        )
        if existing_item:
            new_qty = existing_item.quantity + data.quantity
            if product.stock_quantity < new_qty:
                raise ConflictError(
                    f"Insufficient stock for '{product.name}' "
                    f"(cart has {existing_item.quantity}, adding {data.quantity}, "
                    f"available {product.stock_quantity})"
                )
            await self.repository.update_item_quantity(existing_item, new_qty)
        else:
            try:
                await self.repository.add_item(cart.id, data.product_id, data.quantity)
            except IntegrityError:
                # Concurrent add_item inserted the same (cart_id, product_id) row first.
                rollback = getattr(self.repository.session, "rollback", None)
                if callable(rollback):
                    res = rollback()
                    if hasattr(res, "__await__"):
                        await res
                existing_item = await self.repository.get_cart_item(
                    cart.id, data.product_id
                )
                if existing_item is None:
                    raise
                new_qty = existing_item.quantity + data.quantity
                if product.stock_quantity < new_qty:
                    raise ConflictError(
                        f"Insufficient stock for '{product.name}' "
                        f"(cart has {existing_item.quantity}, adding {data.quantity}, "
                        f"available {product.stock_quantity})"
                    )
                await self.repository.update_item_quantity(existing_item, new_qty)

        # Expire cached cart so re-fetch gets fresh data from DB
        self.repository.session.expire(cart)
        cart = await self.repository.get_cart(user_id)
        return self._build_response(cart)

    async def update_item_quantity(
        self, user_id: uuid.UUID, product_id: uuid.UUID, quantity: int
    ) -> CartResponse:
        cart = await self.repository.get_or_create_cart(user_id)

        item = await self.repository.get_cart_item(cart.id, product_id)
        if not item:
            raise NotFoundError("Item not in cart")

        if quantity <= 0:
            await self.repository.remove_item(item)
        else:
            product = await self.repository.get_product(product_id)
            if product and product.stock_quantity < quantity:
                raise ConflictError(
                    f"Insufficient stock for '{product.name}' "
                    f"(requested {quantity}, available {product.stock_quantity})"
                )
            await self.repository.update_item_quantity(item, quantity)

        self.repository.session.expire(cart)
        cart = await self.repository.get_cart(user_id)
        return self._build_response(cart)

    async def remove_item(
        self, user_id: uuid.UUID, product_id: uuid.UUID
    ) -> CartResponse:
        cart = await self.repository.get_or_create_cart(user_id)

        item = await self.repository.get_cart_item(cart.id, product_id)
        if not item:
            raise NotFoundError("Item not in cart")

        await self.repository.remove_item(item)

        self.repository.session.expire(cart)
        cart = await self.repository.get_cart(user_id)
        return self._build_response(cart)

    async def clear_cart(self, user_id: uuid.UUID) -> CartResponse:
        cart = await self.repository.get_or_create_cart(user_id)
        await self.repository.clear_cart(cart.id)

        self.repository.session.expire(cart)
        cart = await self.repository.get_cart(user_id)
        return self._build_response(cart)

    def _build_response(self, cart) -> CartResponse:
        items = []
        total = Decimal("0")
        for ci in cart.items:
            subtotal = Decimal(str(ci.product.price)) * ci.quantity
            total += subtotal
            items.append(
                CartItemResponse(
                    id=ci.id,
                    product_id=ci.product_id,
                    product_name=ci.product.name,
                    unit_price=Decimal(str(ci.product.price)),
                    quantity=ci.quantity,
                    subtotal=subtotal,
                )
            )
        return CartResponse(id=cart.id, items=items, total=total)

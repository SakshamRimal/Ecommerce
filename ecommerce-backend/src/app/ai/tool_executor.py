import json
import uuid

import structlog

from app.api.v1.search.service import SearchService
from app.api.v1.products.repository import ProductRepository

logger = structlog.get_logger("tool_executor")


def _parse_uuid(value) -> uuid.UUID | None:
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError, AttributeError):
        return None


def _optional_float(value) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


class ToolExecutor:
    def __init__(self, search_service: SearchService, product_repository: ProductRepository):
        self.search_service = search_service
        self.product_repository = product_repository

    async def execute(self, tool_name: str, arguments: dict) -> str:
        """Dispatch a GPT tool call to backend logic, returning a JSON string.

        Every branch is defensive: malformed arguments or tool failures are
        returned as ``{"error": ...}`` so one bad tool call cannot abort the
        whole chat turn.
        """
        arguments = arguments if isinstance(arguments, dict) else {}

        try:
            return await self._dispatch(tool_name, arguments)
        except Exception as exc:  # noqa: BLE001 - tool errors must not break chat
            logger.warning(
                "tool_execution_failed", tool=tool_name, error=str(exc)
            )
            return json.dumps({"error": f"Tool '{tool_name}' failed: {exc}"})

    async def _dispatch(self, tool_name: str, arguments: dict) -> str:
        if tool_name == "search_products":
            query = arguments.get("query")
            if not isinstance(query, str) or not query.strip():
                return json.dumps({"error": "A non-empty 'query' is required"})

            result = await self.search_service.search_products(
                query=query,
                limit=5,
                min_price=_optional_float(arguments.get("min_price")),
                max_price=_optional_float(arguments.get("max_price")),
                category_id=_parse_uuid(arguments.get("category_id")),
            )
            return json.dumps({
                "currency": "NRs",
                "results": [
                    {
                        "id": str(r.id),
                        "name": r.name,
                        "price": f"NRs {r.price}",
                        "stock": r.stock_quantity,
                        "category": r.category_name,
                    }
                    for r in result.results
                ],
                "total": result.total,
            })

        elif tool_name == "get_product_details":
            product_id = _parse_uuid(arguments.get("product_id"))
            if product_id is None:
                return json.dumps({"error": "Invalid or missing 'product_id'"})

            product = await self.product_repository.get_by_id(product_id)
            if not product:
                return json.dumps({"error": "Product not found"})
            return json.dumps({
                "id": str(product.id),
                "name": product.name,
                "currency": "NRs",
                "price": f"NRs {product.price}",
                "stock": product.stock_quantity,
                "description": product.description,
                "category": product.category.name if product.category else None,
            })

        elif tool_name == "check_stock":
            product_id = _parse_uuid(arguments.get("product_id"))
            if product_id is None:
                return json.dumps({"error": "Invalid or missing 'product_id'"})

            product = await self.product_repository.get_by_id(product_id)
            if not product:
                return json.dumps({"error": "Product not found"})
            return json.dumps({
                "product_id": str(product.id),
                "stock_quantity": product.stock_quantity,
            })

        elif tool_name == "semantic_search_products":
            query = arguments.get("query")
            if not isinstance(query, str) or not query.strip():
                return json.dumps({"error": "A non-empty 'query' is required"})

            results = await self.search_service.semantic_search_products(
                query=query,
                limit=5,
                min_price=_optional_float(arguments.get("min_price")),
                max_price=_optional_float(arguments.get("max_price")),
                category_id=_parse_uuid(arguments.get("category_id")),
            )
            return json.dumps({
                "results": [
                    {
                        "id": str(r.id),
                        "name": r.name,
                        "price": str(r.price),
                        "stock": r.stock_quantity,
                    }
                    for r in results
                ]
            })

        return json.dumps({"error": f"Unknown tool: {tool_name}"})

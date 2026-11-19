from decimal import Decimal
import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from app.ai.tool_executor import ToolExecutor
from app.ai.tools import TOOL_DEFINITIONS
from app.api.v1.chat.service import ChatService
from app.api.v1.search.schema import ProductSearchResult, SearchResponse
from app.api.v1.search.service import SearchService
from app.cli import _build_parser, _create_admin
from app.models.category import Category
from app.models.product import Product


class TestToolDefinitionsAndExecutor:
    def test_all_tool_definitions_have_parameters_key(self):
        for tool in TOOL_DEFINITIONS:
            fn = tool["function"]
            assert "parameters" in fn, f"Missing 'parameters' in {fn['name']}"
            assert "paramters" not in fn

    async def test_executor_handles_malformed_uuid_gracefully(self):
        executor = ToolExecutor(AsyncMock(), AsyncMock())
        raw = await executor.execute(
            "get_product_details", {"product_id": "not-a-uuid"}
        )
        payload = json.loads(raw)
        assert "error" in payload

    async def test_executor_search_and_stock(self):
        pid = uuid.uuid4()
        search_service = AsyncMock()
        search_service.search_products = AsyncMock(
            return_value=SearchResponse(
                query="shoe",
                total=1,
                results=[
                    ProductSearchResult(
                        id=pid,
                        name="Trail Shoe",
                        description="Fast",
                        category_name="Footwear",
                        price=Decimal("99.00"),
                        stock_quantity=4,
                        score=2.5,
                    )
                ],
            )
        )
        product_repo = AsyncMock()
        product_repo.get_by_id = AsyncMock(
            return_value=Product(
                id=pid,
                name="Trail Shoe",
                description="Fast",
                price=Decimal("99.00"),
                stock_quantity=4,
                category_id=uuid.uuid4(),
            )
        )

        executor = ToolExecutor(search_service, product_repo)
        search_json = json.loads(
            await executor.execute(
                "search_products",
                {"query": "shoe", "min_price": 50, "max_price": 120},
            )
        )
        assert search_json["total"] == 1
        assert search_json["results"][0]["name"] == "Trail Shoe"

        stock_json = json.loads(
            await executor.execute("check_stock", {"product_id": str(pid)})
        )
        assert stock_json["stock_quantity"] == 4


class TestSearchServiceFallback:
    async def test_falls_back_to_postgres_when_es_fails(self):
        cat = Category(id=uuid.uuid4(), name="Gear", slug="gear")
        prod = Product(
            id=uuid.uuid4(),
            name="Rain Jacket",
            description="Waterproof",
            price=Decimal("120.00"),
            stock_quantity=7,
            category_id=cat.id,
            category=cat,
        )
        repo = AsyncMock()
        repo.search_by_keyword = AsyncMock(return_value=[prod])

        bad_es = AsyncMock()
        bad_es.search = AsyncMock(side_effect=ConnectionError("ES unreachable"))

        with patch(
            "app.api.v1.search.service.get_es_client", return_value=bad_es
        ):
            service = SearchService(repo)
            res = await service.search_products(query="rain", limit=10, offset=0)

        assert res.total == 1
        assert res.results[0].name == "Rain Jacket"
        repo.search_by_keyword.assert_awaited_once()


class TestChatService:
    async def test_send_message_persists_exchange_and_caps_tool_loop(self):
        repo = AsyncMock()
        repo.get_recent_messages = AsyncMock(return_value=[])
        repo.add_exchange = AsyncMock()

        executor = AsyncMock()
        executor.execute = AsyncMock(return_value='{"results": [], "total": 0}')

        service = ChatService(repo, executor)

        tool_call = MagicMock()
        tool_call.id = "call_1"
        tool_call.function.name = "search_products"
        tool_call.function.arguments = '{"query": "boots"}'

        tool_choice = MagicMock()
        tool_choice.finish_reason = "tool_calls"
        tool_choice.message.tool_calls = [tool_call]
        tool_choice.message.model_dump.return_value = {
            "role": "assistant",
            "tool_calls": [],
        }

        final_choice = MagicMock()
        final_choice.finish_reason = "stop"
        final_choice.message.content = "We have hiking boots in stock!"

        resp1 = MagicMock(choices=[tool_choice])
        resp2 = MagicMock(choices=[final_choice])
        service._complete = AsyncMock(side_effect=[resp1, resp2])

        session_id = uuid.uuid4()
        reply = await service.send_message(session_id, "Do you have boots?")

        assert reply == "We have hiking boots in stock!"
        executor.execute.assert_awaited_once_with(
            "search_products", {"query": "boots"}
        )
        repo.add_exchange.assert_awaited_once_with(
            session_id, "Do you have boots?", "We have hiking boots in stock!"
        )


class TestAdminCli:
    async def test_cli_rejects_short_password(self):
        parser = _build_parser()
        args = parser.parse_args(
            ["create-admin", "--email", "admin@example.com", "--password", "short"]
        )
        rc = await _create_admin(args)
        assert rc == 2

    async def test_cli_creates_admin(self, mock_session):
        parser = _build_parser()
        args = parser.parse_args(
            [
                "create-admin",
                "--email",
                "Admin@Example.com",
                "--password",
                "strongpass123",
                "--full-name",
                "Site Admin",
            ]
        )

        ctx = AsyncMock()
        ctx.__aenter__.return_value = mock_session
        ctx.__aexit__.return_value = False

        with patch("app.cli.AsyncSessionFactory", return_value=ctx):
            rc = await _create_admin(args)

        assert rc == 0
        mock_session.add.assert_called_once()
        mock_session.commit.assert_awaited_once()


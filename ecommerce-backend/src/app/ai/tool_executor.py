import json 
import uuid 
from app.api.v1.search.service import SearchService
from app.api.v1.products.repository import ProductRepository

class ToolExecutor:
    def __init__(self , search_service: SearchService , product_repository: ProductRepository):
        self.search_service = search_service 
        self.product_repository = product_repository
        
    async def execute(self , tool_name: str , arguments: dict) -> str:
        """Dispatch a GPT tool call to the real backend logic , return a JSON string with the result."""
        if tool_name == "search_products":
            result = await self.search_service.search_products(
                query=arguments["query"] ,limit=5
            )
            filtered = [
                r for r in result.results
                if arguments.get("min_price") is None or r.price >= arguments["min_price"]
            ]
            return json.dumps({
                "results": [
                    {"id": str(r.id), "name": r.name, "price": str(r.price), "stock": r.stock_quantity}
                    for r in filtered
                ]
            })
            
        elif tool_name == "get_product_details":
            product = await self.product_repository.get_by_id(uuid.UUID(arguments["product_id"]))
            if not product:
                return json.dumps({"error": "Product not found"})
            return json.dumps({
                "id": str(product.id), "name": product.name, "price": str(product.price), "stock": product.stock_quantity, "description": product.description , "stock":product.stock_quantity , 
                "category": product.category.name
            })
            
        elif tool_name == "check_stock":
            product = await self.product_repository.get_by_id(uuid.UUID(arguments["product_id"]))
            if not product:
                return json.dumps({"error": "Product not found"})
            return json.dumps({"product_id": str(product.id), "stock_quantity": product.stock_quantity})
        
        return json.dumps({"error": f"Unknown tool: {tool_name}"})
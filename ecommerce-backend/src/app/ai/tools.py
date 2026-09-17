TOOL_DEFINATIONS = [
    {
        "type":"function",
        "function":{
            "name":"search_products",
            "description":"Search the product catalog by keywordd , with optional price filtering. Use this whenever the user descibes what they are looking for ",
            "parameters": {
                "type":"object",
                "properties":{
                    "query":{
                        "type":"string",
                        "description":"The search query or keywords to look for in the product catalog"
                    },
                    "min_price":{
                        "type":"number",
                        "description":"Optional minimum price filter for the search results"
                    },
                    "max_price":{
                        "type":"number",
                        "description":"Optional maximum price filter for the search results"
                    }
                },
                "required":["query"]
            },
            
        },
    },
    {
        "type":"function",
        "function": {
            "name":"get_product_details",
            "description": "Get full details (price, stock, description) for a specific product by its ID. Use this after search_products to give the user more detail on one item.",
            "parameters": {
                "type":"object",
                "properties": {
                    "product_id" : {"type":"string","description":"The unique identifier of the product to retrieve details for"}
                },
                "required":["product_id"]
            },  
        },
    },
    {
        "type":"function",
        "function": {
            "name":"check_stock",
            "description": "Check current stock quantity for a sepcific product.",
            "paramters":{
                "type":"object",
                "properties":{
                    "product_id":{"type":"string","description":"The unique identifier of the product to check stock for"}
                },
                "required":["product_id"],
            },
        },
    },
]
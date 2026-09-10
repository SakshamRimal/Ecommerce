PRODUCT_INDEX_MAPPING = {
    "mappings" : {
        "properties" : {
            "id" : {"type" : "keyword"},
            "name" : {
                "type" : "text",
                "analyzer": "standard",
                "fields": {
                    "raw": {"type": "keyword"}
                },
            },
            "description" : {"type" : "text" , "analyzer": "standard"},
            "category_id" : {"type" : "keyword"},
            "category_name" : {"type":"keyword"},
            "price" : {"type" : "scaled_float" , "scaling_factor": 100},
            "stock_quantity" : {"type" : "integer"},
            "created_at" : {"type" : "date"},
        }
            
    }
}

async def ensure_product_index_exists(es_client) -> None:
    from app.core.config import get_settings
    from app.core.logging import get_logger
    logger = get_logger("search_index")
    settings = get_settings()
    index_name = settings.elasticsearch_products_index

    try:
        exists = await es_client.indices.exists(index=index_name)
        if not exists:
            await es_client.indices.create(index=index_name, body=PRODUCT_INDEX_MAPPING)
            logger.info("elasticsearch_index_created", index=index_name)
        else:
            logger.info("elasticsearch_index_exists", index=index_name)
    except Exception as e:
        logger.warning("elasticsearch_unavailable", error=str(e))
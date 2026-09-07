from elasticsearch import AsyncElasticsearch
from app.core.config import get_settings

settings = get_settings()

_es_client: AsyncElasticsearch | None = None


async def get_es_client() -> AsyncElasticsearch:
    """Retrieves or initializes the global AsyncElasticsearch client."""
    global _es_client
    if _es_client is None:
        _es_client = AsyncElasticsearch(hosts=[settings.elasticsearch_url])
    return _es_client


async def close_es_client() -> None:
    """Closes the global AsyncElasticsearch client connection pool."""
    global _es_client
    if _es_client is not None:
        await _es_client.close()
        _es_client = None

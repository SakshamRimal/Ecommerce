from openai import AsyncOpenAI 
from app.core.config import get_settings

settings = get_settings()
client = AsyncOpenAI(api_key=settings.openai_api_key)                       

async def generate_embedding(text: str) -> list[float]:
    """
    Generate an embedding for the given text using OpenAI's API.

    Args:
        text (str): The input text to generate an embedding for.
    """
    response = await client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

def build_product_embedding_text(name: str , description: str | None , category_name: str) -> str:
    """
    Build a text representation of a product for embedding generation.

    Args:
        name (str): The name of the product.
        description (str): The description of the product.

    Returns:
        str: A concatenated string of the product's name and description.
    """
    parts = [name , category_name]
    if description:
        parts.append(description)
    return "-".join(parts)
    
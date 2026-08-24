from sqlalchemy import text 
from sqlalchemy.ext.asyncio import AsyncSession

class HealthCheckRepository:
    
    def __init__(self , session:AsyncSession):
        self.session = session
        
    async def check_database(self) -> bool:
        result = await self.session.execute(text("SELECT 1"))
        return result.scalar_one() == 1
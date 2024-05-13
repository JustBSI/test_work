from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from src.config import Config

engine = create_async_engine(Config.DATABASE_URL)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class DbRequest:
    def __init__(self):
        self.session = async_session_maker()

    async def execute_query(self, query: Any) -> Any | None:
        result = await self.session.execute(query)
        return result

    async def execute_stmt(self, stmt: Any) -> None:
        await self.session.execute(stmt)
        try:
            await self.session.commit()
        except Exception as e:
            print(e)
            await self.session.rollback()

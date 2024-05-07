from typing import AsyncGenerator, Any

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from src.config import DB_HOST, DB_NAME, DB_PASS, DB_PORT, DB_USER

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


engine = create_async_engine(DATABASE_URL)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def __get_async_session() -> AsyncSession:
    async with async_session_maker() as session:
        yield session


async def execute_query(query: Any, session: AsyncSession) -> Any | None:
    result = await session.execute(query)
    return result


async def execute_stmt(stmt: Any, session: AsyncSession) -> None:
    await session.execute(stmt)
    try:
        await session.commit()
    except Exception as e:
        print(e)
        await session.rollback()

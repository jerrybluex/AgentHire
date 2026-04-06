import asyncio
from app.core.database import db_manager
from sqlalchemy import select, func
from app.models import Enterprise

async def test():
    session = db_manager.session_factory()
    try:
        # Simple query
        result = await session.execute(select(Enterprise))
        enterprises = result.scalars().all()
        print(f"Found {len(enterprises)} enterprises")
        for e in enterprises:
            print(f"  - {e.id}: {e.name}")

        # Count query with subquery
        query = select(Enterprise)
        count_result = await session.execute(
            select(func.count()).select_from(query.subquery())
        )
        print(f"Count: {count_result.scalar()}")
    finally:
        await session.close()

asyncio.run(test())

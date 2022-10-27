from typing import List, Union, Optional


from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.elements import or_

from app.libs.postgres.models import Event
from app.settings import get_settings

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine


import datetime as d
from datetime import datetime

settings = get_settings()

connection = f'{settings.postgres_settings.postgres_server}{settings.postgres_settings.postgres_db}'
engine = create_async_engine(connection, echo=True)
async_session = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def get_time_segment_user_events(
    user_id,
    event_beginning: bool,
    before_ts: Optional[datetime] = d.date(2000, 12, 12),
    after_ts: Optional[datetime] = d.date(3000, 12, 12),
    sort_required: bool = False):


    async with async_session() as session:
        stmt = select(Event).where(Event.owner_id == user_id).filter(
            or_(Event.from_datetime <= before_ts, before_ts == None),
            or_(Event.to_datetime >= after_ts, after_ts == None))
        result = await session.execute(stmt)
        events = result.scalars().all()
        return events


async def get_enveloping_user_events(
    user_id,
    begin_ts: Optional[datetime] = d.date(2000, 12, 12),
    end_ts: Optional[datetime] = d.date(3000, 12, 12)
):
    async with async_session() as session:
        stmt = select(Event).where(Event.owner_id == user_id).filter(
                                    or_(Event.from_datetime >= begin_ts, begin_ts == None),
                                    or_(Event.to_datetime <= end_ts, end_ts == None))
        result = await session.execute(stmt)
        events = result.scalars().all()
        return events


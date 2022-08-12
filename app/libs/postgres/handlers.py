from datetime import datetime
from typing import List

from fastapi import HTTPException, status
from pydantic import UUID4

from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.elements import and_

from app.libs.postgres.models import Event
from app.schemas.calendar_schemas import EventsSchema
from app.settings import get_settings

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import update, delete

settings = get_settings()

connection = f'{settings.postgres_settings.postgres_server}{settings.postgres_settings.postgres_db}'
engine = create_async_engine(connection, echo=True)
async_session = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def chek_event_exists_and_owner_rights(event_id: UUID4, owner_id: UUID4) -> Event:
    async with async_session() as session:
        event = await session.get(Event, event_id)
        if event:
            if event.owner_id == owner_id:
                return event
            else:
                raise HTTPException(status.HTTP_403_FORBIDDEN, 'Forbidden')
        else:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail='Event not found')


async def insert_event(event: EventsSchema,
                 owner_id: UUID4):
    async with async_session() as session:

        new_event = Event(id=event.id,
                          title=event.title,
                          description=event.description,
                          from_datetime=event.from_datetime.replace(tzinfo=None),
                          to_datetime=event.to_datetime.replace(tzinfo=None),
                          location=event.location,
                          is_online_event=event.is_online_event,
                          photo_uri=event.photo_uri,
                          repeat_mode=event.repeat_mode.value,
                          repeat_days=event.repeat_days,
                          repeat_end=event.repeat_end,
                          source=event.source,
                          owner_id=owner_id,
                          )
        async with session.begin():
            session.add(new_event)
        await session.commit()



async def get_event(event_id: UUID4, user_id: UUID4) -> Event:
    event = await chek_event_exists_and_owner_rights(event_id=event_id, owner_id=user_id)
    return event

async def get_events(owner_id) -> List[Event]:
    async with async_session() as session:
        stmt = select(Event).where(Event.owner_id==owner_id)
        result = await session.execute(stmt)
        events = result.scalars().all()
        return events


async def update_event(event_id: UUID4, event: EventsSchema, owner_id: UUID4):
    async with async_session() as session:
        await chek_event_exists_and_owner_rights(event_id=event_id, owner_id=owner_id)
        stmt = update(Event).where(Event.id == event_id, Event.owner_id == owner_id).values(title=event.title,
                              description=event.description,
                              from_datetime=event.from_datetime.replace(tzinfo=None),
                              edited_at=datetime.now(),
                              to_datetime=event.to_datetime.replace(tzinfo=None),
                              location=event.location,
                              is_online_event=event.is_online_event,
                              photo_uri=event.photo_uri,
                              repeat_mode=event.repeat_mode.value,
                              repeat_days=event.repeat_days,
                              repeat_end=event.repeat_end,
                              source=event.source)

        await session.execute(stmt)
        await session.commit()


async def delete_event(event_id: UUID4, owner_id: UUID4):
    async with async_session() as session:
        await chek_event_exists_and_owner_rights(event_id=event_id, owner_id=owner_id)
        stmt = delete(Event).where(Event.id == event_id, Event.owner_id == owner_id)
        await session.execute(stmt)
        await session.commit()



async def find_events_by_filters(owner_id, title, from_datetime, to_datetime, location):
    async with async_session() as session:

        if owner_id:
            owner_id = str(owner_id)
            stmt = select(Event).filter(Event.owner_id == owner_id)
        if title:
            stmt = select(Event).filter(Event.title.like(f'%{title}%'))
        if from_datetime:
            stmt = select(Event).filter(Event.from_datetime >= from_datetime)
        if to_datetime:
            stmt = select(Event).filter(Event.to_datetime <= to_datetime)
        if location:
            stmt = select(Event).filter(Event.location.like(f'%{location}%'))

        stmt = select(Event).filter(and_(Event.title.like(f'%{title}%'),
                                         Event.owner_id == str(owner_id)))
        result = await session.execute(stmt)
        events = result.scalars().all()
        return events


# async def accept_event(event_id: UUID4, user_id: UUID4):
#     async with async_session() as session:
#         event_user = Event_User(id=event.id,
#                           title=event.title,
#                           description=event.description,
#                           from_datetime=event.from_datetime.replace(tzinfo=None),
#                           to_datetime=event.to_datetime.replace(tzinfo=None),
#                           location=event.location,
#                           is_online_event=event.is_online_event,
#                           photo_uri=event.photo_uri,
#                           repeat_mode=event.repeat_mode.value,
#                           repeat_days=event.repeat_days,
#                           repeat_end=event.repeat_end,
#                           source=event.source,
#                           owner_id=owner_id,
#                           )
#         async with session.begin():
#             session.add(new_event)
#         await session.commit()

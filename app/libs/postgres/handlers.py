import uuid
from datetime import datetime
from typing import List, Dict, Union, Optional

from fastapi import HTTPException, status
from pydantic import UUID4

from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.elements import and_, or_

from app.libs.postgres.models import Event, EventUser, User
from app.schemas.calendar_schemas import EventsSchema, Rights, EventUserSchema
from app.settings import get_settings

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import update, delete
from sqlalchemy.dialects.postgresql import insert

settings = get_settings()

connection = f'{settings.postgres_settings.postgres_server}{settings.postgres_settings.postgres_db}'
engine = create_async_engine(connection, echo=True)
async_session = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def check_event_exits_and_user_rights(event_id: UUID4,
                                            user_id: UUID4,
                                            return_event: bool = False) -> Rights or Union[Event, Rights]:
    async with async_session() as session:
        event = await session.get(Event, event_id)
        if event:

            event_user = await session.get(EventUser, {'event_id': event_id,
                                                       'user_id': user_id})
            if event_user:
                rights = event_user.permissions
            else:
                rights = event.default_permissions
            if return_event:
                return event, Rights.get_rights(rights)
            return Rights.get_rights(rights)
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
                          default_permissions=event.default_permissions.value
                          )

        new_event_user = EventUser(
            event_id=event.id,
            user_id=owner_id,
            permissions=Rights.owner.value,
            is_viewed=True,
            is_accepted=True,
        )

        async with session.begin():
            session.add(new_event)
            session.add(new_event_user)
        await session.commit()
        return new_event


async def edit_event(event_id: UUID4, event: EventsSchema, user_id: UUID4):
    async with async_session() as session:
        rights = await check_event_exits_and_user_rights(event_id=event_id, user_id=user_id)
        if 'w' in rights:
            stmt = update(Event).where(Event.id == event_id).values(id=Event.id, title=event.title,
                                                                    description=event.description,
                                                                    from_datetime=event.from_datetime.replace(
                                                                        tzinfo=None),
                                                                    edited_at=datetime.now(),
                                                                    to_datetime=event.to_datetime.replace(
                                                                        tzinfo=None),
                                                                    location=event.location,
                                                                    is_online_event=event.is_online_event,
                                                                    photo_uri=event.photo_uri,
                                                                    repeat_mode=event.repeat_mode.value,
                                                                    repeat_days=event.repeat_days,
                                                                    repeat_end=event.repeat_end,
                                                                    source=event.source,
                                                                    default_permissions=event.default_permissions.value)

            await session.execute(stmt)
            await session.commit()
            event.id = event_id
            return event
        else:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail='Forbidden')


async def delete_event(event_id: UUID4, user_id: UUID4):
    async with async_session() as session:
        rights = await check_event_exits_and_user_rights(event_id=event_id, user_id=user_id)
        if 'd' in rights:
            stmt = delete(Event).where(Event.id == event_id)
            await session.execute(stmt)
            await session.commit()
        else:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail='Forbidden')


async def get_event(event_id: UUID4, user_id: UUID4) -> Event:
    event, rights = await check_event_exits_and_user_rights(event_id=event_id, user_id=user_id, return_event=True)
    if 'r' in rights:
        return event
    else:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail='Forbidden')


async def get_events(user_id: UUID4) -> List[Event]:
    async with async_session() as session:
        stmt = select(Event).select_from(EventUser).where(EventUser.user_id == user_id,
                                                          EventUser.is_accepted == True).join(Event, Event.id == EventUser.event_id)
        result = await session.execute(stmt)
        events = result.scalars().all()
        return events

async def find_events_by_filters(owner_id: UUID4, title: str, location: str, from_datetime: datetime,
                                 to_datetime: datetime):
    async with async_session() as session:
        stmt = select(Event).filter(or_(Event.title.like(f'%{title}%'), title == None),
                                    or_(Event.owner_id == str(owner_id), owner_id == None),
                                    or_(Event.from_datetime >= from_datetime, from_datetime == None),
                                    or_(Event.to_datetime <= to_datetime, to_datetime == None),
                                    or_(Event.location.like(f'%{location}%'), location == None))
        result = await session.execute(stmt)
        events = result.scalars().all()
        return events


async def invite_user(event_id: UUID4, invited_users_id: List[UUID4], user_id: UUID4):
    async with async_session() as session:
        event, rights = await check_event_exits_and_user_rights(event_id=event_id, user_id=user_id, return_event=True)
        if 'i' in rights:
            print(event.default_permissions)
            if event.default_permissions == Rights.close.value:
                permissions = Rights.read_only.value
            else:
                permissions = Rights.public.value
            invites = []
            for user_id in invited_users_id:
                new_event_user = {
                    'event_id': event.id,
                    'user_id': str(user_id),
                    'permissions': permissions,
                    'is_accepted': None,
                }
                invites.append(new_event_user)

            stmt = insert(EventUser).values(invites)
            stmt = stmt.on_conflict_do_update(constraint='event_user_pkey', set_={'is_viewed': stmt.excluded.is_viewed,
                                                                                  'is_accepted': stmt.excluded.is_accepted})
            await session.execute(stmt)
            await session.commit()
        else:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail='Forbidden')


async def accept_to_event(event_id: UUID4, user_id: UUID4):
    async with async_session() as session:

        event_user = await session.get(EventUser, {'event_id': event_id,
                                                   'user_id': user_id})

        if event_user:

            stmt = update(EventUser).where(EventUser.user_id == user_id,
                                           EventUser.event_id == event_id).values(is_viewed=True, is_accepted=True)

            await session.execute(stmt)
            await session.commit()

        else:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail='Invite not found')


async def join_to_event(event_id: UUID4, user_id: UUID4):
    async with async_session() as session:
        rights = await check_event_exits_and_user_rights(event_id=event_id, user_id=user_id)
        if 'r' in rights:

            new_event_user = {
                'event_id': event_id,
                'user_id': user_id,
                'permissions': Rights.public.value,
                'is_accepted': True,
                'is_viewed': True,
            }
            stmt = insert(EventUser).values(new_event_user)
            stmt = stmt.on_conflict_do_update(constraint='event_user_pkey', set_={'is_viewed': True,
                                                                                  'is_accepted': True})
            await session.execute(stmt)
            await session.commit()

        else:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail='Forbidden')


async def reject_invite_to_event(event_id: UUID4, user_id: UUID4):
    async with async_session() as session:
        event_user = await session.get(EventUser, {'event_id': event_id,
                                                   'user_id': user_id})
        if event_user:
            stmt = update(EventUser).where(EventUser.user_id == user_id,
                                           EventUser.event_id == event_id).values(is_viewed=True, is_accepted=False)

            await session.execute(stmt)
            await session.commit()
        else:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail='Invite not found')


async def leave_the_event(event_id: UUID4, user_id: UUID4):
    async with async_session() as session:
        event_user = await session.get(EventUser, {'event_id': event_id,
                                                   'user_id': user_id})
        if event_user:
            stmt = update(EventUser).where(EventUser.user_id == user_id,
                                           EventUser.event_id == event_id).values(is_viewed=True, is_accepted=False)
            # Тут будет анбинд очереди
            await session.execute(stmt)
            await session.commit()
        else:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail='Invite not found')


async def delete_user_from_event(event_id: UUID4, deleted_user_id: UUID4, user_id: UUID4):
    async with async_session() as session:
        rights = await check_event_exits_and_user_rights(event_id=event_id, user_id=user_id)
        if 'm' in rights:
            event_user = await session.get(EventUser, {'event_id': event_id,
                                                       'user_id': deleted_user_id})
            if event_user:
                stmt = delete(EventUser).where(EventUser.user_id == deleted_user_id,
                                               EventUser.event_id == event_id)

                await session.execute(stmt)
                await session.commit()
            else:
                raise HTTPException(status.HTTP_404_NOT_FOUND, detail='User is not a member of the event')
        else:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail='Forbidden')


async def hide_event_for_user(event_id: UUID4, user_id: UUID4):
    async with async_session() as session:
        event_user = await session.get(EventUser, {'event_id': event_id,
                                                   'user_id': user_id})
        if event_user:
            stmt = update(EventUser).where(EventUser.user_id == user_id,
                                           EventUser.event_id == event_id).values(is_hidden=not event_user.is_hidden)

            await session.execute(stmt)
            await session.commit()
        else:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail='User is not a member of the event')


async def transfer_owner_rights(event_id: UUID4, user_id: UUID4, owner_id: UUID4):
    async with async_session() as session:
        rights = await check_event_exits_and_user_rights(event_id=event_id, user_id=owner_id)

        if rights == Rights.owner.value:
            stmt = update(Event).where(Event.id == event_id).values(owner_id=user_id)
            await session.execute(stmt)

            event_user = await session.get(EventUser, {'event_id': event_id,
                                                       'user_id': user_id})

            if event_user:

                stmt = update(EventUser).where(EventUser.user_id == user_id,
                                               EventUser.event_id == event_id).values(permissions=Rights.owner.value)
                await session.execute(stmt)
            else:

                new_event_user = {
                    'event_id': event_id,
                    'user_id': user_id,
                    'permissions': Rights.owner.value,
                    'is_accepted': True,
                    'is_viewed': True,
                }
                stmt = insert(EventUser).values(new_event_user)
                await session.execute(stmt)

            stmt = update(EventUser).where(EventUser.user_id == owner_id,
                                           EventUser.event_id == event_id).values(permissions=Rights.public.value)
            await session.execute(stmt)
            await session.commit()
        else:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail='Forbidden')


async def get_event_participants(event_id: UUID4, user_id: UUID4):
    async with async_session() as session:
        rights = await check_event_exits_and_user_rights(event_id=event_id, user_id=user_id)
        if 'r' in rights:
            stmt = select(User).select_from(EventUser).where(EventUser.event_id == event_id,
                                                             EventUser.is_accepted == True).join(User,
                                                                                                 User.id == EventUser.user_id)
            result = await session.execute(stmt)
            events = result.scalars().all()
            return events
        else:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail='Forbidden')


async def clone_event(event_id: UUID4, user_id: UUID4):
    async with async_session() as session:
        event, rights = await check_event_exits_and_user_rights(event_id=event_id, user_id=user_id, return_event=True)
        if 'r' in rights:
            id = uuid.uuid4()
            new_event = Event(id=id,
                              title=event.title,
                              description=event.description,
                              from_datetime=event.from_datetime.replace(tzinfo=None),
                              to_datetime=event.to_datetime.replace(tzinfo=None),
                              location=event.location,
                              is_online_event=event.is_online_event,
                              photo_uri=event.photo_uri,
                              repeat_mode=event.repeat_mode,
                              repeat_days=event.repeat_days,
                              repeat_end=event.repeat_end,
                              source=event.source,
                              owner_id=user_id,
                              default_permissions=event.default_permissions
                              )

            new_event_user = EventUser(
                event_id=id,
                user_id=user_id,
                permissions=Rights.owner.value,
                is_viewed=True,
                is_accepted=True,
            )

            async with session.begin():
                session.add(new_event)
                session.add(new_event_user)
            await session.commit()
            return new_event

async def like_event(event_id: UUID4, user_id: UUID4):
    async with async_session() as session:
        event_user = await session.get(EventUser, {'event_id': event_id,
                                                   'user_id': user_id})
        if event_user:
            stmt = update(EventUser).where(EventUser.user_id == user_id,
                                           EventUser.event_id == event_id).values(is_liked=not event_user.is_liked)

            await session.execute(stmt)
            await session.commit()
        else:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail='User is not a member of the event')

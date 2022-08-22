import uuid
from datetime import datetime, date
from typing import List, Union, Optional

from aio_pika import ExchangeType
from fastapi import HTTPException, status
from pydantic import UUID4

from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.elements import  or_

from app.libs.postgres.models import Event, EventUser, User
from app.schemas.calendar_schemas import EventsSchema, Rights,EventRepeatMode
from app.settings import get_settings

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import update, delete
from sqlalchemy.dialects.postgresql import insert

from platform_services.rabbitmq import RabbitMQWrapper

import datetime as d

settings = get_settings()

connection = f'{settings.postgres_settings.postgres_server}{settings.postgres_settings.postgres_db}'
engine = create_async_engine(connection, echo=True)
async_session = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def create_exchange_and_bind_queue(exchange_name: str, queue_name: str) -> None:
    rabbit_mq = RabbitMQWrapper()
    await rabbit_mq.startup_event_handler()
    async with rabbit_mq.channel_pool.acquire() as channel:
        try:
            queue = await channel.get_queue(name=queue_name, ensure=True)
        except:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f'Queue for user {queue_name} not found')
        exchange = await channel.declare_exchange(name=exchange_name, type=ExchangeType.FANOUT, auto_delete=True)
        await queue.bind(exchange)
    await rabbit_mq.shutdown_event_handler()


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


async def get_dates_from_date_interval(end_date: date,
                                       repeat_days: Optional[List[int]],
                                       repeat_interval: Optional[int],
                                       repeat_mode: EventRepeatMode) -> List[date]:
    start_date = date.today()
    all_dates = []
    repeat_dates = []
    if repeat_mode == EventRepeatMode.week_days:
        while start_date <= end_date:
            all_dates.append(start_date)
            start_date += d.timedelta(days=1)
        for day in repeat_days:
            for data in all_dates:
                print(day, data.weekday())
                if data.weekday() == day:
                    repeat_dates.append(data)
        return sorted(repeat_dates)
    elif repeat_mode == EventRepeatMode.interval:
        while start_date <= end_date:
            repeat_dates.append(start_date)
            start_date += d.timedelta(days=repeat_interval)
        return sorted(repeat_dates)


async def insert_event(event: EventsSchema,
                       owner_id: UUID4) -> Event:
    async with async_session() as session:
        if event.repeat_mode != EventRepeatMode.no_repeat:
            event.repeat_dates = await get_dates_from_date_interval(end_date=event.repeat_end,
                                                                    repeat_days=event.repeat_days,
                                                                    repeat_interval=event.repeat_interval,
                                                                    repeat_mode=event.repeat_mode)
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
                          repeat_dates=event.repeat_dates,
                          repeat_interval=event.repeat_interval,
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
        await create_exchange_and_bind_queue(exchange_name=str(event.id), queue_name=str(owner_id))
        async with session.begin():
            session.add(new_event)
            session.add(new_event_user)
        await session.commit()


        return new_event


async def edit_event(event_id: UUID4, event: EventsSchema, user_id: UUID4, generate_dates_interval: bool) -> EventsSchema:
    async with async_session() as session:
        rights = await check_event_exits_and_user_rights(event_id=event_id, user_id=user_id)
        if 'w' in rights:
            if generate_dates_interval:
                if event.repeat_mode != EventRepeatMode.no_repeat:
                    event.repeat_dates = await get_dates_from_date_interval(end_date=event.repeat_end,
                                                                            repeat_days=event.repeat_days,
                                                                            repeat_interval=event.repeat_interval,
                                                                            repeat_mode=event.repeat_mode)
            stmt = update(Event).where(Event.id == event_id).values(id=Event.id,
                                                                    title=event.title,
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
                                                                    repeat_dates=event.repeat_dates,
                                                                    repeat_interval=event.repeat_interval,
                                                                    source=event.source,
                                                                    default_permissions=event.default_permissions.value)

            await session.execute(stmt)
            await session.commit()
            event.id = event_id
            return event
        else:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail='Forbidden')


async def change_next_repeat_and_create_new_event(event_id: UUID4, event: EventsSchema, user_id: UUID4) -> Event:
    async with async_session() as session:
        changing_event, rights = await check_event_exits_and_user_rights(event_id=event_id, user_id=user_id,
                                                                         return_event=True)
        if 'w' in rights:
            start_date = date.today()
            if changing_event.repeat_dates:
                repeat_dates = sorted([x for x in changing_event.repeat_dates if x >= start_date])

                changing_date = repeat_dates[0]
                repeat_dates.pop(0)

                stmt = update(Event).where(Event.id == event_id).values(id=Event.id,
                                                                        repeat_dates=repeat_dates,
                                                                        )

                await session.execute(stmt)
                new_event = Event(id=event.id,
                                  title=event.title,
                                  description=event.description,
                                  from_datetime=changing_date,
                                  to_datetime=changing_date,
                                  location=event.location,
                                  is_online_event=event.is_online_event,
                                  photo_uri=event.photo_uri,
                                  repeat_mode=event.repeat_mode.value,
                                  repeat_days=event.repeat_days,
                                  repeat_end=event.repeat_end,
                                  repeat_dates=event.repeat_dates,
                                  repeat_interval=event.repeat_interval,
                                  source=event.source,
                                  owner_id=user_id,
                                  default_permissions=event.default_permissions.value
                                  )

                new_event_user = EventUser(
                    event_id=event.id,
                    user_id=user_id,
                    permissions=Rights.owner.value,
                    is_viewed=True,
                    is_accepted=True,
                )

                session.add(new_event)
                session.add(new_event_user)
                await session.commit()
                return new_event
            else:
                raise HTTPException(status.HTTP_404_NOT_FOUND, detail='Event have not repeat dates')


async def delete_event(event_id: UUID4, user_id: UUID4) -> None:
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
                                                          EventUser.is_accepted == True).join(Event,
                                                                                              Event.id == EventUser.event_id)
        result = await session.execute(stmt)
        events = result.scalars().all()
        return events


async def find_events_by_filters(owner_id: UUID4, title: str, location: str, from_datetime: datetime,
                                 to_datetime: datetime) -> List[Event]:
    async with async_session() as session:
        stmt = select(Event).filter(or_(Event.title.like(f'%{title}%'), title == None),
                                    or_(Event.owner_id == str(owner_id), owner_id == None),
                                    or_(Event.from_datetime >= from_datetime, from_datetime == None),
                                    or_(Event.to_datetime <= to_datetime, to_datetime == None),
                                    or_(Event.location.like(f'%{location}%'), location == None))
        result = await session.execute(stmt)
        events = result.scalars().all()
        return events


async def invite_user(event_id: UUID4, invited_users_id: List[UUID4], user_id: UUID4) -> None:
    async with async_session() as session:
        event, rights = await check_event_exits_and_user_rights(event_id=event_id, user_id=user_id, return_event=True)
        if 'i' in rights:

            if event.default_permissions == Rights.close.value:
                permissions = Rights.read_only.value
            else:
                permissions = Rights.public.value
            invites = []


            for user_id in invited_users_id:
                event_user = await session.get(EventUser, {'event_id': event_id,
                                                           'user_id': user_id})
                if event_user:
                    if event_user.is_accepted:
                        continue
                new_event_user = {
                    'event_id': event.id,
                    'user_id': str(user_id),
                    'permissions': permissions,
                    'is_accepted': None,
                }
                invites.append(new_event_user)

            if len(invites) == 0:
                return
            stmt = insert(EventUser).values(invites)
            stmt = stmt.on_conflict_do_update(constraint='event_user_pkey', set_={'is_viewed': stmt.excluded.is_viewed,
                                                                                  'is_accepted': stmt.excluded.is_accepted})
            await session.execute(stmt)
            await session.commit()
        else:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail='Forbidden')


async def accept_to_event(event_id: UUID4, user_id: UUID4) -> None:
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


async def join_to_event(event_id: UUID4, user_id: UUID4) -> None:
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


async def reject_invite_to_event(event_id: UUID4, user_id: UUID4) -> None:
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


async def leave_the_event(event_id: UUID4, user_id: UUID4) -> None:
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


async def delete_user_from_event(event_id: UUID4, deleted_user_id: UUID4, user_id: UUID4) -> None:
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


async def hide_event_for_user(event_id: UUID4, user_id: UUID4) -> None:
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


async def transfer_owner_rights(event_id: UUID4, user_id: UUID4, owner_id: UUID4) -> None:
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


async def get_event_participants(event_id: UUID4, user_id: UUID4) -> List[User]:
    async with async_session() as session:
        rights = await check_event_exits_and_user_rights(event_id=event_id, user_id=user_id)
        if 'r' in rights:
            stmt = select(User).select_from(EventUser).where(EventUser.event_id == event_id,
                                                             EventUser.is_accepted == True).join(User,
                                                                                                 User.id == EventUser.user_id)
            result = await session.execute(stmt)
            participants = result.scalars().all()
            return participants
        else:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail='Forbidden')


async def clone_event(event_id: UUID4, user_id: UUID4) -> Event:
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


async def like_event(event_id: UUID4, user_id: UUID4) -> None:
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


async def remind_event(event_id: UUID4, user_id: UUID4) -> None:
    async with async_session() as session:
        event_user = await session.get(EventUser, {'event_id': event_id,
                                                   'user_id': user_id})
        if event_user:
            stmt = update(EventUser).where(EventUser.user_id == user_id,
                                           EventUser.event_id == event_id).values(is_reminder_on=not event_user.is_reminder_on)

            await session.execute(stmt)
            await session.commit()
        else:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail='User is not a member of the event')

from datetime import datetime
from typing import List, Union

from fastapi import HTTPException, status
from pydantic import UUID4

from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker

from app.libs.postgres.events_handlers import get_dates_from_date_interval
from app.libs.postgres.models import Event, Task, TaskUser
from app.schemas.calendar_schemas import Rights, TasksSchema, EventRepeatMode
from app.settings import get_settings

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import update, delete

settings = get_settings()

connection = f'{settings.postgres_settings.postgres_server}{settings.postgres_settings.postgres_db}'
engine = create_async_engine(connection, echo=True)
async_session = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def check_task_exits_and_user_rights(task_id: UUID4,
                                           user_id: UUID4,
                                           return_task: bool = False) -> Rights or Union[Task, Rights]:
    async with async_session() as session:
        task = await session.get(Task, task_id)
        if task:

            task_user = await session.get(TaskUser, {'task_id': task_id,
                                                     'user_id': user_id})
            if task_user:
                rights = task_user.permissions
            else:
                rights = task.default_permissions
            if return_task:
                return task, Rights.get_rights(rights)
            return Rights.get_rights(rights)
        else:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail='Task not found')


async def insert_task(task: TasksSchema,
                      owner_id: UUID4) -> Task:
    async with async_session() as session:
        if task.repeat_mode != EventRepeatMode.no_repeat:
            task.repeat_dates = await get_dates_from_date_interval(end_date=task.repeat_end,
                                                                   repeat_days=task.repeat_days,
                                                                   repeat_interval=task.repeat_interval,
                                                                   repeat_mode=task.repeat_mode)
        new_task = Task(id=task.id,

                        title=task.title,
                        description=task.description,
                        icon=task.icon,
                        from_datetime=task.from_datetime.replace(tzinfo=None),
                        to_datetime=task.to_datetime.replace(tzinfo=None),
                        location=task.location,
                        repeat_mode=task.repeat_mode.value,
                        repeat_days=task.repeat_days,
                        repeat_end=task.repeat_end,
                        repeat_dates=task.repeat_dates,
                        repeat_interval=task.repeat_interval,
                        parent_task=task.parent_task,
                        owner_id=owner_id,
                        default_permissions=task.default_permissions.value
                        )

        new_task_user = TaskUser(
            task_id=task.id,
            user_id=owner_id,
            permissions=Rights.owner.value,
            is_viewed=True,
            is_accepted=True,
        )

        async with session.begin():
            session.add(new_task)
            session.add(new_task_user)
        await session.commit()
        return new_task


async def edit_task(task_id: UUID4, task: TasksSchema, user_id: UUID4, generate_dates_interval: bool) -> TasksSchema:
    async with async_session() as session:
        rights = await check_task_exits_and_user_rights(task_id=task_id, user_id=user_id)
        if 'w' in rights:
            if generate_dates_interval:
                if task.repeat_mode != EventRepeatMode.no_repeat:
                    task.repeat_dates = await get_dates_from_date_interval(end_date=task.repeat_end,
                                                                           repeat_days=task.repeat_days,
                                                                           repeat_interval=task.repeat_interval,
                                                                           repeat_mode=task.repeat_mode)
            stmt = update(Task).where(Task.id == task_id).values(id=Task.id,

                                                                 title=task.title,
                                                                 description=task.description,
                                                                 icon=task.icon,
                                                                 edited_at=datetime.now(),
                                                                 from_datetime=task.from_datetime.replace(tzinfo=None),
                                                                 to_datetime=task.to_datetime.replace(tzinfo=None),
                                                                 location=task.location,
                                                                 repeat_mode=task.repeat_mode.value,
                                                                 repeat_days=task.repeat_days,
                                                                 repeat_end=task.repeat_end,
                                                                 repeat_dates=task.repeat_dates,
                                                                 repeat_interval=task.repeat_interval,
                                                                 parent_task=task.parent_task,

                                                                 default_permissions=task.default_permissions.value)

            await session.execute(stmt)
            await session.commit()
            task.id = task_id
            return task
        else:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail='Forbidden')


async def delete_task(task_id: UUID4, user_id: UUID4) -> None:
    async with async_session() as session:
        rights = await check_task_exits_and_user_rights(task_id=task_id, user_id=user_id)
        if 'd' in rights:
            stmt = delete(Task).where(Task.id == task_id)
            await session.execute(stmt)
            await session.commit()
        else:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail='Forbidden')


async def get_task(task_id: UUID4, user_id: UUID4) -> Event:
    task, rights = await check_task_exits_and_user_rights(task_id=task_id, user_id=user_id, return_task=True)
    if 'r' in rights:
        return task
    else:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail='Forbidden')


async def get_tasks(user_id: UUID4) -> List[Task]:
    async with async_session() as session:
        stmt = select(Task).select_from(TaskUser).where(TaskUser.user_id == user_id,
                                                        TaskUser.is_accepted == True).join(Task,
                                                                                           Task.id == TaskUser.task_id)
        result = await session.execute(stmt)
        tasks = result.scalars().all()
        return tasks


async def like_task(task_id: UUID4, user_id: UUID4) -> None:
    async with async_session() as session:
        task_user = await session.get(TaskUser, {'task_id': task_id,
                                                 'user_id': user_id})
        if task_user:
            stmt = update(TaskUser).where(TaskUser.user_id == user_id,
                                          TaskUser.task_id == task_id).values(is_liked=not task_user.is_liked)

            await session.execute(stmt)
            await session.commit()
        else:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail='User is not a member of the event')


async def done_task(task_id: UUID4, user_id: UUID4) -> None:
    async with async_session() as session:
        task_user = await session.get(TaskUser, {'task_id': task_id,
                                                 'user_id': user_id})
        if task_user:
            stmt = update(TaskUser).where(TaskUser.user_id == user_id,
                                          TaskUser.task_id == task_id).values(is_done=not task_user.is_done)

            await session.execute(stmt)
            await session.commit()
        else:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail='User is not a member of the event')

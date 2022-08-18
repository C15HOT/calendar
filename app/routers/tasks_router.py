from fastapi import APIRouter, Depends
from app.schemas.calendar_schemas import *
from app.libs.auth import auth_required
from fastapi import status, HTTPException
from app.settings import get_settings
from app.libs.postgres.tasks_handlers import *

import datetime as d

tasks_router = APIRouter(tags=['Tasks'], prefix='/tasks')
settings = get_settings()


@tasks_router.post('/create/', summary='Create task')
async def add_task_route(task: TasksSchema,
                    owner_id: UUID4 = Depends(auth_required)):
    try:
        new_task = await insert_task(task=task, owner_id=owner_id)
    except BaseException as exc:
        print('\n')
        print(exc)
        print('\n')
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Failed to write event to database')
    return new_task


@tasks_router.delete('/{task_id}/delete', summary='Delete task')
async def delete_task_route(task_id: UUID4,
                       user_id: UUID4 = Depends(auth_required)):
    await delete_task(task_id=task_id, user_id=user_id)
    return status.HTTP_200_OK


@tasks_router.get('/{task_id}/info', summary='Get task')
async def get_task_route(task_id: UUID4,
                    user_id: UUID4 = Depends(auth_required)):
    event = await get_task(task_id=task_id, user_id=user_id)
    return event

@tasks_router.get('/tasks/', summary='Get tasks')
async def get_tasks_route(user_id: UUID4 = Depends(auth_required)):
        tasks = await get_tasks(user_id=user_id)
        return tasks


@tasks_router.put('/{task_id}/info/edit', summary='Update task')
async def edit_task_route(task_id: UUID4,
                       task: TasksSchema,
                           generate_dates_interval: bool = True,
                       user_id: UUID4 = Depends(auth_required)):

    updated_event = await edit_task(task_id=task_id, user_id=user_id, generate_dates_interval=generate_dates_interval,
                                     task=task)
    return updated_event

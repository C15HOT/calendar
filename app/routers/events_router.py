from fastapi import APIRouter, Depends
from app.schemas.calendar_schemas import *
from app.libs.auth import auth_required
from fastapi import status, HTTPException
from app.settings import get_settings
from app.libs.postgres.handlers import insert_event, get_event, get_events

events_router = APIRouter(tags=['Events'])
settings = get_settings()


@events_router.post('/add_event/', summary='Add event calendar. Access: all authenticated users')
async def add_event(event: EventsSchema,
                    owner_id: UUID4 = Depends(auth_required)):
    try:
        insert_event(event=event, owner_id=owner_id)
    except BaseException as exc:
        print(exc)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Failed to write event to database')
    return status.HTTP_201_CREATED


@events_router.get('/get_event/{evend_id}', summary='Get event calendar')
async def add_event(event_id: UUID4,
                    user_id: UUID4 = Depends(auth_required)):
    try:
        event = get_event(event_id=event_id)

    except BaseException as exc:
        print(exc)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Failed to read event from database')

    if event.owner_id == user_id:
        return event
    else:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail='Not allowed')


@events_router.get('/all_user_events/', summary='Get events calendar')
async def add_event(owner_id: UUID4 = Depends(auth_required)):
    try:
        events = get_events(owner_id=owner_id)
        return events
    except BaseException as exc:
        print(exc)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Failed to read events from database')



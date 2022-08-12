from fastapi import APIRouter, Depends
from app.schemas.calendar_schemas import *
from app.libs.auth import auth_required
from fastapi import status, HTTPException
from app.settings import get_settings
from app.libs.postgres.handlers import insert_event, get_event, get_events, update_event, delete_event, \
    find_events_by_filters

events_router = APIRouter(tags=['Events'])
settings = get_settings()


@events_router.post('/add_event/', summary='Add event calendar. Access: all authenticated users')
async def add_event_route(event: EventsSchema,
                    owner_id: UUID4 = Depends(auth_required)):
    try:
        await insert_event(event=event, owner_id=owner_id)
    except BaseException as exc:
        print(exc)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Failed to write event to database')
    return status.HTTP_201_CREATED


@events_router.get('/get_event/{evend_id}', summary='Get event calendar')
async def get_event_route(event_id: UUID4,
                    user_id: UUID4 = Depends(auth_required)):
    event = await get_event(event_id=event_id, user_id=user_id)
    return event



@events_router.get('/all_user_events/', summary='Get events calendar')
async def get_events_route(owner_id: UUID4 = Depends(auth_required)):
        events = await get_events(owner_id=owner_id)
        return events




@events_router.put('/update_event/{evend_id}', summary='Update event')
async def update_event_route(event_id: UUID4,
                       event: EventsSchema,
                       owner_id: UUID4 = Depends(auth_required)):
    try:
        updated_event = await update_event(event_id=event_id, owner_id=owner_id,
                     event=event)
        return updated_event
    except BaseException as exc:
        print(exc)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Failed to update event')


@events_router.delete('/delete_event/{event_id}', summary='Delete event')
async def delete_event_route(event_id: UUID4,
                       owner_id: UUID4 = Depends(auth_required)):
    await delete_event(event_id=event_id, owner_id=owner_id)
    return status.HTTP_200_OK



@events_router.get('/get_events_by_filter/', summary='Find events by filter')
async def find_events_by_filter_route(title: str = None,
                                      from_datetime: datetime = None,
                                      to_datetime: datetime = None,
                                      location: str = None,
                                      user_id: UUID4 = None,
                                      owner_id: UUID4 = Depends(auth_required),
                                      ):

    events = await find_events_by_filters(owner_id=user_id,
                                          title=title,
                                          from_datetime=from_datetime,
                                          to_datetime=to_datetime,
                                          location=location)

    return events

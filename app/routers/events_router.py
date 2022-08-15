from fastapi import APIRouter, Depends
from app.schemas.calendar_schemas import *
from app.libs.auth import auth_required
from fastapi import status, HTTPException
from app.settings import get_settings
from app.libs.postgres.handlers import insert_event, get_event,  update_event, delete_event, \
    find_events_by_filters, invite_user, accept_to_event, reject_invite_to_event, join_to_event

import datetime as d

events_router = APIRouter(tags=['Events'], prefix='/event')
settings = get_settings()


@events_router.post('/create/', summary='Add event calendar. Access: all authenticated users')
async def add_event_route(event: EventsSchema,
                    owner_id: UUID4 = Depends(auth_required)):
    try:
        new_event = await insert_event(event=event, owner_id=owner_id)
    except BaseException as exc:
        print(exc)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Failed to write event to database')
    return new_event


@events_router.get('/get/{evend_id}', summary='Get event calendar')
async def get_event_route(event_id: UUID4,
                    user_id: UUID4 = Depends(auth_required)):
    event = await get_event(event_id=event_id, user_id=user_id)
    return event



# @events_router.get('/get_all_users_events/', summary='Get events calendar')
# async def get_events_route(owner_id: UUID4 = Depends(auth_required)):
#         events = await get_events(owner_id=owner_id)
#         return events




@events_router.put('/update/{evend_id}', summary='Update event')
async def update_event_route(event_id: UUID4,
                       event: EventsSchema,
                       user_id: UUID4 = Depends(auth_required)):

    updated_event = await update_event(event_id=event_id, user_id=user_id,
                 event=event)
    return updated_event



@events_router.delete('/delete/{event_id}', summary='Delete event')
async def delete_event_route(event_id: UUID4,
                       user_id: UUID4 = Depends(auth_required)):
    await delete_event(event_id=event_id, user_id=user_id)
    return status.HTTP_200_OK



@events_router.get('/get_events_by_filter/', summary='Find events by filter')
async def find_events_by_filter_route(title: str = None,
                                      from_datetime: datetime = d.date(2000, 12, 12),
                                      to_datetime: datetime = d.date(3000, 12, 12),
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

@events_router.post('/{evend_id}/invite', summary='Invite user to event')
async def invite_user_route(event_id: UUID4,
                            invited_users_id: List[UUID4],
                            user_id: UUID4 = Depends(auth_required)):

    await invite_user(event_id=event_id, invited_users_id=invited_users_id, user_id=user_id)

    return status.HTTP_200_OK


@events_router.post('/{event_id}/accept', summary='Join to event')
async def join_to_event_route(event_id: UUID4,
                              user_id: UUID4 = Depends(auth_required)):

    await accept_to_event(event_id=event_id, user_id=user_id)
    return status.HTTP_200_OK


@events_router.post('/{event_id}/join', summary='Join to event')
async def join_to_event_route(event_id: UUID4,
                              user_id: UUID4 = Depends(auth_required)):

    await join_to_event(event_id=event_id, user_id=user_id)
    return status.HTTP_200_OK

@events_router.post('/{event_id}/reject', summary='Reject invite to event')
async def reject_invite_to_event_route(event_id: UUID4,
                                 user_id: UUID4 = Depends(auth_required)):
    await reject_invite_to_event(event_id=event_id, user_id=user_id)
    return status.HTTP_200_OK

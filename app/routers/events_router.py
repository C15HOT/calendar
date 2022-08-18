from fastapi import APIRouter, Depends
from app.schemas.calendar_schemas import *
from app.libs.auth import auth_required
from fastapi import status, HTTPException
from app.settings import get_settings
from app.libs.postgres.events_handlers import insert_event, get_event, edit_event, delete_event, \
    find_events_by_filters, invite_user, accept_to_event, reject_invite_to_event, join_to_event, leave_the_event, \
    delete_user_from_event, hide_event_for_user, transfer_owner_rights, get_event_participants, clone_event, like_event, \
    get_events, change_next_repeat_and_create_new_event

import datetime as d

events_router = APIRouter(tags=['Events'], prefix='/event')
settings = get_settings()


@events_router.post('/create/', summary='Add event calendar. Access: all authenticated users')
async def add_event_route(event: EventsSchema,
                    owner_id: UUID4 = Depends(auth_required)):
    try:
        new_event = await insert_event(event=event, owner_id=owner_id)
    except BaseException as exc:
        print('\n')
        print(exc)
        print('\n')
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Failed to write event to database')
    return new_event


@events_router.get('/{evend_id}/info', summary='Get event')
async def get_event_route(event_id: UUID4,
                    user_id: UUID4 = Depends(auth_required)):
    event = await get_event(event_id=event_id, user_id=user_id)
    return event



@events_router.get('/events/', summary='Get events calendar')
async def get_events_route(user_id: UUID4 = Depends(auth_required)):
        events = await get_events(user_id=user_id)
        return events




@events_router.put('/{evend_id}/info/edit', summary='Update event')
async def edit_event_route(event_id: UUID4,
                       event: EventsSchema,
                           generate_dates_interval: bool = True,
                       user_id: UUID4 = Depends(auth_required)):

    updated_event = await edit_event(event_id=event_id, user_id=user_id, generate_dates_interval=generate_dates_interval,
                                     event=event)
    return updated_event

@events_router.post('/{event_id}/change_next_repeat', summary='Delete next repeat and create new event on next date')
async def change_next_repeat_route(event_id: UUID4,
                                   event: EventsSchema,
                                   user_id: UUID4 = Depends(auth_required)):
    new_event = await change_next_repeat_and_create_new_event(event_id=event_id, event=event, user_id=user_id)
    return new_event



@events_router.delete('/{event_id}/delete', summary='Delete event')
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
async def accept_to_event_route(event_id: UUID4,
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


@events_router.post('/{event_id}/leave', summary='Leave from event')
async def leave_the_event_route(event_id: UUID4,
                                 user_id: UUID4 = Depends(auth_required)):
    await leave_the_event(event_id=event_id, user_id=user_id)
    return status.HTTP_200_OK


@events_router.delete('/{event_id}/user/{deleted_user_id}/delete', summary='Delete user from event')
async def delete_user_from_event_route(event_id: UUID4,
                                       deleted_user_id: UUID4,
                                       user_id: UUID4 = Depends(auth_required)):
    await delete_user_from_event(event_id=event_id, deleted_user_id=deleted_user_id, user_id=user_id)
    return status.HTTP_200_OK


@events_router.post('/{event_id}/hide', summary='Hide event')
async def hide_event_route(event_id: UUID4,
                           user_id: UUID4 = Depends(auth_required)):
    await hide_event_for_user(event_id=event_id, user_id=user_id)
    return status.HTTP_200_OK


@events_router.post('/{event_id}/owner/transfer', summary='Transfer owner rights')
async def transfer_owner_rights_route(event_id: UUID4,
                                      user_id: UUID4,
                                      owner_id: UUID4 = Depends(auth_required)):

    await transfer_owner_rights(event_id=event_id, user_id=user_id, owner_id=owner_id)
    return status.HTTP_200_OK


@events_router.get('/{event_id}/participants', summary='Get event participants')
async def get_event_participants_route(event_id: UUID4,
                                       user_id: UUID4 = Depends(auth_required)):
    participants = await get_event_participants(event_id=event_id,
                                 user_id=user_id)
    return participants


@events_router.post('/{event_id}/clone', summary='Clone event')
async def clone_event_route(event_id: UUID4,
                            user_id: UUID4 = Depends(auth_required)):
    event = await clone_event(event_id=event_id, user_id=user_id)
    return event

@events_router.post('/{event_id}/like', summary='Like event')
async def like_event_route(event_id: UUID4,
                           user_id: UUID4 = Depends(auth_required)):
    await like_event(event_id=event_id, user_id=user_id)
    return status.HTTP_200_OK

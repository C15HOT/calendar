from platform_services.postgresql import PostgreSQListener
from pydantic import BaseModel, UUID4


listener = PostgreSQListener()

class EventPayload(BaseModel):
    event_id: UUID4
    title: str

@listener.listen_channel("event_create")
def event_create(payload: str):
    print('\n')
    print("INSERT:", payload)

@listener.listen_channel("event_update")
def event_update(payload: str):
    print('\n')
    print('UPDATE:', payload)

@listener.listen_channel("event_delete")
def event_update(payload: str):
    print('\n')
    print('DELETE:', payload)

@listener.listen_channel("task_create")
def task_create(payload: str):
    print('\n')
    print("INSERT:", payload)

@listener.listen_channel("task_update")
def task_update(payload: str):
    print('\n')
    print('UPDATE:', payload)

@listener.listen_channel("task_delete")
def task_delete(payload: str):
    print('\n')
    print('DELETE:', payload)



@listener.listen_channel("event_user_join")
def event_user_join(payload: str):
    print('\n')
    print('event_user_join:', payload)


@listener.listen_channel("event_user_invite")
def event_user_invite(payload: str):
    print('\n')
    print('event_user_invite:', payload)


@listener.listen_channel("event_user_delete")
def event_user_delete(payload: str):
    print('\n')
    print('event_user_delete:', payload)


@listener.listen_channel("event_transfer")
def event_transfer(payload: str):
    print('\n')
    print('event_transfer:', payload)


@listener.listen_channel("event_user_rejected")
def event_user_rejected(payload: str):
    print('\n')
    print('event_user_rejected:', payload)


@listener.listen_channel("event_user_like")
def event_user_liked(payload: str):
    print('\n')
    print('event_user_liked:', payload)


@listener.listen_channel("event_user_unlike")
def event_user_unliked(payload: str):
    print('\n')
    print('event_user_unliked:', payload)


@listener.listen_channel("event_user_remind")
def event_user_remind(payload: str):
    print('\n')
    print('event_user_remind:', payload)


@listener.listen_channel("event_user_unremind")
def event_user_unremind(payload: str):
    print('\n')
    print('event_user_unremind:', payload)


@listener.listen_channel("event_user_hidden")
def event_user_hidden(payload: str):
    print('\n')
    print('event_user_hidden:', payload)


@listener.listen_channel("event_user_unhidden")
def event_user_unhidden(payload: str):
    print('\n')
    print('event_user_unhidden:', payload)



@listener.listen_channel("task_user_like")
def task_user_like(payload: str):
    print('\n')
    print('task_user_like:', payload)


@listener.listen_channel("task_user_unlike")
def task_user_unlike(payload: str):
    print('\n')
    print('task_user_unlike:', payload)


@listener.listen_channel("task_user_done")
def task_user_done(payload: str):
    print('\n')
    print('task_user_done:', payload)


@listener.listen_channel("task_user_undone")
def task_user_undone(payload: str):
    print('\n')
    print('task_user_undone:', payload)

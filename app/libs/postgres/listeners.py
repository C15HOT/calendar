import aio_pika
from aio_pika import ExchangeType
from fastapi import HTTPException
from platform_services.postgresql import PostgreSQListener
from platform_services.rabbitmq import RabbitMQWrapper
from pydantic import UUID4
from starlette import status

from app.schemas.calendar_schemas import EventsSchema, EventUserSchema, TasksSchema, TaskUserSchema

import json

from app.settings import getLogger


logger = getLogger('LISTENER')



listener = PostgreSQListener()


async def create_exchange_and_bind_or_unbind_queue(exchange_name: UUID4, queue_name: UUID4,
                                                   unbind: bool = False) -> None:
    rabbit_mq = RabbitMQWrapper()
    exchange_name = str(exchange_name)
    queue_name = str(queue_name)
    await rabbit_mq.startup_event_handler()
    async with rabbit_mq.channel_pool.acquire() as channel:
        try:
            queue = await channel.get_queue(name=queue_name, ensure=True)
        except:

            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f'Queue for user {queue_name} not found')
        exchange = await channel.declare_exchange(name=exchange_name, durable=True, type=ExchangeType.FANOUT,
                                                  auto_delete=True)
        if unbind:
            await queue.unbind(exchange)
        else:
            await queue.bind(exchange)
    await rabbit_mq.shutdown_event_handler()


async def delete_exchange(exchange_name: UUID4) -> None:
    exchange_name = str(exchange_name)
    rabbit_mq = RabbitMQWrapper()
    await rabbit_mq.startup_event_handler()
    async with rabbit_mq.channel_pool.acquire() as channel:
        try:
            await channel.exchange_delete(exchange_name=exchange_name)
        except:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail='Exchange not found')
    await rabbit_mq.shutdown_event_handler()


async def send_message(event_type: str, exchange_name: UUID4, payload: json) -> None:
    rabbit_mq = RabbitMQWrapper()
    exchange_name = str(exchange_name)
    await rabbit_mq.startup_event_handler()
    message = {'event': event_type, 'payload': payload}
    logger.info(  message)
    async with rabbit_mq.channel_pool.acquire() as channel:
        exchange = await channel.get_exchange(name=exchange_name)
        message = aio_pika.Message(body=json.dumps(message).encode())
        await exchange.publish(message, routing_key=exchange_name)
    await rabbit_mq.shutdown_event_handler()


@listener.listen_channel("event_create")
async def event_create(payload) -> None:

    json_payload = json.loads(payload)
    event = EventsSchema(**json_payload)
    event_type = 'calendar/event/created'
    await create_exchange_and_bind_or_unbind_queue(exchange_name=event.id, queue_name=event.owner_id)
    await send_message(event_type=event_type, exchange_name=event.id, payload=json_payload)


@listener.listen_channel("event_update")
async def event_update(payload: str) -> None:
    json_payload = json.loads(payload)
    event = EventsSchema(**json_payload)
    event_type = 'calendar/event/edited'
    await send_message(event_type=event_type, exchange_name=event.id, payload=json_payload)


@listener.listen_channel("event_delete")
async def event_delete(payload: str) -> None:
    json_payload = json.loads(payload)
    event = EventsSchema(**json_payload)
    event_type = 'calendar/event/deleted'
    await send_message(event_type=event_type, exchange_name=event.id, payload=json_payload)
    await delete_exchange(exchange_name=event.id)


@listener.listen_channel("task_create")
async def task_create(payload: str) -> None:
    json_payload = json.loads(payload)
    task = TasksSchema(**json_payload)
    event_type = 'calendar/task/created'
    await create_exchange_and_bind_or_unbind_queue(exchange_name=task.id, queue_name=task.owner_id)
    await send_message(event_type=event_type, exchange_name=task.id, payload=json_payload)


@listener.listen_channel("task_update")
async def task_update(payload: str) -> None:
    json_payload = json.loads(payload)
    task = TasksSchema(**json_payload)
    event_type = 'calendar/task/edited'
    await send_message(event_type=event_type, exchange_name=task.id, payload=json_payload)


@listener.listen_channel("task_delete")
async def task_delete(payload: str) -> None:
    json_payload = json.loads(payload)
    task = TasksSchema(**json_payload)
    event_type = 'calendar/task/deleted'
    await send_message(event_type=event_type, exchange_name=task.id, payload=json_payload)
    await delete_exchange(exchange_name=task.id)


@listener.listen_channel("event_user_join")
async def event_user_join(payload: str) -> None:
    json_payload = json.loads(payload)
    event_user = EventUserSchema(**json_payload)
    event_type = 'calendar/event/participant/joined'
    await create_exchange_and_bind_or_unbind_queue(exchange_name=event_user.event_id, queue_name=event_user.user_id)
    await send_message(event_type=event_type, exchange_name=event_user.event_id, payload=json_payload)


@listener.listen_channel("event_user_invite")
async def event_user_invite(payload: str) -> None:
    json_payload = json.loads(payload)
    event_user = EventUserSchema(**json_payload)
    event_type = 'calendar/event/participant/invited'
    await send_message(event_type=event_type, exchange_name=event_user.event_id, payload=json_payload)


@listener.listen_channel("event_user_delete")
async def event_user_delete(payload: str) -> None:
    json_payload = json.loads(payload)
    event_user = EventUserSchema(**json_payload)
    event_type = 'calendar/event/participant/deleted'
    await create_exchange_and_bind_or_unbind_queue(exchange_name=event_user.event_id,
                                                   queue_name=event_user.user_id,
                                                   unbind=True)
    await send_message(event_type=event_type, exchange_name=event_user.event_id, payload=json_payload)


@listener.listen_channel("event_transfer")
async def event_transfer(payload: str) -> None:
    json_payload = json.loads(payload)
    event = EventsSchema(**json_payload)
    event_type = 'calendar/event/owner/transfered'
    await create_exchange_and_bind_or_unbind_queue(exchange_name=event.id, queue_name=event.owner_id)
    await send_message(event_type=event_type, exchange_name=event.id, payload=json_payload)


@listener.listen_channel("event_user_rejected")
async def event_user_rejected(payload: str) -> None:
    json_payload = json.loads(payload)
    event_user = EventUserSchema(**json_payload)
    event_type = 'calendar/event/participant/rejected'
    await create_exchange_and_bind_or_unbind_queue(exchange_name=event_user.event_id,
                                                   queue_name=event_user.user_id,
                                                   unbind=True)
    await send_message(event_type=event_type, exchange_name=event_user.event_id, payload=json_payload)


@listener.listen_channel("event_user_like")
async def event_user_liked(payload: str) -> None:
    json_payload = json.loads(payload)
    event_user = EventUserSchema(**json_payload)
    event_type = 'calendar/event/liked'
    await send_message(event_type=event_type, exchange_name=event_user.event_id, payload=json_payload)


@listener.listen_channel("event_user_unlike")
async def event_user_unliked(payload: str) -> None:
    json_payload = json.loads(payload)
    event_user = EventUserSchema(**json_payload)
    event_type = 'calendar/event/unliked'
    await send_message(event_type=event_type, exchange_name=event_user.event_id, payload=json_payload)


@listener.listen_channel("event_user_remind")
async def event_user_remind(payload: str) -> None:
    json_payload = json.loads(payload)
    event_user = EventUserSchema(**json_payload)
    event_type = 'calendar/event/remind'
    await send_message(event_type=event_type, exchange_name=event_user.event_id, payload=json_payload)


@listener.listen_channel("event_user_unremind")
async def event_user_unremind(payload: str) -> None:
    json_payload = json.loads(payload)
    event_user = EventUserSchema(**json_payload)
    event_type = 'calendar/event/unremind'
    await send_message(event_type=event_type, exchange_name=event_user.event_id, payload=json_payload)


@listener.listen_channel("event_user_hidden")
async def event_user_hidden(payload: str) -> None:
    json_payload = json.loads(payload)
    event_user = EventUserSchema(**json_payload)
    event_type = 'calendar/event/hidden'
    await send_message(event_type=event_type, exchange_name=event_user.event_id, payload=json_payload)


@listener.listen_channel("event_user_unhidden")
async def event_user_unhidden(payload: str) -> None:
    json_payload = json.loads(payload)
    event_user = EventUserSchema(**json_payload)
    event_type = 'calendar/event/unhidden'
    await send_message(event_type=event_type, exchange_name=event_user.event_id, payload=json_payload)


@listener.listen_channel("task_user_like")
async def task_user_like(payload: str) -> None:
    json_payload = json.loads(payload)
    task_user = TaskUserSchema(**json_payload)
    event_type = 'calendar/task/liked'
    await send_message(event_type=event_type, exchange_name=task_user.task_id, payload=json_payload)


@listener.listen_channel("task_user_unlike")
async def task_user_unlike(payload: str) -> None:
    json_payload = json.loads(payload)
    task_user = TaskUserSchema(**json_payload)
    event_type = 'calendar/task/unliked'
    await send_message(event_type=event_type, exchange_name=task_user.task_id, payload=json_payload)


@listener.listen_channel("task_user_done")
async def task_user_done(payload: str) -> None:
    json_payload = json.loads(payload)
    task_user = TaskUserSchema(**json_payload)
    event_type = 'calendar/task/checked'
    await send_message(event_type=event_type, exchange_name=task_user.task_id, payload=json_payload)


@listener.listen_channel("task_user_undone")
async def task_user_undone(payload: str) -> None:
    json_payload = json.loads(payload)
    task_user = TaskUserSchema(**json_payload)
    event_type = 'calendar/task/unchecked'
    await send_message(event_type=event_type, exchange_name=task_user.task_id, payload=json_payload)

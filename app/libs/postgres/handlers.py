from typing import List

from fastapi import HTTPException, status
from pydantic import UUID4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import exists
from app.libs.postgres.models import Event
from app.schemas.calendar_schemas import EventsSchema
from app.settings import get_settings

settings = get_settings()

connection = f'{settings.postgres_settings.postgres_server}{settings.postgres_settings.postgres_db}'


def insert_event(event: EventsSchema,
                 owner_id: UUID4):
    engine = create_engine(connection)
    Session = sessionmaker(bind=engine)
    session = Session()
    new_event = Event(id=event.id,
                      title=event.title,
                      description=event.description,
                      from_datetime=event.from_datetime,
                      to_datetime=event.to_datetime,
                      location=event.location,
                      is_online_event=event.is_online_event,
                      photo_uri=event.photo_uri,
                      repeat_mode=event.repeat_mode.value,
                      repeat_days=event.repeat_days,
                      repeat_end=event.repeat_end,
                      source=event.source,
                      owner_id=owner_id,
                      )
    try:
        session.add(new_event)
        session.commit()
    finally:
        session.close()


def get_event(event_id: UUID4) -> Event:
    engine = create_engine(connection)
    Session = sessionmaker(bind=engine)
    session = Session()
    event = session.query(Event).filter(Event.id == event_id).first()
    session.close()
    return event


def get_events(owner_id) -> List[Event]:
    engine = create_engine(connection)
    Session = sessionmaker(bind=engine)
    session = Session()
    events = session.query(Event).filter(Event.owner_id == owner_id).all()
    session.close()
    return events

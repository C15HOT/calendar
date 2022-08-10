from pydantic import BaseModel
from pydantic.types import UUID4
from datetime import datetime, date

from enum import Enum

class Gender(Enum):
    male = 'male'
    female = 'female'
    other = 'other'

class Users(BaseModel):
    id: UUID4
    username: str
    firstname: str
    lastname: str
    middlename: str
    gender: Gender.value
    birthday: date
    photo_uri: str
    join_data: date
    is_online: bool
    last_seen: datetime

class EventRepeatMode(Enum):
    no_repeat = 'no_repeat'
    interval = 'interval'
    week_days = 'week_days'

class Tasks(BaseModel):
    id: UUID4
    done: bool
    title: str
    created_at: datetime
    edited_at: datetime
    description: str
    icon: str
    from_datetime: datetime
    to_datetime: datetime
    location: str
    repeat_mode: EventRepeatMode
    repeat_day: str
    repeat_end: date


class Events(BaseModel):
    id: UUID4
    title: str
    created_at: datetime
    edited_at: datetime
    description: str
    icon: str
    from_datetime: datetime
    to_datetime: datetime
    location: str
    is_online_event: bool
    repeat_mode: EventRepeatMode
    repeat_day: str
    repeat_end: date
    source: str
    owner_id: UUID4 #Возможно юзер

class TaskUser(BaseModel):
    task_id: UUID4
    user_id: UUID4

class EventUser(BaseModel):
    event_id: UUID4
    user_id: UUID4
    is_viewed: bool
    is_accepted: bool
    is_hidden: bool
    is_reminder_on: bool

class EventTag(BaseModel):
    event_id: UUID4
    tag_id: UUID4

class Tags(BaseModel):
    id: UUID4
    title: str
    description: str

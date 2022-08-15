from typing import List, Optional

from pydantic import BaseModel, Field
from pydantic.types import UUID4
from datetime import datetime, date
import uuid
from enum import Enum


class Rights(Enum):
    owner = 'rwsd'
    close = '----'
    public = 'r-s-'
    moderator = 'rws-'
    read_only = 'r---'

    @classmethod
    def get_rights(cls, value):
        return [x.value for x in cls if x.value == value][0]


class Gender(Enum):
    male = 'male'
    female = 'female'
    other = 'other'

class UsersSchema(BaseModel):
    id: UUID4
    username: str
    firstname: str
    lastname: str
    middlename: str
    gender: Gender
    birthday: date
    photo_uri: str
    join_data: date
    is_online: bool
    last_seen: datetime

class EventRepeatMode(Enum):
    no_repeat = 'no_repeat'
    interval = 'interval'
    week_days = 'week_days'

class TasksSchema(BaseModel):
    id: UUID4 = Field(default_factory=uuid.uuid4)
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
    repeat_days: str
    repeat_end: date


class EventsSchema(BaseModel):
    id: UUID4 = Field(default_factory=uuid.uuid4)
    title: str
    created_at: datetime
    edited_at: datetime = None
    description: str
    from_datetime: datetime
    to_datetime: datetime
    location: str
    is_online_event: bool
    photo_uri: List[str]
    repeat_mode: EventRepeatMode
    repeat_days: str
    repeat_end: date
    source: str
    owner_id: Optional[UUID4]
    default_permissions: str = 'r-s-'


class TaskUserSchema(BaseModel):
    task_id: UUID4
    user_id: UUID4

class EventUserSchema(BaseModel):
    event_id: UUID4
    user_id: UUID4
    permissions: str
    is_viewed: bool = False
    is_accepted: bool = None
    is_hidden: bool = False
    is_remider_on: bool = True

class EventTagSchema(BaseModel):
    event_id: UUID4
    tag_id: UUID4

class TagsSchema(BaseModel):
    id: UUID4
    title: str
    description: str


# coding: utf-8
from sqlalchemy import ARRAY, BigInteger, Boolean, Column, Date, DateTime, Enum, ForeignKey, ForeignKeyConstraint, Integer, JSON, String, Table, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


class Attachment(Base):
    __tablename__ = 'attachments'

    id = Column(UUID, primary_key=True)
    type = Column(Enum('link', 'image', 'document', 'other', 'message', 'note', 'event', 'news', name='ATTACHMENT_TYPE'), nullable=False)
    created_at = Column(DateTime)
    edited_at = Column(DateTime)
    uri = Column(String, nullable=False)
    default_permissions = Column(String(4), server_default=text("'r-s-'::character varying"))

    workspaces = relationship('Workspace', secondary='workspace_attachment')


class Chat(Base):
    __tablename__ = 'chats'

    id = Column(UUID, primary_key=True)
    type = Column(Enum('global', 'avatar', 'personal', 'group', name='CHAT_TYPE'), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=text("now()"))


class Interview(Base):
    __tablename__ = 'interviews'

    id = Column(UUID, primary_key=True)
    title = Column(String, nullable=False, unique=True)
    description = Column(String)
    photo_uri = Column(String, server_default=text("'random generated'::character varying"))


class News(Base):
    __tablename__ = 'news'

    id = Column(UUID, primary_key=True)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    photo_uri = Column(ARRAY(String()))
    source_url = Column(String)

    tags = relationship('Tag', secondary='news_tag')


class Organization(Base):
    __tablename__ = 'organizations'

    id = Column(UUID, primary_key=True)
    type = Column(Enum('university', name='ORGANIZATION_TYPE'), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String)
    photo_uri = Column(String, server_default=text("'random generated'::character varying"))
    country_iso = Column(String(2))
    city = Column(String)
    url = Column(String)


class SchemaMigration(Base):
    __tablename__ = 'schema_migrations'

    version = Column(BigInteger, primary_key=True)
    dirty = Column(Boolean, nullable=False)


class Tag(Base):
    __tablename__ = 'tags'

    id = Column(UUID, primary_key=True)
    title = Column(String, nullable=False, unique=True)
    description = Column(String)


class Task(Base):
    __tablename__ = 'tasks'

    id = Column(UUID, primary_key=True)
    done = Column(Boolean, server_default=text("false"))
    title = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    edited_at = Column(DateTime, nullable=False)
    description = Column(String)
    icon = Column(String)
    from_datetime = Column(DateTime)
    to_datetime = Column(DateTime)
    location = Column(String)
    repeat_mode = Column(Enum('no_repeat', 'interval', 'week_days', name='EVENT_REPEAT_MODE'), nullable=False)
    repeat_days = Column(String, comment='if repeat_mode == week_days only')
    repeat_end = Column(Date)

    users = relationship('User', secondary='task_user')


class User(Base):
    __tablename__ = 'users'

    id = Column(UUID, primary_key=True)
    username = Column(String, nullable=False, unique=True)
    firstname = Column(String, nullable=False)
    lastname = Column(String, nullable=False)
    middlename = Column(String)
    gender = Column(Enum('male', 'female', 'other', name='GENDER_TYPE'), nullable=False)
    birthday = Column(Date, nullable=False)
    photo_uri = Column(String, nullable=False)
    join_date = Column(Date, nullable=False, server_default=text("now()"))
    is_online = Column(Boolean, nullable=False, server_default=text("false"))
    last_seen = Column(DateTime, nullable=False, server_default=text("now()"))


class UserIntegration(User):
    __tablename__ = 'user_integrations'

    id = Column(ForeignKey('users.id'), primary_key=True)
    priority_messenger = Column(Enum('telegram', 'vk', 'email', name='MESSENGER'))
    vk_id = Column(String)
    telegram_id = Column(String)
    email = Column(String)


class UserSetting(User):
    __tablename__ = 'user_settings'

    id = Column(ForeignKey('users.id'), primary_key=True)
    allow_avatar_suggestions = Column(Boolean, server_default=text("false"))
    allow_sync_calendar = Column(Boolean, server_default=text("false"))
    allow_profile_sharing = Column(Boolean, server_default=text("false"))


class AttachmentUser(Base):
    __tablename__ = 'attachment_user'

    attachment_id = Column(ForeignKey('attachments.id'), primary_key=True, nullable=False)
    user_id = Column(ForeignKey('users.id'), primary_key=True, nullable=False)
    permissions = Column(String(4))

    attachment = relationship('Attachment')
    user = relationship('User')


class ChatUser(Base):
    __tablename__ = 'chat_user'

    chat_id = Column(ForeignKey('chats.id'), primary_key=True, nullable=False)
    user_id = Column(ForeignKey('users.id'), primary_key=True, nullable=False)
    permissions = Column(String(8))
    last_read_id = Column(Integer, server_default=text("'-1'::integer"))
    is_muted = Column(Boolean, server_default=text("false"))
    mute_end = Column(Date)
    is_left = Column(Boolean, server_default=text("false"))

    chat = relationship('Chat')
    user = relationship('User')


class Event(Base):
    __tablename__ = 'events'

    id = Column(UUID(as_uuid=True), primary_key=True)
    title = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=text("now()"))
    edited_at = Column(DateTime)
    description = Column(String)
    from_datetime = Column(DateTime, nullable=False)
    to_datetime = Column(DateTime, nullable=False)
    location = Column(String, nullable=False)
    is_online_event = Column(Boolean, nullable=False)
    photo_uri = Column(ARRAY(String()))
    repeat_mode = Column(Enum('no_repeat', 'interval', 'week_days', name='EVENT_REPEAT_MODE'), nullable=False)
    repeat_days = Column(String)
    repeat_end = Column(Date)
    source = Column(String)
    owner_id = Column(ForeignKey('users.id'))

    owner = relationship('User')
    tags = relationship('Tag', secondary='event_tag')


t_group_chats = Table(
    'group_chats', metadata,
    Column('id', ForeignKey('chats.id')),
    Column('name', String, nullable=False, unique=True),
    Column('title', String),
    Column('description', String),
    Column('photo_uri', String, server_default=text("'random generated'::character varying")),
    Column('default_permissions', String(8), server_default=text("'rwspi---'::character varying")),
    Column('owner_id', ForeignKey('users.id'))
)


class InterviewUser(Base):
    __tablename__ = 'interview_user'

    interview_id = Column(ForeignKey('interviews.id'), primary_key=True, nullable=False)
    user_id = Column(ForeignKey('users.id'), primary_key=True, nullable=False)
    iteration = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    answer = Column(JSON, nullable=False)
    result = Column(JSON, nullable=False)

    interview = relationship('Interview')
    user = relationship('User')


class Message(Base):
    __tablename__ = 'messages'
    __table_args__ = (
        ForeignKeyConstraint(['chat_id', 'reply_to'], ['messages.chat_id', 'messages.message_id']),
    )

    chat_id = Column(ForeignKey('chats.id'), primary_key=True, nullable=False)
    message_id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    user_id = Column(ForeignKey('users.id'), nullable=False)
    reply_to = Column(Integer)
    created_at = Column(DateTime, nullable=False, server_default=text("now()"))
    edited_at = Column(DateTime)
    content = Column(String(1024))
    attachments = Column(ARRAY(Integer()))
    is_pinned = Column(Boolean, server_default=text("false"))

    chat = relationship('Message', remote_side=[chat_id, message_id])
    chat1 = relationship('Chat')
    user = relationship('User')


t_news_tag = Table(
    'news_tag', metadata,
    Column('news_id', ForeignKey('news.id'), primary_key=True, nullable=False),
    Column('tag_id', ForeignKey('tags.id'), primary_key=True, nullable=False)
)


t_news_user = Table(
    'news_user', metadata,
    Column('news_id', ForeignKey('news.id')),
    Column('user_id', ForeignKey('users.id')),
    Column('is_viewed', Boolean, server_default=text("false")),
    Column('is_liked', Boolean, server_default=text("false")),
    Column('is_hidden', Boolean, server_default=text("false"))
)


class Note(Base):
    __tablename__ = 'notes'

    id = Column(UUID, primary_key=True)
    is_diary = Column(Boolean, nullable=False)
    title = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    edited_at = Column(DateTime, nullable=False)
    content = Column(String)
    owner_id = Column(ForeignKey('users.id'))
    attachments = Column(ARRAY(UUID()))
    default_permissions = Column(String(4), server_default=text("'----'::character varying"))

    owner = relationship('User')


class OrganizationRole(Base):
    __tablename__ = 'organization_roles'

    organization_id = Column(ForeignKey('organizations.id'), primary_key=True, nullable=False)
    role_id = Column(UUID, primary_key=True, nullable=False)
    title = Column(String)
    description = Column(String)

    organization = relationship('Organization')


class PersonalChat(Base):
    __tablename__ = 'personal_chats'

    id = Column(UUID, primary_key=True)
    chat_id = Column(ForeignKey('chats.id'))

    chat = relationship('Chat')


class Subscriber(Base):
    __tablename__ = 'subscribers'

    user_id = Column(ForeignKey('users.id'), primary_key=True, nullable=False)
    subscriber_id = Column(ForeignKey('users.id'), primary_key=True, nullable=False)
    subscribtion_date = Column(Date, nullable=False, server_default=text("now()"))

    subscriber = relationship('User', primaryjoin='Subscriber.subscriber_id == User.id')
    user = relationship('User', primaryjoin='Subscriber.user_id == User.id')


t_task_user = Table(
    'task_user', metadata,
    Column('task_id', ForeignKey('tasks.id'), primary_key=True, nullable=False),
    Column('user_id', ForeignKey('users.id'), primary_key=True, nullable=False)
)


class Workspace(Base):
    __tablename__ = 'workspaces'

    id = Column(UUID, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    title = Column(String)
    description = Column(String)
    photo_uri = Column(String, server_default=text("'random generated'::character varying"))
    is_private = Column(Boolean, server_default=text("true"))
    default_permissions = Column(String(8), server_default=text("'r-------'::character varying"))
    owner_id = Column(ForeignKey('users.id'))

    owner = relationship('User')


t_event_tag = Table(
    'event_tag', metadata,
    Column('event_id', ForeignKey('events.id'), primary_key=True, nullable=False),
    Column('tag_id', ForeignKey('tags.id'), primary_key=True, nullable=False)
)


class EventUser(Base):
    __tablename__ = 'event_user'

    event_id = Column(ForeignKey('events.id'), primary_key=True, nullable=False)
    user_id = Column(ForeignKey('users.id'), primary_key=True, nullable=False)
    is_viewed = Column(Boolean, server_default=text("false"))
    is_accepted = Column(Boolean, server_default=text("false"))
    is_hidden = Column(Boolean, server_default=text("false"))
    is_remider_on = Column(Boolean, server_default=text("true"))

    event = relationship('Event')
    user = relationship('User')


t_note_user = Table(
    'note_user', metadata,
    Column('note_id', ForeignKey('notes.id')),
    Column('user_id', ForeignKey('users.id')),
    Column('is_viewed', Boolean, server_default=text("false")),
    Column('is_liked', Boolean, server_default=text("false")),
    Column('is_hidden', Boolean, server_default=text("false")),
    Column('permissions', String(4))
)


class OrganizationUser(Base):
    __tablename__ = 'organization_user'
    __table_args__ = (
        ForeignKeyConstraint(['organization_id', 'role_id'], ['organization_roles.organization_id', 'organization_roles.role_id']),
    )

    organization_id = Column(ForeignKey('organizations.id'), primary_key=True, nullable=False)
    user_id = Column(ForeignKey('users.id'), primary_key=True, nullable=False)
    role_id = Column(UUID, nullable=False)
    assigned_on = Column(Date, nullable=False)
    discharged_on = Column(Date)

    organization = relationship('OrganizationRole')
    organization1 = relationship('Organization')
    user = relationship('User')


t_workspace_attachment = Table(
    'workspace_attachment', metadata,
    Column('workspace_id', ForeignKey('workspaces.id'), primary_key=True, nullable=False),
    Column('attachment_id', ForeignKey('attachments.id'), primary_key=True, nullable=False)
)


class WorkspaceUser(Base):
    __tablename__ = 'workspace_user'

    workspace_id = Column(ForeignKey('workspaces.id'), primary_key=True, nullable=False)
    user_id = Column(ForeignKey('users.id'), primary_key=True, nullable=False)
    permissions = Column(String(8))

    user = relationship('User')
    workspace = relationship('Workspace')

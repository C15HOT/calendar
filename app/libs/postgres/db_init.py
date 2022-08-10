from sqlalchemy import create_engine
from app.settings import get_settings
from models import Base

settings = get_settings()


if __name__=='__main__':

    CONNECTION = f'{settings.postgres_settings.postgres_server}/{settings.postgres_settings.postgres_db}'
    # CONNECTION = 'postgresql+psycopg2://calendar:calendar@localhost/calendar'
    engine = create_engine(CONNECTION)
    Base.metadata.create_all(engine)

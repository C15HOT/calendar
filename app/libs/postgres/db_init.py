from sqlalchemy import create_engine
from app.settings import get_settings
from models import Base

settings = get_settings()


if __name__=='__main__':


    CONNECTION = 'postgresql+psycopg2://calendar:calendar@localhost/calendar'
    engine = create_engine(CONNECTION)
    Base.metadata.create_all(engine)

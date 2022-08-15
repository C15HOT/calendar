from sqlalchemy import create_engine
from models import Base



if __name__=='__main__':


    CONNECTION = 'postgresql+psycopg2://calendar:calendar@localhost/calendar'
    engine = create_engine(CONNECTION)
    Base.metadata.create_all(engine)

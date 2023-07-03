import asyncio
import logging
from datetime import datetime
from sqlalchemy import Column, Integer, String, select, delete, Float, create_engine, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker, DeclarativeBase

from common.yaml_config import YamlConfig

logger = logging.getLogger(__name__)
yc = YamlConfig()
config = yc.config_open()
print(config.get('active_engine'))
if config['databases']['active_engine'] == 'postgres':
    username = config['databases']['postgres']['postgres_user']
    password = config['databases']['postgres']['postgres_password']
    server_address = config['databases']['postgres']["postgres_address"]
    server_port = config['databases']['postgres']["postgres_port"]
    postgres_database = config['databases']['postgres']["postgres_database"]

    engine = create_engine(f"postgresql+psycopg2://{username}:{password}@{server_address}/{postgres_database}", echo=False)
    Session = sessionmaker(engine)
    
elif config['databases']['active_engine'] == 'sqlite':
    engine = create_engine("sqlite:///base.db", echo=False)
    Session = sessionmaker(bind=engine)
else:
    logger.error('Invalid database engine, must be postgres or sqlite, by default use sqlite')
    engine = create_engine("sqlite:///base.db", echo=False)
    Session = sessionmaker(bind=engine)
# Base = declarative_base()

logger.info(f"current database engine is {config['databases']['active_engine']}")

GLOBAL_COUNT: int = 0

class Base(DeclarativeBase):
    pass

class Buffer(Base):
    __tablename__ = "buffer"

    id = Column(Integer, primary_key=True, autoincrement=True)
    message = Column(String)
    # status = Column(String)

    def __init__(self, message):
        self.message = message
    #     self.status = status

class DatabaseVersion(Base):
    __tablename__ = "database_version"
    id = Column(Integer, primary_key=True)
    current_db_version = Column(String)
    

class Devices(Base):
    __tablename__ = "devices"
    id = Column(Integer, primary_key=True, autoincrement=True)
    ppk_id = Column(String)
    last_test = Column(Float)


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True)
    protocol_number = Column(Integer)
    receiver_number = Column(Integer)
    line_number = Column(Integer)
    format_identifier = Column(String)
    subscriber_id = Column(String)
    event_identifier = Column(String)
    event_code = Column(String)
    group_number = Column(String)
    zone_or_sensor_number = Column(String)
    event_description = Column(String)
    ip = Column(String)
    time = Column(String)


def create_buffer_table_sync():
    with engine.begin() as conn:
        Base.metadata.create_all(conn)

def check_database_verison():
    with Session() as session:
        query = session.execute(select(DatabaseVersion).limit(1)).scalar
        q = query.db_version
        for q in query: 
            if q is None:
                new_database_version = DatabaseVersion(current_db_version = 1)
                session.add(new_database_version)
                session.commit()


def insert_into_buffer_sync(messages):
    buffer_objs = [Buffer(message) for message in messages]
    with Session() as session:
        session.add_all(buffer_objs)
        session.commit()
        
# async def insert_into_buffer_async(messages):
#     buffer_objs = [Buffer(message) for message in messages]
#     async with Session() as session:
#         session.add_all(buffer_objs)
#         await session.commit()

def select_from_buffer_sync():
    new_list = []
    with Session() as session:
        # count = session.query(func.count()).select_from(Buffer).scalar()
        result = session.execute(select(Buffer).limit(300)).scalars()

        if result:
            for data in result:
                new_list.append([data.id, data.message])
        session.close()
    return new_list


def delete_from_buffer_sync(id):
    with Session() as session:
        session.execute(delete(Buffer).where(Buffer.id == id))
        session.commit()


def insert_event_sync(sg_dict, ip):
    protocol_number = sg_dict["protocol_number"]
    receiver_number = sg_dict["receiver_number"]
    line_number = sg_dict["line_number"]
    format_identifier = sg_dict["format_identifier"]
    subscriber_id = sg_dict["subscriber_id"]
    event_identifier = sg_dict["event_identifier"]
    event_code = sg_dict["event_code"]
    group_number = sg_dict["group_number"]
    zone_or_sensor_number = sg_dict["zone_or_sensor_number"]
    event_description = sg_dict["event_description"]
    ip = f"{ip[0]}:{ip[1]}"
    current_time = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")

    with Session() as session:
        new_event = Event(
            protocol_number=protocol_number,
            receiver_number=receiver_number,
            line_number=line_number,
            format_identifier=format_identifier,
            subscriber_id=subscriber_id,
            event_identifier=event_identifier,
            event_code=event_code,
            group_number=group_number,
            zone_or_sensor_number=zone_or_sensor_number,
            event_description=event_description,
            ip=ip,
            time=current_time,
        )
        session.add(new_event)
        session.commit()


# check_database_verison()
import asyncio
import logging
from datetime import datetime
from sqlalchemy import Column, Integer, String, select, delete, Float, create_engine, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

logger = logging.getLogger(__name__)

engine = create_engine("postgresql+psycopg2://postgres:Ap15021991@localhost/rdb", echo=False)
async_session = sessionmaker(engine)
Base = declarative_base()

GLOBAL_COUNT: int = 0


class Buffer(Base):
    __tablename__ = "buffer"

    id = Column(Integer, primary_key=True, autoincrement=True)
    message = Column(String)

    def __init__(self, message):
        self.message = message


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


def insert_into_buffer_sync(message):
    buffer_obj = Buffer(message)
    with async_session() as session:
        session.add(buffer_obj)
        session.commit()


def select_from_buffer_sync():
    new_list = []
    with async_session() as session:
        count = session.query(func.count()).select_from(Buffer).scalar()
        if count >= 300:
            result = session.execute(select(Buffer).limit(300)).scalars()
        else:
            result = session.execute(select(Buffer).limit(count)).scalars()

        if result:
            for data in result:
                new_list.append([data.id, data.message])
    return new_list


def delete_from_buffer_sync(id):
    with async_session() as session:
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

    with async_session() as session:
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

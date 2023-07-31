import asyncio
import logging
from datetime import datetime
import time
from sqlalchemy.exc import OperationalError
from sqlalchemy import (
    Column,
    Integer,
    String,
    select,
    delete,
    Float,
    create_engine,
    func,
)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker, DeclarativeBase
from PySide6.QtCore import QTimer

from common.yaml_config import YamlConfig

logger = logging.getLogger(__name__)

yc = YamlConfig()
config = yc.config_open()


def create_engine_and_session():
    retry_delay = 2
    current_retry = 0
    try:
        if config["databases"]["active_engine"] == "postgres":
            username = config["databases"]["postgres"]["postgres_user"]
            password = config["databases"]["postgres"]["postgres_password"]
            server_address = config["databases"]["postgres"]["postgres_address"]
            server_port = config["databases"]["postgres"]["postgres_port"]
            postgres_database = config["databases"]["postgres"]["postgres_database"]

            engine = create_engine(
                f"postgresql+psycopg2://{username}:{password}@{server_address}/{postgres_database}",
                echo=False,
                pool_pre_ping=True,
            )
            Session = sessionmaker(engine)
            return engine, Session

        elif config["databases"]["active_engine"] == "sqlite":
            engine = create_engine("sqlite:///base.db", echo=False, pool_pre_ping=True)
            Session = sessionmaker(bind=engine)
            return engine, Session

        else:
            logger.error(
                "Invalid database engine, must be postgres or sqlite, by default use sqlite"
            )
            engine = create_engine("sqlite:///base.db", echo=False, pool_pre_ping=True)
            Session = sessionmaker(bind=engine)
            return engine, Session
    except Exception as err:
        logger.debug(
            f"Connection to database not exist, reconnecting in {retry_delay ** current_retry}"
        )
        QTimer.singleShot(
            retry_delay**current_retry, lambda: create_engine_and_session()
        )()
        logger.debug(err)
        current_retry += 1
        create_engine_and_session()


# Base = declarative_base()

logger.info(f"current database engine is {config['databases']['active_engine']}")

GLOBAL_COUNT: int = 0
db_engine, db_Session = create_engine_and_session()


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


def create_buffer_table_sync(engine):
    with engine.begin() as conn:
        Base.metadata.create_all(conn)


def check_database_verison(Session):
    with Session() as session:
        query = session.execute(select(DatabaseVersion).limit(1)).scalar
        q = query.db_version
        for q in query:
            if q is None:
                new_database_version = DatabaseVersion(current_db_version=1)
                session.add(new_database_version)
                session.commit()
                session.close()


def insert_into_buffer_sync(Session, messages):
    buffer_objs = [Buffer(message) for message in messages]
    with Session() as session:
        session.add_all(buffer_objs)
        session.commit()
        session.close()


# async def insert_into_buffer_async(messages):
#     buffer_objs = [Buffer(message) for message in messages]
#     async with Session() as session:
#         session.add_all(buffer_objs)
#         await session.commit()


def select_from_buffer_sync(Session):
    new_list = []
    with Session() as session:
        # count = session.query(func.count()).select_from(Buffer).scalar()
        result = session.execute(select(Buffer).limit(300)).scalars()

        if result:
            for data in result:
                new_list.append([data.id, data.message])
        session.close()
    return new_list


def delete_from_buffer_sync(Session, id):
    with Session() as session:
        session.execute(delete(Buffer).where(Buffer.id == id))
        session.commit()
        session.close()


def insert_event_sync(sg_dict, ip, Session):
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
        session.close()


create_buffer_table_sync(db_engine)
# check_database_verison()


def check_connection(engine):
    try:
        with engine.begin() as conn:
            conn.scalar(select(1))
            conn.close()
            return True
    except OperationalError:
        return False

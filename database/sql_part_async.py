import asyncio
import logging
from datetime import datetime
from sqlalchemy import Column, Integer, String, select, delete, Float, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker, DeclarativeBase

from common.yaml_config import YamlConfig

logger = logging.getLogger(__name__)
yc = YamlConfig()
config = yc.config_open()
print(config.get("active_engine"))
if config["databases"]["active_engine"] == "postgres":
    username = config["databases"]["postgres"]["postgres_user"]
    password = config["databases"]["postgres"]["postgres_password"]
    server_address = config["databases"]["postgres"]["postgres_address"]
    server_port = config["databases"]["postgres"]["postgres_port"]
    postgres_database = config["databases"]["postgres"]["postgres_database"]

    engine = create_async_engine(
        f"postgresql+psycopg2://{username}:{password}@{server_address}/{postgres_database}",
        echo=False,
    )
    Session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

elif config["databases"]["active_engine"] == "sqlite":
    engine = create_async_engine("sqlite+aiosqlite:///base.db", echo=False)
    Session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    session = Session()
else:
    logger.error(
        "Invalid database engine, must be postgres or sqlite, by default use sqlite"
    )
    engine = create_async_engine("sqlite+aiosqlite:///base.db", echo=False)
    Session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass


logger.info(f"current database engine is {config['databases']['active_engine']}")


class Buffer(Base):
    __tablename__ = "buffer"

    id = Column(Integer, primary_key=True, autoincrement=True)
    message = Column(String)

    def __init__(self, message):
        self.message = message


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


async def create_buffer_table_async():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def check_database_version():
    async with Session() as session:
        query = await session.execute(select(DatabaseVersion).limit(1))
        db_version = query.scalar()
        if db_version is None:
            new_database_version = DatabaseVersion(current_db_version="1")
            session.add(new_database_version)
            await session.commit()


async def insert_into_buffer_async(messages):
    buffer_objs = [Buffer(message) for message in messages]
    async with Session() as session:
        session.add_all(buffer_objs)
        await session.commit()


async def select_from_buffer_async():
    new_list = []
    async with Session() as session:
        result = await session.execute(select(Buffer).limit(300))
        buffers = result.scalars().all()
        if buffers:
            for buffer in buffers:
                new_list.append([buffer.id, buffer.message])
        print(len(new_list))
    return new_list


async def delete_from_buffer_async(id):
    async with AsyncSession(engine) as session:
        await session.execute(delete(Buffer).where(Buffer.id == id))
        await session.commit()
        await session.close()
        await engine.dispose()


async def insert_event_async(sg_dict, ip):
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

    async with Session() as session:
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
        await session.commit()

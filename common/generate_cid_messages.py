import asyncio
import logging
import random

from surguad_codes import *

logger = logging.getLogger(__name__)


async def establish_connection(timeout=3):
    server_host = 'localhost'
    server_port = 5551

    """Підключення до сервера з можливістю встановлення таймауту"""
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(server_host, server_port),
            timeout=timeout,
        )
        logger.info(f"Connected to {server_host}:{server_port}")

        return reader, writer

    except asyncio.TimeoutError as ex:
        logger.error(
            f"Connection to {server_host}:{server_port} timed out"
        )
        logger.info("Reconnecting after 10 seconds")
        await asyncio.sleep(10)
        await establish_connection(3)
    except OSError as e:
        logger.exception(
            f"Error connecting to {server_host}:{server_port}: {e}"
        )
        await asyncio.sleep(10)
        await establish_connection(3)

async def send_message_to_server(message_count):
    try:
        reader, writer = await establish_connection(3)
        for i in range(message_count):
            data = generate_message()
            writer.write(data)
            await writer.drain()
            try:
                 response = await asyncio.wait_for(reader.read(1024), timeout=1024)
            except ConnectionResetError as err:
                logger.exception(err)
                writer.close()
            # if response == MSG_ACK:
            # logger.info(f"Sent data: {data}, Received response: {response}")
            await asyncio.sleep(0)
    except Exception:
        logger.exception("error")
        await asyncio.sleep(10)

surgard_codes = [*event_guard, *event_disguard, *event_alarm, *event_ok, *other_events]

count = 0

def generate_message():
    global count
    ppk_number = random.randint(1000, 9999)
    event_code = random.choice(surgard_codes)
    event_type = random.choice(["E", "R"])

    message = f'5010 18{ppk_number}{event_code}00000\x14'.encode()
    print(f'{count}) {message}')
    count +=1
    return message


asyncio.run(send_message_to_server(10000000))
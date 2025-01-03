import asyncio
import logging
import random
from surguad_codes import *

logger = logging.getLogger(__name__)

async def establish_connection(timeout=3):
    server_host = "10.32.1.110"
    server_port = 20005

    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(server_host, server_port),
            timeout=timeout,
        )
        logger.info(f"Connected to {server_host}:{server_port}")

        return reader, writer

    except asyncio.TimeoutError as ex:
        logger.error(f"Connection to {server_host}:{server_port} timed out")
        logger.info("Reconnecting after 10 seconds")
        await asyncio.sleep(10)
        return await establish_connection(3)
    except OSError as e:
        logger.exception(f"Error connecting to {server_host}:{server_port}: {e}")
        await asyncio.sleep(10)
        return await establish_connection(3)

async def send_message_to_server(reader, writer, message_count):
    for i in range(message_count):
        data = generate_message()
        print("Send message")
        writer.write(data)
        await writer.drain()
        print("Send message done")
        try:
            response = await asyncio.wait_for(reader.read(1024), timeout=1)
            logger.info(f"Recieve response: {response}")
        except ConnectionResetError as err:
            print("З'єднання розірвано")
        except asyncio.exceptions.CancelledError:
            print("Асинхронна задача скасована.")
            break
        except KeyboardInterrupt:
            print("Ви відмінили програму.")
            break
        except Exception as e:
            print(f"Виникла помилка: {e}")
        await asyncio.sleep(10)

async def send_heartbeat_to_server(reader, writer):
    while True:
        hex_string = "31 30 31 31 20 20 20 20 20 20 20 20 20 20 20 40 20 20 20 20 14"
        byte_data = bytes.fromhex(hex_string)

        writer.write(byte_data)
        await writer.drain()

        logger.info(f"Send heartbeat: {byte_data}")
        try:
            response = await asyncio.wait_for(reader.read(1024), timeout=1)
            logger.info(f"Recieve response: {response}")
        except ConnectionResetError as err:
            print("З'єднання розірвано")
        except asyncio.exceptions.CancelledError:
            print("Асинхронна задача скасована.")
            break
        except KeyboardInterrupt:
            print("Ви відмінили програму.")
            break
        except Exception as e:
            print(f"Виникла помилка: {e}")

        await asyncio.sleep(25)

surgard_codes = [*event_guard, *event_disguard, *event_alarm, *event_ok, *other_events]

count = 0

def generate_message():
    global count
    ppk_number = random.randint(1000, 9998)
    event_code = random.choice(surgard_codes)
    event_type = random.choice(["E", "R"])

    message = f"5010 181002{event_code}00000\x14".encode()
    print(f"{count}) {message}")
    count += 1
    return message

async def task():
    reader, writer = await establish_connection(3)
    await asyncio.gather(send_message_to_server(reader, writer, 10000000), send_heartbeat_to_server(reader, writer))

try:
    asyncio.run(task())
except (RuntimeError, RuntimeError):
    pass

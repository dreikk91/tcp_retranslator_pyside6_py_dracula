import asyncio
import logging
import random

from common.generate_cid_heartbeat import send_heartbeat_to_server
# from common.generate_cid_heartbeat import send_heartbeat_to_server
from surguad_codes import *

logger = logging.getLogger(__name__)


async def establish_connection(timeout=3):
    server_host = "10.32.1.110"
    server_port = 20005

    """Підключення до сервера з можливістю встановлення таймауту"""
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
        await establish_connection(3)
    except OSError as e:
        logger.exception(f"Error connecting to {server_host}:{server_port}: {e}")
        await asyncio.sleep(10)
        await establish_connection(3)


async def send_message_to_server(message_count):
    try:
        reader, writer = await establish_connection(3)

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
            # except Exception as e:
            #     print(f"Виникла помилка: {e}")
            # if response == MSG_ACK:
            # logger.info(f"Sent data: {data}, Received response: {response}")
            await asyncio.sleep(0.01)
    except Exception:
        logger.exception("error")
        await asyncio.sleep(10)


# async def send_heartbeat_to_server(message_count, reader, writer):
#     try:
#         # data = b'\x11\x02\n\n\x02\x02\x02\x02\x02\x02\x02\x02\x02\x02\x02\x02\x01\x02\x02\x02\x02\x11'
#         data = b'1011           @    \x14'
#         msg_count = 0
#         hex_string = "31 30 31 31 20 20 20 20 20 20 20 20 20 20 20 40 20 20 20 20 14"
#         byte_data = bytes.fromhex(hex_string)
#         text = byte_data.decode('ansi')
#
#         await asyncio.sleep(25)
#         writer.write(byte_data)
#         await writer.drain()
#         msg_count += 1
#
#         logger.info(f"Send heartbeat: {data}")
#         try:
#             response = await asyncio.wait_for(reader.read(1024), timeout=1024)
#             logger.info(f"Recieve response: {response}")
#         except ConnectionResetError as err:
#             print("З'єднання розірвано")
#         except asyncio.exceptions.CancelledError:
#             print("Асинхронна задача скасована.")
#
#         except KeyboardInterrupt:
#             print("Ви відмінили програму.")
#
#         except Exception as e:
#             print(f"Виникла помилка: {e}")
#         # await asyncio.sleep(30)
#     except Exception:
#         logger.exception("error")
#         await asyncio.sleep(10)


surgard_codes = [*event_guard, *event_disguard, *event_alarm, *event_ok, *other_events]

count = 0


def generate_message():
    global count
    # ppk_number = random.randint(1000, 9998)
    ppk_number = 1002
    event_code = random.choice(surgard_codes)
    event_type = random.choice(["E", "R"])

    # message = f"5010 18{ppk_number}{event_code}00000\x14".encode()
    message = f"5010 18{ppk_number}{event_code}00000\x14".encode()
    # if count + 1 // 2 == 0:
    print(f"{count}) {message}")
    count += 1
    return message


# try:
#     asyncio.run(send_message_to_server(10000000))
# except (RuntimeError, RuntimeError):
#     pass
async def task():
    tasks = []
    tasks.append(send_message_to_server(10000000))
    # tasks.append(send_heartbeat_to_server(10000000))
    group = asyncio.gather(*tasks)

    try:
        await group
    except asyncio.CancelledError:
        print("Tasks cancelled")


try:
    asyncio.run(task())
except (RuntimeError, RuntimeError):
    pass

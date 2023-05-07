import logging
import time

from common.logger_config import logger

def check_message_format(message):
    new_message = message.decode().rstrip()
    if len(new_message) >= 20:
        # if new_message[0] != '5' or new_message[0] != '1':
        #     logger.info(f'First symbol isnt 5 {new_message}')
        #     return False
        # else:
        return True


# noinspection SpellCheckingInspection
def split_message_stream(message):
    try:
        new_message = message.decode()
        splited_message_list = new_message.split('\x14')
        new_message_list = []
        for msg in splited_message_list:
            if len(msg) == 20:
                msg += '\x14'
                encoded_message = msg.encode()
                new_message_list.append(encoded_message)
        return new_message_list
    except UnicodeDecodeError as err:
        logger.debug(err)



class SurGard:
    def __init__(self, message):
        self.message = message.decode()

    def is_valid(self):
        try:
            if len(self.message) == 22:
                return False

            protocol_number = self.message[0:1]
            if protocol_number != "5":
                return False

            receiver_number = self.message[1:3]
            line_number = self.message[3]
            space_char = self.message[4]
            if space_char != " ":
                return False
            account_code = self.message[7:11]
            if len(account_code) == 4:
                account_code = self.message[7:11]
            else:
                return False
            event_code = self.message[11:15]
            area_number = self.message[15:17]

            zone_number = self.message[17:20]
            # terminator = self.message[21:]
            # if terminator != "\14":
            #     return False

            return True
        except IndexError as err:
            logger.error(err)
            return False


def split_data(data):
    data = data.split(b"5")
    return [b"5" + x for x in data[1:]]


def parse_surguard_message(message):
    # logger.info(message)
    protocol_number = message[0:1]
    receiver_number = message[1:3]
    line_number = message[3]
    format_identifier = message[5:7]
    subscriber_id = message[7:11]
    event_identifier = message[11]
    event_code = message[12:15]
    group_number = message[15:17]
    zone_or_sensor_number = message[17:20]

    if protocol_number == "5":
        if event_identifier == "E":
            event_description = "Event"
        elif event_identifier == "R":
            event_description = "Restore"
        else:
            event_description = "Unknown Event Identifier"

        return {
            "protocol_number": protocol_number,
            "receiver_number": receiver_number,
            "line_number": line_number,
            "format_identifier": format_identifier,
            "subscriber_id": subscriber_id,
            "event_identifier": event_identifier,
            "event_code": event_code,
            "group_number": group_number,
            "zone_or_sensor_number": zone_or_sensor_number,
            "event_description": event_description
        }
    elif protocol_number == "0":
        if message == "0x06":
            return "ACK - Confirmation of receipt from PC"
        elif message == "0x15":
            return "NACK - Rejection of receipt from PC"
        else:
            return "Unknown Protocol Number"
    else:
        return "Unknown Protocol Number"


async def calculate_speed(stream):
    start_time = time.monotonic()
    data_size = 0
    while True:
        data = await stream.read(1024)
        if not data:
            break
        data_size += len(data)
    elapsed_time = time.monotonic() - start_time
    if elapsed_time == 0:
        return 0.0
    else:
        received_speed = data_size / elapsed_time
        return received_speed

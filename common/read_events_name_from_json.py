# import json
import rapidjson as json
from typing import Dict, List, Optional, Union

from common.logger_config import logger


class ReadJson:
    def __init__(self, json_file):
        """_summary_

        Args:
            json_file (_type_): _description_
        """
        self.json_file:list = json_file
        self.cache:dict = {}
        self.result:str = ""
        self.messages_by_name:dict = {}

    def open_json(self):
        with open(self.json_file, "r", encoding="utf8") as f:
            json_file = f.read()
            json_dict = json.loads(json_file)
            return json_dict

    def create_messages_dict(self, message_dict):
        for message in message_dict:
            self.messages_by_name[message["name"]] = message

    async def find_event_name_by_type_and_code(
        self, event_dict:dict, message_dict:dict, event_type:str, event_code:str
    ):
        """_summary_

        Args:
            event_dict (dict): _description_
            message_dict (dict): _description_
            event_type (str): _description_
            event_code (str): _description_

        Returns:
            _type_: _description_
        """
        key = f"{event_type}_{event_code}"
        result = self.cache.get(key)
        print(result)
        print(self.cache)
        if result is not None:
            return result

        if not self.messages_by_name:
            self.create_messages_dict(message_dict)

        events_filtered = (
            event
            for event in event_dict
            if event["type_event"] == event_type and event["code"] == event_code
        )
        event_by_user = next(events_filtered, None)
        if event_by_user is not None:
            message = self.messages_by_name.get(event_by_user["event_by_user"])
            additional_type = event_by_user["additional_type"]
            is_alarm = event_by_user["is_alarm"]
            if message is not None:
                event_code_merged = f"{event_type}{event_code}"
                # result = await asyncio.to_thread(self._get_result, message, event_type, event_code, additional_type, is_alarm)
                result = {
                    "message": message["lang_uk"],
                    "event_code": event_code_merged,
                    "additional_type": additional_type,
                    "is_alarm": is_alarm,
                }
                self.cache[key] = result
                return result

    def _get_result(self, message, event_type, event_code, additional_type, is_alarm):
        logger.info(
            f"{message['lang_uk']} ({event_type}{event_code} {additional_type} {is_alarm})"
        )
        return f"{message['lang_uk']} ({event_type}{event_code} {additional_type} {is_alarm})"


class GetEventFromJson:
    def __init__(self, json_file: str) -> None:
        self.cache: dict = {}
        self.json_file: str = json_file
        self.event_list = self.open_json()


    def open_json(self) -> List[Dict[str, Optional[Union[str, int]]]]:
        with open(self.json_file, "r", encoding="utf8") as f:
            # json_file = f.read()
            event_list = json.loads(f.read())
            return event_list


    def read_events(self, event_code: str) -> Dict[str, Union[str, int]]:
        """_summary_

        Args:
            json_file (List[Dict[str, Optional[Union[str, int]]]]): _description_
            event_code (str): _description_

        Returns:
            Dict[str, Union[str, int]]: _description_
        """
        cached_event = self.cache.get(event_code)
        if cached_event:
            return cached_event

        event = next((data for data in self.event_list if data["contactId_code"] == event_code), None)
        if event is not None:
            self.cache[event_code] = event
            return event

        default_event:dict = {
            "contactId_code": event_code,
            "TypeCodeMes_UK": "unknown type",
            "CodeMes_UK": "Unknown message",
            "Zoneno": None,
            "AccessCode": None,
            "GroupSent": None,
            "AutoReset": None,
        }
        # self.cache[event_code] = default_event
        return default_event



get_event_from_json = GetEventFromJson("common/events.json")

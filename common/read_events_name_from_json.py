# import json
import logging
import os

import rapidjson as json
from typing import Dict, List, Optional, Union


logger = logging.getLogger(__name__)

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

base_dir = os.path.dirname(os.path.abspath(__file__))
events_file_path = os.path.join(base_dir, "events.json")

get_event_from_json = GetEventFromJson(events_file_path)

import asyncio
import json
import cProfile

import bson as bson
import msgpack as msgpack

from common.logger_config import logger


# class HashTable:
#     def __init__(self):
#         self.size = 11  # Розмір хеш-таблиці
#         self.slots = [None] * self.size  # Список для збереження ключів
#         self.data = [None] * self.size  # Список для збереження даних
#
#     def put(self, key, data):
#         """
#         Додає новий елемент до хеш-таблиці
#         """
#         # Обчислення хеш-коду ключа
#         hashvalue = self.hashfunction(hash(key), len(self.slots))
#
#         # Якщо слот з даною хеш-адресою вільний, додати ключ та дані
#         if self.slots[hashvalue] is None:
#             self.slots[hashvalue] = key
#             self.data[hashvalue] = data
#         # Якщо слот з даною хеш-адресою вже зайнятий і ключ співпадає, замінити дані
#         elif self.slots[hashvalue] == key:
#             self.data[hashvalue] = data
#         # Якщо слот з даною хеш-адресою зайнятий і ключ відрізняється, знайти вільний слот та додати елемент
#         else:
#             nextslot = self.rehash(hashvalue, len(self.slots))
#             while self.slots[nextslot] is not None and self.slots[nextslot] != key:
#                 nextslot = self.rehash(nextslot, len(self.slots))
#             if self.slots[nextslot] is None:
#                 self.slots[nextslot] = key
#                 self.data[nextslot] = data
#             else:
#                 self.data[nextslot] = data
#
#     def get(self, key):
#         """
#         Отримує значення по ключу
#         """
#         # Обчислення хеш-коду ключа
#         startslot = self.hashfunction(hash(key), len(self.slots))
#
#         data = None
#         stop = False
#         found = False
#         position = startslot
#         # Пошук елемента за ключем
#         while self.slots[position] is not None and not found and not stop:
#             if self.slots[position] == key:
#                 found = True
#                 data = self.data[position]
#             else:
#                 position = self.rehash(position, len(self.slots))
#                 if position == startslot:
#                     stop = True
#         return data
#
#     def hashfunction(self, key, size):
#         """
#         Обчислює хеш-код ключа
#         """
#         return key % size
#
#     def rehash(self, oldhash, size):
#         """
#         Генерує нову хеш-адресу, якщо попередня зайнята
#         """
#         return (oldhash + 1) % size


class ReadJson:
    def __init__(self, json_file):
        self.json_file = json_file
        self.cache = {}
        self.result = ''
        self.messages_by_name = {}

    def open_json(self):
        with open(self.json_file, "r", encoding="utf8") as f:
            json_file = f.read()
            json_dict = json.loads(json_file)
            return json_dict

    def create_messages_dict(self, message_dict):
        for message in message_dict:
            self.messages_by_name[message['name']] = message

    async def find_event_name_by_type_and_code(self, event_dict, message_dict, event_type, event_code):
        key = f"{event_type}_{event_code}"
        result = self.cache.get(key)
        print(result)
        print(self.cache)
        if result is not None:
            return result

        if not self.messages_by_name:
            self.create_messages_dict(message_dict)

        events_filtered = (event for event in event_dict if
                           event['type_event'] == event_type and event['code'] == event_code)
        event_by_user = next(events_filtered, None)
        if event_by_user is not None:
            message = self.messages_by_name.get(event_by_user['event_by_user'])
            additional_type = event_by_user['additional_type']
            is_alarm = event_by_user['is_alarm']
            if message is not None:
                event_code_merged = f'{event_type}{event_code}'
                # result = await asyncio.to_thread(self._get_result, message, event_type, event_code, additional_type, is_alarm)
                result = {'message': message['lang_uk'], 'event_code': event_code_merged, 'additional_type': additional_type, 'is_alarm': is_alarm }
                self.cache[key] = result
                return result

    def _get_result(self, message, event_type, event_code, additional_type, is_alarm):
        logger.info(f"{message['lang_uk']} ({event_type}{event_code} {additional_type} {is_alarm})")
        return f"{message['lang_uk']} ({event_type}{event_code} {additional_type} {is_alarm})"



    # def find_event_name_by_type_and_code2(self, event_dict, message_dict, event_type, event_code):
    #     # створюємо словник для швидкого пошуку event_by_user по типу події та коду
    #     event_by_user_dict = {(event['type_event'], event['code']): event['event_by_user'] for event in event_dict}
    #
    #     # шукаємо event_by_user за заданими event_type та event_code
    #     event_by_user = event_by_user_dict.get((event_type, event_code))
    #
    #     # якщо подія не знайдена, повертаємо None
    #     if not event_by_user:
    #         return None
    #
    #     # знаходимо event_by_user в словнику повідомлень та повертаємо його переклад на українську
    #     for message in message_dict:
    #         if message['name'] == event_by_user:
    #             return message['lang_uk']
    #
    #     return None

read_json = ReadJson("common/custom_device.json")
json_dict = read_json.open_json()
# print(json_dict)
dictionary_add = json_dict['data'][0]['dictionary_add']
events = json_dict['data'][0]['events']
# bson_data = bson.dumps(json_dict)
# msgpack_data = msgpack.packb(json_dict)
# print(msgpack_data)
print(events)
# hashtable = HashTable()
# for event_dict in events:
#     for key, value in event_dict.items():
#         # print(key, value)
#         hashtable.put(key, value)
# print(hashtable.get('event_by_user'))
#
# for event_dict in events:
#     for key, value in json_dict.items():
#         if key == "event_by_user" and value == 'DOWNLOAD_SUCCESS_FIRMWARE':
#             print(event_dict['code'])
#             break
#
# for key, value in json_dict.items():
#     # print(key, value)
#     hashtable.put(key, value)
# print(hashtable.get(['data'][0]['events']))

# cProfile.run(read_json.find_event_name_by_type_and_code(events,dictionary_add,'R',400))


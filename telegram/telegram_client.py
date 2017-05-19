from getpass import getpass
from time import sleep
from typing import Set, List

from telethon import RPCError, TelegramClient
from telethon.tl.functions.messages import GetFullChatRequest
from telethon.tl.types import Channel
from telethon.tl.types import Chat as TChat
from telethon.tl.types import MessageService

from models import Chat, ChatsEntities, Message, User


class SettingsHolder:
    _cfg_delimiter = '='

    # parameters names
    _session_user_id = 'session_user_id'
    _user_phone = 'user_phone'
    _api_id, _api_hash = 'api_id', 'api_hash'
    _proxy = 'proxy'

    # matching parameters names and types
    _params_names_types = {_session_user_id: str, _user_phone: str, _api_id: int, _api_hash: str, _proxy: str}

    def __init__(self, tg_config_file_path: str, target_chats_file_path: str):
        self._tg_config_file_path = tg_config_file_path
        self._target_chats_file_path = target_chats_file_path

        self.tg_settings = self._load_tg_settings()
        self.target_chats_titles = self._load_target_chats_titles()

    def _get_name_value_pair(self, cfg_line: str) -> tuple:
        """
        Gets name and value from the given config line.
        :param cfg_line: line from the config file
        :return: tuple(name, value) - name-value pair

        ..:note: Config line should have correct format 'name=value' or 'name='
        """
        name, value = cfg_line.replace(' ', '').replace('\n', '').split('=')

        if name in self._params_names_types.keys():
            # cast value to the corresponding type
            return name, self._params_names_types[name](value) if value else None

    def _load_tg_settings(self):
        with open(self._tg_config_file_path, 'r') as config_file:
            keys_values = [self._get_name_value_pair(line) for line in config_file
                           if line and line != '\n' and not line.startswith('#')]

        return dict(keys_values)

    def _load_target_chats_titles(self):
        with open(self._target_chats_file_path, 'r', encoding='utf-8') as f:
            return [chat_title.replace('\n', '') for chat_title in f]

    def get_tg_settings(self):
        return self.tg_settings

    def get_target_chats(self):
        return self.target_chats_titles


class TelegramDataLoader(TelegramClient):
    _dialogs_per_time, _messages_per_time = 100, 100

    def __init__(self, session_user_id, user_phone, api_id, api_hash, proxy=None):

        print('Initializing interactive example...')
        super().__init__(session_user_id, api_id, api_hash, proxy)

        # Store all the found media in memory here,
        # so it can be downloaded if the user wants
        self.found_media = set()

        print('Connecting to Telegram servers...')
        self.connect()

        # Then, ensure we're authorized and have access
        if not self.is_user_authorized():
            print('First run. Sending code request...')
            self.send_code_request(user_phone)

            code_ok = False
            while not code_ok:
                code = input('Enter the code you just received: ')
                try:
                    code_ok = self.sign_in(user_phone, code)

                # Two-step verification may be enabled
                except RPCError as e:
                    if e.password_required:
                        pw = getpass(
                            'Two step verification is enabled. Please enter your password: ')
                        code_ok = self.sign_in(password=pw)
                    else:
                        raise e

    def download_media(self, media_id):
        try:
            # The user may have entered a non-integer string!
            msg_media_id = int(media_id)

            # Search the message ID
            for msg in self.found_media:
                if msg.id == msg_media_id:
                    # Let the output be the message ID
                    output = str('usermedia/{}'.format(msg_media_id))
                    print('Downloading media with name {}...'.format(output))
                    output = self.download_msg_media(
                        msg.media,
                        file_path=output,
                        progress_callback=None)
                    print('Media downloaded to {}!'.format(output))

        except ValueError:
            print('Invalid media ID given!')

    @staticmethod
    def _parse_chat(chat, chat_users: Set[User]) -> Chat:
        if chat:
            return Chat(chat.id, chat.title, len(chat_users), set(u.uid for u in chat_users))

    @staticmethod
    def _parse_message(msg, channel_id) -> Message:
        if msg and not isinstance(msg, MessageService):
            return Message(msg.id, msg.message, msg.date, msg.from_id, channel_id)

    @staticmethod
    def _parse_user(user) -> User:
        if user:
            return User(user.id, user.first_name, user.last_name, user.username)

    def get_chats_entities(self, chats_names: List[str]) -> ChatsEntities:
        dialogs, entities = self.get_dialogs(self._dialogs_per_time)    # get last `_dialogs_per_time` dialogs

        chats, users, messages = set(), set(), set()

        for e in entities:
            if isinstance(e, Channel) and e.title in chats_names:

                curr_chat_users = set()

                # get total messages counts
                total_count, history, senders = self.get_message_history(e, 1)

                # calculate iterations number needed to get download all the messages
                offset, iterations_number = 0, int(total_count / self._messages_per_time) + 1

                # parse messages
                for i in range(0, iterations_number):
                    total_count, history, senders = self.get_message_history(e,
                                                                             self._messages_per_time,
                                                                             add_offset=offset)

                    messages.update([self._parse_message(msg, e.id) for msg in history
                                     if msg and not isinstance(msg, MessageService) and msg.message])

                    curr_chat_users.update([self._parse_user(user) for user in senders if user])

                    offset += self._messages_per_time

                    sleep(0.75)

                # add chat to chats list
                chats.add(self._parse_chat(e, curr_chat_users))

                users.update(curr_chat_users)

        return ChatsEntities(users, chats, messages)


if __name__ == '__main__':
    s = SettingsHolder('settings/tg_config', 'settings/target_chats')
    tg = TelegramDataLoader(**s.get_tg_settings())

    dialogs, entities = tg.get_dialogs(10)
    entities = [e for e in entities if isinstance(e, TChat) and e.title == 'Test']
    res = tg.invoke(
        GetFullChatRequest(entities[-1].id)
    )

    print(res)
    # getFullChat() - for isinstance(e, Chat)
    # GetParticipantsRequest(InputChannel(), ChannelParticipants(), offset=0, limit=100)

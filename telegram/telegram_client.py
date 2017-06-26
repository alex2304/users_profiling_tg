import os
from datetime import datetime, timedelta
from getpass import getpass
from time import sleep
from typing import Set, List, Tuple

from telethon import RPCError, TelegramClient
from telethon.tl.types import Channel
from telethon.tl.types import MessageActionChatAddUser
from telethon.tl.types import MessageActionChatJoinedByLink
from telethon.tl.types import MessageService

from models import Chat, ChatsEntities, Message, User
from models import UserInChat


class SettingsHolder:
    _cfg_delimiter = '='

    # parameters names
    _session_name = 'session_name'
    _user_phone = 'user_phone'
    _api_id, _api_hash = 'api_id', 'api_hash'
    _proxy = 'proxy'

    # matching parameters names and types
    _params_names_types = {_session_name: str, _user_phone: str, _api_id: int, _api_hash: str, _proxy: str}

    def __init__(self, config_file_path: str):
        self._config_file_path = config_file_path

        self.settings_dict = self._load_settings()

    def _load_settings(self):
        try:
            with open(self._config_file_path, 'r') as config_file:
                keys_values = [self._get_name_value_pair(line) for line in config_file
                               if line and line != '\n' and not line.startswith('#')]

        except FileNotFoundError as e:
            e.with_traceback(e.__traceback__)

        else:
            return dict(keys_values)

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

        # str type of values by default (if any unknown parameters)
        else:
            return name, str(value)

    def get_settings_dict(self):
        return self.settings_dict


class TgClient(TelegramClient):
    _dialogs_per_time, _messages_per_time = 100, 100
    _sessions_folder = os.path.join(os.path.dirname(__file__), 'sessions')

    def __init__(self, session_name: str = None, user_phone: str = None, api_id: int = None, api_hash: str = None,
                 proxy=None,
                 debug_mode=False):
        self._debug = (lambda text: print(text)) if debug_mode else (lambda text: text)
        self._session_filepath = os.path.join(self._sessions_folder, session_name)

        # create session folder if doesn't exist
        if not os.path.exists(self._sessions_folder):
            os.mkdir(self._sessions_folder)

        self._debug('Initializing with session at %s' % self._session_filepath)
        super().__init__(self._session_filepath, api_id, api_hash, proxy)

        # save the current user's phone
        self.user_phone = user_phone

        self._debug('Connecting to Telegram servers...')
        self.connect()

        self._debug('Connected!')

    def authorized(self):
        """
        Checks whether the session of the user contains authorization data (user is authorized)
        If so - returns True, otherwise - sends authorization code to the user and returns False
        """
        if not self.is_user_authorized():
            self._debug('First run. Sending code request...')
            self.send_code_request(self.user_phone)

            return False

        return True

    def enter_code(self, code):
        try:
            self._debug('Trying to sign in...')
            code_ok = self.sign_in(self.user_phone, code)
            self._debug('Result with code #%s...' % str(code_ok if code_ok else 'error'))

            return code_ok

        # Two-step verification may be enabled
        except RPCError as e:
            if e.password_required:
                self._debug('Error signing in: password is required (Two-step verification is enabled)')

            return None

    def enter_password(self, password):
        code_ok = self.sign_in(password=password)

        return code_ok

    @staticmethod
    def _parse_chat(chat: Channel, users_count: int, messages_count: int, creation_datetime: datetime) -> Chat:
        if chat:
            return Chat(chat.id, chat.title, users_count, messages_count, creation_datetime)

    @staticmethod
    def _parse_message(msg, channel_id) -> Message:
        # service message: who has joined, who has been invited, ...
        if msg and not isinstance(msg, MessageService) and msg.message:
            message_text = msg.message

            if message_text and 2 < len(message_text) < 500:
                return Message(msg.id, message_text, msg.date, msg.from_id, channel_id)

    @staticmethod
    def _parse_user(user) -> User:
        if user:
            return User(user.id, user.first_name, user.last_name, user.username)

    @staticmethod
    def _parse_users_in_chat(chat, chat_users, chat_messages) -> Tuple[List[UserInChat], Set[User], datetime]:
        """
        # 1) Average common messages frequency (count/day)
        # 2) Average messages length
        # 3) Difference between chat creation and chat entering
        :return: Tuple(UserChats, NewUsers, chat creation datetime)
        """
        # TODO: parse who added who

        def _get_empty_params():
            return {
                'last_day_msgs_count': 0,
                'active_days_count': 0,
                'last_day': None,

                'total_len': 0,
                'text_msgs_count': 0,
                'total_msgs_count': 0,

                'join_datetime': None
            }

        chat_creation_datetime = chat.date

        users_ids = {user.id: _get_empty_params()
                     for user in chat_users}
        new_users = set()

        # traverse history from newest to oldest messages
        chat_messages = sorted(list(chat_messages), key=lambda m: m.date, reverse=True)

        for msg in chat_messages:
            sender_params = users_ids.get(msg.from_id)

            # service message
            if isinstance(msg, MessageService):
                action = msg.action

                join_datetime = msg.date
                if join_datetime < chat_creation_datetime:
                    chat_creation_datetime = join_datetime

                # user has joined the chat by link or has been invited by someone
                if isinstance(action, MessageActionChatJoinedByLink):
                    # MessageActionChatJoinedByLink:
                    #   action.inviter_id - id of the people who has joined
                    joiner_id = msg.from_id

                    sender_params = users_ids.get(joiner_id)

                    if not sender_params:
                        new_users.add(User(joiner_id, 'joined by link'))

                        users_ids[joiner_id] = _get_empty_params()
                        sender_params = users_ids[joiner_id]

                    sender_params['join_datetime'] = join_datetime

                elif isinstance(action, MessageActionChatAddUser):
                    # MessageActionChatAddUser:
                    #   msg.from_id - id of the people who has invited
                    #   action.users - list of users who have been invited
                    if not action.users:
                        print('Warning: empty "users" field of the MessageActionChatAddUser')
                        continue

                    for joiner_id in action.users:
                        sender_params = users_ids.get(joiner_id)

                        if not sender_params:
                            new_users.add(User(joiner_id, 'was invited'))

                            users_ids[joiner_id] = _get_empty_params()
                            sender_params = users_ids[joiner_id]

                        sender_params['join_datetime'] = join_datetime

                else:
                    continue

            # message written directly by user
            else:
                if not sender_params:
                    print('Missed user with id #%s' % str(msg.from_id if msg.from_id else 'None'))
                    continue

                # message with a text
                if msg.message:
                    # increase total messages length
                    sender_params['total_len'] += len(msg.message)
                    sender_params['text_msgs_count'] += 1

                # message without a text
                else:
                    pass

                sender_params['total_msgs_count'] += 1

                msg_date = msg.date.date()

                if msg_date != sender_params['last_day']:
                    # add new active day
                    sender_params['active_days_count'] += 1

                    # reset params
                    sender_params['last_day'] = msg_date
                    sender_params['last_day_msgs_count'] = 1

                else:
                    sender_params['last_day_msgs_count'] += 1

        users_in_chat = []

        for u_id, params in users_ids.items():
            join_datetime = params['join_datetime']

            # calculate average messages length
            text_msgs_count, total_len = params['text_msgs_count'], params['total_len']
            avg_msg_len = total_len / text_msgs_count if text_msgs_count else 0

            # calculate average messages frequency
            # TODO: add chat characteristic
            active_days_count = params['active_days_count']

            total_msgs_count = params['total_msgs_count']

            if join_datetime:
                now_entering_diff = datetime.now() - join_datetime
            else:
                now_entering_diff = datetime.now() - chat_creation_datetime

            days_count = now_entering_diff.days
            avg_daily_freq = total_msgs_count / days_count if days_count else 0

            # calculate difference between chat entering and chat creation
            if join_datetime:
                creation_entering_diff = join_datetime - chat_creation_datetime

            else:
                creation_entering_diff = timedelta()

            users_in_chat.append(UserInChat(chat.id, u_id,
                                            creation_entering_diff.total_seconds(),
                                            avg_daily_freq, avg_msg_len))

        return users_in_chat, new_users, chat_creation_datetime

    def get_chats_entities(self, chats_names: List[str]) -> ChatsEntities:
        _, entities = self.get_dialogs(100)

        # it's expected that title is a unique identifier of a chat
        channels = {e.title: e for e in entities if isinstance(e, Channel) and e.title in chats_names}

        # if some chats not found
        not_found = set(chats_names).difference(channels.keys())
        if not_found:
            raise ValueError('Chats %s not found, exiting.' % str(not_found))
        else:
            print('Found all the %d chats.\nMessages and users gathering started.' % len(channels))

        total_chats, total_users, total_messages = set(), set(), set()
        total_users_in_chats = set()

        chat_users, chat_messages = set(), set()

        for chat in channels.values():
            chat_users.clear()
            chat_messages.clear()

            # get total messages counts
            messages_count, _, _ = self.get_message_history(chat, 1)

            # calculate iterations number needed to get download all the messages
            offset, iterations_number = 0, int(messages_count / self._messages_per_time) + 1

            # download chat information (by iterations)
            for i in range(0, iterations_number):
                _, history, senders = self.get_message_history(chat,
                                                               self._messages_per_time,
                                                               add_offset=offset)
                chat_users.update([s for s in senders if s])
                chat_messages.update([m for m in history if m])

                # wait before next iteration
                sleep(0.75)

                offset += self._messages_per_time

            # TODO: save to cache before parsing
            # add users_in_chat entities for the chat, and get extra users
            users_in_chat, extra_chat_users, chat_creation_datetime = self._parse_users_in_chat(chat, chat_users, chat_messages)
            total_users_in_chats.update(users_in_chat)

            # add users from the chat
            curr_chat_users = {self._parse_user(user) for user in chat_users}.union(extra_chat_users)
            total_users.update(curr_chat_users)

            # add messages from the chat
            for msg in chat_messages:
                message = self._parse_message(msg, chat.id)

                if message:
                    total_messages.add(message)

            # the same thing in different way
            # messages.update(filter(lambda m: m, [self._parse_message(msg, chat.id) for msg in chat_messages]))

            # finally - add chat entity
            total_chats.add(self._parse_chat(chat, len(curr_chat_users), messages_count, chat_creation_datetime))

        return ChatsEntities(total_chats, total_users, total_messages, total_users_in_chats)


if __name__ == '__main__':
    chats_names = ['Попутчики Иннополис']

    # telegram settings
    # session_name = 'Yota'
    # user_phone = '+79991632629'
    session_name = 'Tele2'
    user_phone = '+79500343697'
    api_id = 157094
    api_hash = '7f9607eb95326111a8ed0b289a75640b'

    tg = TgClient(session_name, user_phone, api_id, api_hash, debug_mode=True)

    # make sure we're authorized
    if not tg.authorized():
        if not tg.enter_code(input('Enter code: ')):
            if not tg.enter_password(getpass('Enter password: ')):
                # something goes wrong ('if' statements below can be replaced with 'while')
                exit()

    chat_entities = tg.get_chats_entities(chats_names)
    print('done')

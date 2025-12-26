# message_helper.py
import random
from typing import List
from constants import Constants


class MessageHelper:
    @staticmethod
    def get_random_message(message_list: List[str]) -> str:
        return random.choice(message_list)

    @staticmethod
    def format_player_added(player_name: str) -> str:
        base_msg = random.choice(Constants.YOU_ADD_IN_LIST)
        return f"<b>{base_msg}</b>\n\n{player_name}"  # ✅ HTML

    @staticmethod
    def format_player_removed(player_name: str) -> str:
        base_msg = random.choice(Constants.YOU_DEL_IN_LIST)
        return f"<b>{base_msg}</b>\n\n{player_name}"  # ✅ HTML

    @staticmethod
    def format_player_exists(player_name: str) -> str:
        base_msg = random.choice(Constants.YOU_IN_LIST)
        return f"<b>{base_msg}{player_name}</b>"  # ✅ HTML

    @staticmethod
    def format_player_not_exists() -> str:
        return f"<b>{random.choice(Constants.YOU_NOT_LIST)}</b>"  # ✅ HTML

    @staticmethod
    def format_friend_added() -> str:
        return f"<b>{random.choice(Constants.YOU_ADD_FRIEND_IN_LIST)}</b>"  # ✅ HTML

    @staticmethod
    def format_friend_removed() -> str:
        return f"<b>{random.choice(Constants.YOU_DEL_FRIEND_IN_LIST)}</b>"  # ✅ HTML

    @staticmethod
    def format_serega_message() -> str:
        return f"<b>{random.choice(Constants.SEREGA_LIST)}</b>"  # ✅ HTML

    @staticmethod
    def get_great_player_message() -> str:
        return f"<b>{random.choice(Constants.GRATE_PLAYER_LIST)}</b>"  # ✅ HTML

    @staticmethod
    def get_loser_player_message() -> str:
        return f"<b>{random.choice(Constants.LOSER_PLAYER_LIST)}</b>"  # ✅ HTML


message_helper = MessageHelper()
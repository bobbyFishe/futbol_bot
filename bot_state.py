# bot_state.py
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from constants import Constants
from time_manager import time_manager
from database import db  # Добавляем импорт базы данных


class BotState:
    def __init__(self):
        self.group_lists: Dict[int, List[str]] = {}
        self.great_player: Optional[str] = None
        self.loser_player: Optional[str] = None
        self.last_reset_day: int = time_manager.get_current_day()
        self.last_reset_date: Dict[int, str] = {}  # Хранит дату последнего обнуления для каждого чата

    def get_chat_list(self, chat_id: int) -> List[str]:
        if chat_id not in self.group_lists:
            self.group_lists[chat_id] = []
        return self.group_lists[chat_id]

    def reset_daily_lists(self, chat_id: int):
        """Сбрасывает списки если прошло нужное количество дней"""
        try:
            reset_days = db.get_reset_days(chat_id)
            current_date = time_manager.get_current_date()

            # Если это первый раз для чата, устанавливаем текущую дату
            if chat_id not in self.last_reset_date:
                self.last_reset_date[chat_id] = current_date
                return

            last_reset = self.last_reset_date[chat_id]

            # Проверяем, прошло ли нужное количество дней
            if self._days_between_dates(last_reset, current_date) >= reset_days:
                self.group_lists[chat_id] = []
                self.last_reset_date[chat_id] = current_date
                self.great_player = None
                self.loser_player = None
                print(f"Список для чата {chat_id} обнулен. Следующее обнуление через {reset_days} дней")

        except Exception as e:
            print(f"Ошибка в reset_daily_lists: {e}")

    def _days_between_dates(self, date1: str, date2: str) -> int:
        """Вычисляет количество дней между двумя датами"""
        from datetime import datetime
        d1 = datetime.strptime(date1, '%Y-%m-%d')
        d2 = datetime.strptime(date2, '%Y-%m-%d')
        return (d2 - d1).days

    def set_great_loser_players(self, great_player: str, loser_player: str):
        self.great_player = great_player
        self.loser_player = loser_player

    def get_great_loser_players(self) -> Tuple[Optional[str], Optional[str]]:
        return self.great_player, self.loser_player


bot_state = BotState()
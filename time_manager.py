# time_manager.py
from datetime import datetime, timedelta

class TimeManager:
    def __init__(self):
        pass

    def get_moscow_time(self):
        """Возвращает время с учетом смещения +3 часа к серверному времени"""
        server_time = datetime.now()
        return server_time + timedelta(hours=3)  # UTC+0 → UTC+3 = Москва (+3 часа)

    def is_voting_time(self) -> bool:
        """Проверяет, можно ли голосовать (с 9 до 21 часа по Москве)"""
        now = self.get_moscow_time()
        return 9 <= now.hour < 21

    def is_early_voting_time(self) -> bool:
        """Проверяет раннее время голосования (до 9 часов по Москве)"""
        now = self.get_moscow_time()
        return now.hour < 9

    def can_add_friends(self) -> bool:
        """Проверяет, можно ли добавлять друзей (после 10 часов по Москве)"""
        now = self.get_moscow_time()
        return now.hour >= 10

    def is_penalty_time(self) -> bool:
        """Проверяет время для штрафов (после 18 часов по Москве)"""
        now = self.get_moscow_time()
        return now.hour >= 18

    def get_current_date(self) -> str:
        return self.get_moscow_time().strftime('%Y-%m-%d')

    def get_current_day(self) -> int:
        return self.get_moscow_time().day

    def get_current_hour(self) -> int:
        return self.get_moscow_time().hour

    # 🔴 НОВЫЕ МЕТОДЫ ДЛЯ ОТОБРАЖЕНИЯ ВРЕМЕНИ
    def get_voting_start_hour(self) -> int:
        """Возвращает час начала голосования по Москве"""
        return 9

    def get_voting_end_hour(self) -> int:
        """Возвращает час окончания голосования по Москве"""
        return 21

    def get_friends_start_hour(self) -> int:
        """Возвращает час начала добавления друзей по Москве"""
        return 10

    def get_penalty_start_hour(self) -> int:
        """Возвращает час начала штрафного времени по Москве"""
        return 18

    # Добавим в класс TimeManager:

    def is_voting_time_for_chat(self, chat_id: int) -> bool:
        """Проверяет, можно ли голосовать в указанном чате"""
        try:
            from database import db  # Импортируем здесь чтобы избежать циклического импорта
            start_hour, end_hour = db.get_voting_time(chat_id)
            current_hour = self.get_moscow_time().hour

            # Если время круглосуточное
            if start_hour == 0 and end_hour == 24:
                return True

            # Если период не пересекает полночь (например, 9-21)
            if start_hour < end_hour:
                return start_hour <= current_hour < end_hour
            # Если период пересекает полночь (например, 22-6)
            else:
                return current_hour >= start_hour or current_hour < end_hour

        except Exception as e:
            print(f"Ошибка в is_voting_time_for_chat: {e}")
            return True  # По умолчанию разрешаем

    def get_voting_time_for_chat(self, chat_id: int) -> tuple[int, int]:
        """Возвращает время голосования для чата"""
        try:
            from database import db
            return db.get_voting_time(chat_id)
        except Exception:
            return 0, 24  # По умолчанию

# Глобальный экземпляр
time_manager = TimeManager()
# database.py
import sqlite3
import os
from typing import Optional, List, Tuple, Dict, Any
from constants import Constants


class DatabaseManager:
    def __init__(self, db_path: str = None):
        if db_path is None:
            if not os.path.exists('data'):
                os.makedirs('data')
            self.db_path = '/data/user_name.db'
        else:
            self.db_path = db_path

        self._init_tables()

    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    # database.py - добавить в класс DatabaseManager

    # database.py - обновляем метод _init_tables и добавляем миграцию

    def _init_tables(self):
        """Инициализация всех таблиц"""
        try:
            tables = [
                # Основные таблицы (остаются без изменений)
                'CREATE TABLE IF NOT EXISTS chats(chat_id INTEGER PRIMARY KEY, chat_name TEXT, active_db TEXT)',
                'CREATE TABLE IF NOT EXISTS users(id_ int, name varchar(50), user_name varchar(50))',

                # Таблицы, связанные с чатами
                'CREATE TABLE IF NOT EXISTS chat_settings(chat_id INTEGER, setting_name TEXT, setting_value TEXT, PRIMARY KEY(chat_id, setting_name))',
                'CREATE TABLE IF NOT EXISTS chat_penalty(chat_id INTEGER, user_id INTEGER, penalty BOOLEAN, PRIMARY KEY(chat_id, user_id))',

                # НОВАЯ ТАБЛИЦА для хранения всех баз данных чата
                'CREATE TABLE IF NOT EXISTS chat_databases(chat_id INTEGER, db_name TEXT, created_date TEXT, PRIMARY KEY(chat_id, db_name))',

                # Таблицы статистики для разных баз данных
                'CREATE TABLE IF NOT EXISTS database_stats(db_name TEXT, chat_id INTEGER, date_game TEXT, team1_score INTEGER, team2_score INTEGER, PRIMARY KEY(db_name, chat_id, date_game))',

                # НОВЫЕ ТАБЛИЦЫ для статистики игроков (общая по всем сезонам)
                'CREATE TABLE IF NOT EXISTS player_stats(chat_id INTEGER, user_id INTEGER, games_played INTEGER DEFAULT 0, friends_added INTEGER DEFAULT 0, PRIMARY KEY(chat_id, user_id))',
                'CREATE TABLE IF NOT EXISTS game_attendance(db_name TEXT, chat_id INTEGER, date_game TEXT, user_id INTEGER, attended BOOLEAN, PRIMARY KEY(db_name, chat_id, date_game, user_id))'
            ]

            conn = self._get_connection()
            cursor = conn.cursor()
            for table_sql in tables:
                cursor.execute(table_sql)
            conn.commit()
            conn.close()

            # print("Запуск миграции времени голосования...")
            # self._migrate_voting_time()
            # 🔴 ВЫЗОВ МИГРАЦИЙ ПОСЛЕ ИНИЦИАЛИЗАЦИИ ТАБЛИЦ
            # print("Запуск миграции существующих чатов...")
            # self._migrate_existing_chats()
            # self._migrate_player_stats()  # Новая миграция для статистики игроков

        except Exception:
            raise

    # def _migrate_player_stats(self):
    #     """Очистка таблиц статистики для начала с нуля"""
    #     try:
    #         conn = self._get_connection()
    #         cursor = conn.cursor()
    #
    #         print("Очистка таблиц статистики игроков...")
    #
    #         # УДАЛЯЕТ ВСЕ ДАННЫЕ из таблиц
    #         cursor.execute('DELETE FROM player_stats')
    #         cursor.execute('DELETE FROM game_attendance')
    #
    #         conn.commit()
    #         conn.close()
    #
    #         print("Таблицы статистики очищены - начинаем с нуля")
    #         return True
    #     except Exception as e:
    #         print(f"Ошибка при очистке статистики: {e}")
    #         return False

    def update_player_stats(self, chat_id: int, user_list: List[str], db_name: str):
        """Обновляет статистику игроков (общая по всем сезонам)"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            current_date = self.get_current_date()

            # Обновляем статистику для каждого игрока в списке
            for player_name in user_list:
                if '+1 от ' in player_name:
                    # Это друг - находим основного игрока
                    main_player = player_name.replace('+1 от ', '')
                    cursor.execute('SELECT id_ FROM users WHERE name = ?', (main_player,))
                    result = cursor.fetchone()
                    if result:
                        user_id = result[0]
                        # Увеличиваем счетчик добавленных друзей для основного игрока
                        cursor.execute('''
                            INSERT INTO player_stats (chat_id, user_id, games_played, friends_added) 
                            VALUES (?, ?, 0, 1)
                            ON CONFLICT(chat_id, user_id) 
                            DO UPDATE SET friends_added = friends_added + 1
                        ''', (chat_id, user_id))
                else:
                    # Это основной игрок
                    cursor.execute('SELECT id_ FROM users WHERE name = ?', (player_name,))
                    result = cursor.fetchone()
                    if result:
                        user_id = result[0]
                        # Отмечаем посещение игры (привязываем к сезону)
                        cursor.execute('''
                            INSERT OR REPLACE INTO game_attendance (db_name, chat_id, date_game, user_id, attended)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (db_name, chat_id, current_date, user_id, True))

                        # Увеличиваем счетчик сыгранных игр (общая статистика)
                        cursor.execute('''
                            INSERT INTO player_stats (chat_id, user_id, games_played, friends_added) 
                            VALUES (?, ?, 1, 0)
                            ON CONFLICT(chat_id, user_id) 
                            DO UPDATE SET games_played = games_played + 1
                        ''', (chat_id, user_id))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка в update_player_stats: {e}")
            return False

    # database.py - в класс DatabaseManager добавить/исправить:

    def get_top_players(self, chat_id: int, stat_type: str, limit: int = 3) -> List[Tuple]:
        """Возвращает топ игроков по указанной статистике (только тех, у кого значение > 0)"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            if stat_type == 'games_played':
                cursor.execute('''
                    SELECT u.name, ps.games_played 
                    FROM player_stats ps
                    JOIN users u ON ps.user_id = u.id_
                    WHERE ps.chat_id = ? AND ps.games_played > 0
                    ORDER BY ps.games_played DESC 
                    LIMIT ?
                ''', (chat_id, limit))
            elif stat_type == 'friends_added':
                cursor.execute('''
                    SELECT u.name, ps.friends_added 
                    FROM player_stats ps
                    JOIN users u ON ps.user_id = u.id_
                    WHERE ps.chat_id = ? AND ps.friends_added > 0
                    ORDER BY ps.friends_added DESC 
                    LIMIT ?
                ''', (chat_id, limit))
            else:
                conn.close()
                return []

            results = cursor.fetchall()
            conn.close()
            return results
        except Exception as e:
            print(f"Ошибка в get_top_players: {e}")
            return []

    def get_player_stats_summary(self, chat_id: int) -> Dict[str, int]:
        """Возвращает сводную статистику по всем игрокам (общая по всем сезонам)"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT 
                    COUNT(DISTINCT user_id) as total_players,
                    SUM(games_played) as total_games_played,
                    SUM(friends_added) as total_friends_added
                FROM player_stats 
                WHERE chat_id = ?
            ''', (chat_id,))

            result = cursor.fetchone()
            conn.close()

            if result:
                return {
                    'total_players': result[0] or 0,
                    'total_games_played': result[1] or 0,
                    'total_friends_added': result[2] or 0
                }
            return {'total_players': 0, 'total_games_played': 0, 'total_friends_added': 0}
        except Exception as e:
            print(f"Ошибка в get_player_stats_summary: {e}")
            return {'total_players': 0, 'total_games_played': 0, 'total_friends_added': 0}

    # database.py - добавить в класс DatabaseManager

    def _ensure_chat_initialized(self, chat_id: int, chat_name: str = ""):
        """Автоматически создает базу данных для чата если её нет"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('SELECT * FROM chats WHERE chat_id = ?', (chat_id,))
            existing_chat = cursor.fetchone()

            if not existing_chat:
                # Создаем чат с базой данных по умолчанию
                cursor.execute('INSERT INTO chats(chat_id, chat_name, active_db) VALUES(?, ?, ?)',
                               (chat_id, chat_name, 'default'))

                # Добавляем default базу в список баз
                created_date = self.get_current_date()
                cursor.execute('INSERT INTO chat_databases(chat_id, db_name, created_date) VALUES(?, ?, ?)',
                               (chat_id, 'default', created_date))

                # Устанавливаем настройки по умолчанию
                default_settings = [
                    (chat_id, 'team1_name', Constants.DEFAULT_TEAM1_NAME),
                    (chat_id, 'team2_name', Constants.DEFAULT_TEAM2_NAME),
                    (chat_id, 'limit_player', '14'),
                    (chat_id, 'active_db', 'default'),
                    (chat_id, 'reset_days', '1')
                ]

                cursor.executemany('INSERT INTO chat_settings(chat_id, setting_name, setting_value) VALUES(?, ?, ?)',
                                   default_settings)

                conn.commit()

            conn.close()
            return True
        except Exception:
            return False
    # Управление чатами и базами данных
    def create_database(self, db_name: str, chat_id: int, chat_name: str = ""):
        """Создает новую базу данных для чата"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Проверяем, существует ли уже база с таким именем для этого чата
            cursor.execute('SELECT * FROM chat_databases WHERE chat_id = ? AND db_name = ?', (chat_id, db_name))
            existing_db = cursor.fetchone()

            if existing_db:
                conn.close()
                return False  # База с таким именем уже существует

            # Добавляем базу в список баз чата
            created_date = self.get_current_date()
            cursor.execute('INSERT INTO chat_databases(chat_id, db_name, created_date) VALUES(?, ?, ?)',
                           (chat_id, db_name, created_date))

            # ✅ УЖЕ ЕСТЬ: Обновляем активную базу (сразу переключаемся)
            cursor.execute('INSERT OR REPLACE INTO chats(chat_id, chat_name, active_db) VALUES(?, ?, ?)',
                           (chat_id, chat_name, db_name))

            # Устанавливаем настройки по умолчанию для этой базы
            default_settings = [
                (chat_id, 'team1_name', Constants.DEFAULT_TEAM1_NAME),
                (chat_id, 'team2_name', Constants.DEFAULT_TEAM2_NAME),
                (chat_id, 'limit_player', '12'),
                (chat_id, 'active_db', db_name)  # ✅ И здесь тоже
            ]

            cursor.executemany(
                'INSERT OR REPLACE INTO chat_settings(chat_id, setting_name, setting_value) VALUES(?, ?, ?)',
                default_settings)

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка в create_database: {e}")
            return False

    def switch_database(self, chat_id: int, db_name: str):
        """Переключает активную базу данных для чата"""
        try:
            # Проверяем, существует ли база для этого чата
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM chat_databases WHERE chat_id = ? AND db_name = ?', (chat_id, db_name))
            existing_db = cursor.fetchone()

            if not existing_db:
                conn.close()
                return False  # База не существует для этого чата

            # Переключаем активную базу
            cursor.execute('UPDATE chats SET active_db = ? WHERE chat_id = ?', (db_name, chat_id))
            cursor.execute('UPDATE chat_settings SET setting_value = ? WHERE chat_id = ? AND setting_name = ?',
                           (db_name, chat_id, 'active_db'))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка в switch_database: {e}")
            return False

    def get_chat_databases(self, chat_id: int) -> List[str]:
        """Возвращает список всех баз данных для чата"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Получаем все базы данных для этого чата
            cursor.execute('SELECT db_name FROM chat_databases WHERE chat_id = ? ORDER BY created_date DESC',
                           (chat_id,))
            results = cursor.fetchall()
            conn.close()

            databases = [result[0] for result in results] if results else []

            # Если нет созданных баз, добавляем default
            if not databases:
                databases = ['default']

            return databases
        except Exception as e:
            print(f"Ошибка в get_chat_databases: {e}")
            return ['default']

    def get_active_database(self, chat_id: int) -> str:
        """Возвращает активную базу данных для чата"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT active_db FROM chats WHERE chat_id = ?', (chat_id,))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else 'default'
        except Exception:
            return 'default'

    # Управление командами
    def set_team_names(self, chat_id: int, team1: str, team2: str):
        """Устанавливает названия команд для чата"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('INSERT OR REPLACE INTO chat_settings(chat_id, setting_name, setting_value) VALUES(?, ?, ?)',
                           (chat_id, 'team1_name', team1))
            cursor.execute('INSERT OR REPLACE INTO chat_settings(chat_id, setting_name, setting_value) VALUES(?, ?, ?)',
                           (chat_id, 'team2_name', team2))

            conn.commit()
            conn.close()
            return True
        except Exception:
            return False

    def get_team_names(self, chat_id: int) -> Tuple[str, str]:
        """Возвращает названия команд для чата"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('SELECT setting_value FROM chat_settings WHERE chat_id = ? AND setting_name = ?',
                           (chat_id, 'team1_name'))
            team1 = cursor.fetchone()

            cursor.execute('SELECT setting_value FROM chat_settings WHERE chat_id = ? AND setting_name = ?',
                           (chat_id, 'team2_name'))
            team2 = cursor.fetchone()

            conn.close()

            team1_name = team1[0] if team1 else Constants.DEFAULT_TEAM1_NAME
            team2_name = team2[0] if team2 else Constants.DEFAULT_TEAM2_NAME

            return team1_name, team2_name
        except Exception:
            return Constants.DEFAULT_TEAM1_NAME, Constants.DEFAULT_TEAM2_NAME

    # Статистика с улучшенным выводом
    def add_game_stats(self, chat_id: int, db_name: str, team1_score: int, team2_score: int):
        """Добавляет статистику игры"""
        try:
            date_game = self.get_current_date()
            conn = self._get_connection()
            cursor = conn.cursor()

            # Проверяем, существует ли уже запись для этой даты
            cursor.execute(
                'SELECT * FROM database_stats WHERE db_name = ? AND chat_id = ? AND date_game = ?',
                (db_name, chat_id, date_game)
            )
            existing_record = cursor.fetchone()

            if existing_record:
                # Обновляем существующую запись
                cursor.execute(
                    'UPDATE database_stats SET team1_score = ?, team2_score = ? WHERE db_name = ? AND chat_id = ? AND date_game = ?',
                    (team1_score, team2_score, db_name, chat_id, date_game)
                )
            else:
                # Создаем новую запись
                cursor.execute(
                    'INSERT INTO database_stats(db_name, chat_id, date_game, team1_score, team2_score) VALUES(?, ?, ?, ?, ?)',
                    (db_name, chat_id, date_game, team1_score, team2_score)
                )

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка в add_game_stats: {e}")
            return False

    def get_game_stats(self, chat_id: int, db_name: str) -> Tuple[List[Tuple], int, int, int, int, int, int, int]:
        """Возвращает статистику с количеством побед"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Получаем все записи
            cursor.execute(
                'SELECT date_game, team1_score, team2_score FROM database_stats WHERE chat_id = ? AND db_name = ? ORDER BY date_game',
                (chat_id, db_name))
            records = cursor.fetchall()

            # Подсчет побед и ничьих
            team1_wins = 0
            team2_wins = 0
            draws = 0
            goals_team1 = 0
            goals_team2 = 0

            for record in records:
                team1_score = record[1]
                team2_score = record[2]

                goals_team1 += team1_score
                goals_team2 += team2_score

                if team1_score > team2_score:
                    team1_wins += 1
                elif team2_score > team1_score:
                    team2_wins += 1
                else:
                    draws += 1

            # Подсчет очков
            team1_points = team1_wins * 3 + draws
            team2_points = team2_wins * 3 + draws

            conn.close()
            return records, team1_points, team2_points, goals_team1, goals_team2, draws, team1_wins, team2_wins
        except Exception:
            return [], 0, 0, 0, 0, 0, 0, 0

    # Лимит игроков для каждого чата
    def get_limit_player(self, chat_id: int) -> int:
        try:
            # Сначала убедимся, что чат инициализирован
            self._ensure_chat_initialized(chat_id)

            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT setting_value FROM chat_settings WHERE chat_id = ? AND setting_name = ?',
                           (chat_id, 'limit_player'))
            result = cursor.fetchone()
            conn.close()
            return int(result[0]) if result else 14
        except Exception:
            return 14

    def set_limit_player(self, chat_id: int, limit_players: int):
        try:
            # Сначала убедимся, что чат инициализирован
            self._ensure_chat_initialized(chat_id)

            conn = self._get_connection()
            cursor = conn.cursor()

            # Обновляем настройку
            cursor.execute('INSERT OR REPLACE INTO chat_settings(chat_id, setting_name, setting_value) VALUES(?, ?, ?)',
                           (chat_id, 'limit_player', str(limit_players)))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка в set_limit_player: {e}")
            return False

    # Штрафы для каждого чата
    def update_penalty(self, chat_id: int, user_id: int, penalty: bool):
        try:
            # Сначала убедимся, что чат инициализирован
            self._ensure_chat_initialized(chat_id)

            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('SELECT * FROM chat_penalty WHERE chat_id = ? AND user_id = ?', (chat_id, user_id))
            result = cursor.fetchone()

            if result:
                cursor.execute('UPDATE chat_penalty SET penalty = ? WHERE chat_id = ? AND user_id = ?',
                               (penalty, chat_id, user_id))
            else:
                cursor.execute('INSERT INTO chat_penalty (chat_id, user_id, penalty) VALUES (?, ?, ?)',
                               (chat_id, user_id, penalty))

            conn.commit()
            conn.close()
            return True
        except Exception:
            return False

    def get_penalty(self, chat_id: int, user_id: int) -> bool:
        try:
            # Сначала убедимся, что чат инициализирован
            self._ensure_chat_initialized(chat_id)

            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT penalty FROM chat_penalty WHERE chat_id = ? AND user_id = ?', (chat_id, user_id))
            result = cursor.fetchone()
            conn.close()

            if result and len(result) > 0:
                return bool(result[0])
            return False

        except Exception:
            return False

    # Остальные методы (users) остаются без изменений
    def get_user(self, user_id: int) -> Optional[Tuple]:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE id_ = ?', (user_id,))
            result = cursor.fetchone()
            conn.close()
            return result
        except Exception:
            return None

    def update_user(self, user_id: int, name: str, user_name: str) -> Optional[str]:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('SELECT name FROM users WHERE id_ = ?', (user_id,))
            existing_user = cursor.fetchone()

            if existing_user:
                old_name = existing_user[0]
                cursor.execute("UPDATE users SET name = ?, user_name = ? WHERE id_ = ?",
                               (name, user_name, user_id))
                conn.commit()
                conn.close()
                return old_name
            else:
                cursor.execute('INSERT INTO users(id_, name, user_name) VALUES(?, ?, ?)',
                               (user_id, name, user_name))
                conn.commit()
                conn.close()
                return None
        except Exception:
            return None

    def load_user(self, user_id: int, user_first_name: str, user_name: str) -> str:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('SELECT name, user_name FROM users WHERE id_ = ?', (user_id,))
            name_tuple = cursor.fetchone()

            if name_tuple:
                name_u, existing_user_name = name_tuple
                if existing_user_name is None or existing_user_name == '':
                    cursor.execute('UPDATE users SET user_name = ? WHERE id_ = ?', (user_name, user_id))
                    conn.commit()
            else:
                cursor.execute('INSERT INTO users(id_, name, user_name) VALUES(?, ?, ?)',
                               (user_id, user_first_name, user_name))
                conn.commit()
                name_u = user_first_name

            conn.close()
            return name_u
        except Exception:
            return user_first_name

    def get_username_by_name(self, name: str) -> Optional[str]:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT user_name FROM users WHERE name = ?', (name,))
            result = cursor.fetchone()
            conn.close()
            # 🔴 ИСПРАВЛЕНИЕ: возвращаем None если username пустой или None
            if result and result[0] and result[0].strip():
                return result[0]
            return None
        except Exception:
            return None

    def get_current_date(self) -> str:
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d')

    # database.py - добавить эти методы в класс DatabaseManager

    def set_reset_days(self, chat_id: int, days: int):
        """Устанавливает количество дней между обнулениями списка"""
        try:
            # Сначала убедимся, что чат инициализирован
            self._ensure_chat_initialized(chat_id)

            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                'INSERT OR REPLACE INTO chat_settings(chat_id, setting_name, setting_value) VALUES(?, ?, ?)',
                (chat_id, 'reset_days', str(days))
            )

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка в set_reset_days: {e}")
            return False

    def get_reset_days(self, chat_id: int) -> int:
        """Возвращает количество дней между обнулениями списка"""
        try:
            # Сначала убедимся, что чат инициализирован
            self._ensure_chat_initialized(chat_id)

            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                'SELECT setting_value FROM chat_settings WHERE chat_id = ? AND setting_name = ?',
                (chat_id, 'reset_days')
            )
            result = cursor.fetchone()
            conn.close()

            return int(result[0]) if result else 1  # По умолчанию 1 день
        except Exception:
            return 1  # По умолчанию 1 день

    def _migrate_existing_chats(self):
        """Миграция существующих чатов - добавляет настройку reset_days если её нет"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Получаем все существующие чаты
            cursor.execute('SELECT chat_id FROM chats')
            existing_chats = cursor.fetchall()

            migrated_count = 0
            for chat_tuple in existing_chats:
                chat_id = chat_tuple[0]

                # Проверяем, есть ли уже настройка reset_days для этого чата
                cursor.execute(
                    'SELECT setting_value FROM chat_settings WHERE chat_id = ? AND setting_name = ?',
                    (chat_id, 'reset_days')
                )
                existing_setting = cursor.fetchone()

                # Если настройки нет - добавляем значение по умолчанию
                if not existing_setting:
                    cursor.execute(
                        'INSERT INTO chat_settings(chat_id, setting_name, setting_value) VALUES(?, ?, ?)',
                        (chat_id, 'reset_days', '1')
                    )
                    migrated_count += 1
                    print(f"Мигрирован чат {chat_id} - добавлена настройка reset_days")

            if migrated_count > 0:
                conn.commit()
                print(f"Миграция завершена: обновлено {migrated_count} чатов")
            else:
                print("Миграция не требуется - все чаты уже имеют настройку reset_days")

            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка при миграции: {e}")
            return False

    # database.py - добавить в класс DatabaseManager

    def get_all_chat_settings(self, chat_id: int) -> Dict[str, str]:
        """Возвращает все настройки чата в виде словаря"""
        try:
            # Сначала убедимся, что чат инициализирован
            self._ensure_chat_initialized(chat_id)

            conn = self._get_connection()
            cursor = conn.cursor()

            # Получаем все настройки чата
            cursor.execute(
                'SELECT setting_name, setting_value FROM chat_settings WHERE chat_id = ?',
                (chat_id,)
            )
            settings = cursor.fetchall()

            # Получаем информацию о чате
            cursor.execute(
                'SELECT chat_name, active_db FROM chats WHERE chat_id = ?',
                (chat_id,)
            )
            chat_info = cursor.fetchone()

            # Получаем список всех баз данных
            databases = self.get_chat_databases(chat_id)

            conn.close()

            # Формируем словарь с настройками
            settings_dict = {}

            # Основная информация о чате
            if chat_info:
                settings_dict['chat_name'] = chat_info[0] or "Не указано"
                settings_dict['active_db'] = chat_info[1] or 'default'

            # Настройки из таблицы chat_settings
            for setting_name, setting_value in settings:
                settings_dict[setting_name] = setting_value

            # Список баз данных
            settings_dict['all_databases'] = ', '.join(databases) if databases else 'default'

            # Убедимся, что есть все обязательные настройки
            if 'limit_player' not in settings_dict:
                settings_dict['limit_player'] = '14'
            if 'reset_days' not in settings_dict:
                settings_dict['reset_days'] = '1'
            if 'team1_name' not in settings_dict:
                settings_dict['team1_name'] = Constants.DEFAULT_TEAM1_NAME
            if 'team2_name' not in settings_dict:
                settings_dict['team2_name'] = Constants.DEFAULT_TEAM2_NAME

            return settings_dict

        except Exception as e:
            print(f"Ошибка в get_all_chat_settings: {e}")
            # Возвращаем настройки по умолчанию в случае ошибки
            return {
                'chat_name': 'Неизвестно',
                'active_db': 'default',
                'all_databases': 'default',
                'limit_player': '14',
                'reset_days': '1',
                'team1_name': Constants.DEFAULT_TEAM1_NAME,
                'team2_name': Constants.DEFAULT_TEAM2_NAME
            }

    # В класс DatabaseManager добавить методы:

    def set_voting_time(self, chat_id: int, start_hour: int, end_hour: int):
        """Устанавливает время голосования для чата"""
        try:
            self._ensure_chat_initialized(chat_id)

            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                'INSERT OR REPLACE INTO chat_settings(chat_id, setting_name, setting_value) VALUES(?, ?, ?)',
                (chat_id, 'voting_start_hour', str(start_hour))
            )
            cursor.execute(
                'INSERT OR REPLACE INTO chat_settings(chat_id, setting_name, setting_value) VALUES(?, ?, ?)',
                (chat_id, 'voting_end_hour', str(end_hour))
            )

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка в set_voting_time: {e}")
            return False

    def get_voting_time(self, chat_id: int) -> tuple[int, int]:
        """Возвращает время голосования для чата"""
        try:
            self._ensure_chat_initialized(chat_id)

            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                'SELECT setting_value FROM chat_settings WHERE chat_id = ? AND setting_name = ?',
                (chat_id, 'voting_start_hour')
            )
            start_result = cursor.fetchone()

            cursor.execute(
                'SELECT setting_value FROM chat_settings WHERE chat_id = ? AND setting_name = ?',
                (chat_id, 'voting_end_hour')
            )
            end_result = cursor.fetchone()

            conn.close()

            # По умолчанию 0-24 (круглосуточно)
            start_hour = int(start_result[0]) if start_result else 0
            end_hour = int(end_result[0]) if end_result else 24

            return start_hour, end_hour

        except Exception as e:
            print(f"Ошибка в get_voting_time: {e}")
            return 0, 24  # По умолчанию круглосуточно

    # Добавим миграцию для существующих чатов
    def _migrate_voting_time(self):
        """Миграция для установки времени голосования по умолчанию для существующих чатов"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Получаем все существующие чаты
            cursor.execute('SELECT chat_id FROM chats')
            existing_chats = cursor.fetchall()

            migrated_count = 0
            for chat_tuple in existing_chats:
                chat_id = chat_tuple[0]

                # Проверяем, есть ли уже настройки времени голосования
                cursor.execute(
                    'SELECT setting_value FROM chat_settings WHERE chat_id = ? AND setting_name = ?',
                    (chat_id, 'voting_start_hour')
                )
                existing_start = cursor.fetchone()

                # Если настроек нет - устанавливаем по умолчанию 0-24
                if not existing_start:
                    cursor.execute(
                        'INSERT INTO chat_settings(chat_id, setting_name, setting_value) VALUES(?, ?, ?)',
                        (chat_id, 'voting_start_hour', '0')
                    )
                    cursor.execute(
                        'INSERT INTO chat_settings(chat_id, setting_name, setting_value) VALUES(?, ?, ?)',
                        (chat_id, 'voting_end_hour', '24')
                    )
                    migrated_count += 1
                    print(f"Мигрирован чат {chat_id} - установлено время голосования 0-24")

            if migrated_count > 0:
                conn.commit()
                print(f"Миграция времени голосования завершена: обновлено {migrated_count} чатов")

            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка при миграции времени голосования: {e}")
            return False
# Глобальный экземпляр для использования
db = DatabaseManager()
# bots_commands.py
import random
from datetime import datetime
from functools import lru_cache
from typing import List

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CallbackContext

from mix import mix_list
from database import db
from constants import Constants
from time_manager import time_manager
from message_helper import message_helper
from bot_state import bot_state


def sanitize_input(text: str) -> str:
    """Очистка пользовательского ввода"""
    return text.replace('<', '&lt;').replace('>', '&gt;').replace('&', '&amp;')


@lru_cache(maxsize=100)
def get_cached_limit_player() -> int:
    return db.get_limit_player()


# bots_commands.py - обновить функцию stat_create

def stat_create(chat_id: int) -> str:
    """Создает статистику игр для конкретного чата"""
    try:
        active_db = db.get_active_database(chat_id)
        team1_name, team2_name = db.get_team_names(chat_id)
        records, team1_points, team2_points, goals_team1, goals_team2, draws, team1_wins, team2_wins = db.get_game_stats(
            chat_id, active_db)

        message = f'📊 <b>СТАТИСТИКА ИГР</b>\n'
        message += f'<i>База данных:</i> {active_db}\n\n'

        message += f'🏆 <b>Общий счет по очкам:</b>\n'
        message += f'🔵 <b>{team1_name}</b> {team1_points} : {team2_points} <b>🟠 {team2_name}</b>\n\n'

        message += f'⚽ <b>Общий счет по голам:</b>\n'
        message += f'🔵 <b>{team1_name}</b> {goals_team1} : {goals_team2} <b>🟠 {team2_name}</b>\n\n'

        # ОБНОВЛЕНО: Побед с цветами
        message += f'🟢 <b>Побед:</b> <b>{team1_name}</b>: {team1_wins}, <b>{team2_name}</b>: {team2_wins}\n'
        message += f'🤝 <b>Ничьих:</b> {draws}\n\n'

        if records:
            message += f'📅 <b>История последних игр:</b>\n'
            for record in records[-3:]:
                message += f'{record[0]} - 🔵 <b>{team1_name}</b> {record[1]} : {record[2]} 🟠 <b>{team2_name}</b>\n'
            if len(records) > 3:
                message += f'\n<i>... и еще {len(records) - 3} игр</i>\n'
                message += f'<i>📊 подробная аналитика /stat</i>'
        else:
            message += '📝 <i>История игр пока пуста</i>\n'
            message += 'Добавьте первую игру командой /add'

        return message
    except Exception as e:
        print(f"Ошибка в stat_create: {e}")
        return "❌ Ошибка при получении статистики"


def create_message(data: List[str], limit_player: int, number: int, chat_id: int) -> str:
    """Создает форматированное сообщение со списком игроков"""
    try:
        # Получаем статистику для конкретного чата
        stats_text = stat_create(chat_id)

        # Используем всю статистику
        message = stats_text + '\n\n'
        message += '<b>Основной список:</b>\n'
        rezerv = ''
        message_random_data_01 = ''
        message_random_data_02 = ''

        if len(data) == 0:
            return 'Ау, люди вы где?'
        elif len(data) <= limit_player:
            if len(data) < limit_player:
                for i in range(len(data)):
                    message += f'{i + 1}.  {data[i]}\n'
                return message
            elif len(data) == limit_player:
                great_player, loser_player = bot_state.get_great_loser_players()
                players = data[:limit_player]

                # Выбор лучшего и худшего игрока
                if great_player is None or great_player not in players or loser_player not in players:
                    great_player = random.choice([p for p in players if '+1' not in p])
                    remaining_players = [p for p in players if p != great_player and '+1' not in p]
                    if remaining_players:
                        loser_player = random.choice(remaining_players)
                    else:
                        loser_player = great_player

                    bot_state.set_great_loser_players(great_player, loser_player)

                # Форматирование списка
                for i in range(len(data)):
                    message += f'{i + 1}.  {data[i]}\n'

                # Создание команд
                random_data = mix_list(data)
                len_random_data = len(random_data) // 2

                for i in range(len_random_data):
                    message_random_data_01 += f'{i + 1}.  {random_data[i * 2]}\n'
                for i in range(len_random_data):
                    message_random_data_02 += f'{i + 1}.  {random_data[i * 2 + 1]}\n'

                # Получаем названия команд для чата
                team1_name, team2_name = db.get_team_names(chat_id)

                # Прогноз
                winning = random.randint(0, 1)
                winner = team2_name if winning == 0 else team1_name
                loser = team1_name if winning == 0 else team2_name
                loser_num = random.randint(6, 12)
                winner_num = random.randint(loser_num, 20)

                # Получение username
                great_player_display = format_player_display(great_player)
                loser_player_display = format_player_display(loser_player)

                base_message = (
                    f'<i>Набор закрыт.</i>\n\n'
                    f'{message}'
                    f'<b>Рекомендую поделиться так:</b>\n\n'
                    f'🔵 <b>{team1_name}:</b>\n{message_random_data_01}\n'
                    f'🟠 <b>{team2_name}:</b>\n{message_random_data_02}\n'
                    f'<i>Судя по командам, мой прогноз:  🔵 {winner} {winner_num} : {loser_num} 🟠 {loser}.</i>\n\n'
                    f'--------------------------------------------------------\n'
                    f'<b>{message_helper.get_great_player_message()} {great_player_display}.</b>\n'
                    f'<b>А {loser_player_display} {message_helper.get_loser_player_message()}.</b>'
                )

                if number == 2:
                    end_name_mylist = data[limit_player - 1]
                    if '+1' in end_name_mylist:
                        end_name_mylist = data[limit_player - 1][6:]
                    end_name_username = db.get_username_by_name(end_name_mylist)
                    end_name_display = f"@{end_name_username}" if end_name_username else end_name_mylist

                    return f'@{end_name_display} теперь ты или твой игрок в списке\n\n{base_message}'

                return base_message
        else:
            # Обработка резерва
            for i in range(limit_player):
                message += f'{i + 1}.  {data[i]}\n'

            data_rezerv = data[limit_player:]
            for i in range(len(data_rezerv)):
                rezerv += f'{i + 1}.  {data_rezerv[i]}\n'

            if number == 0:
                return f'Ты в резерве!\n\n<b>Резерв!</b>\n{rezerv}\n{message}'
            elif number == 1:
                return f'Твой игрок в резерве!\n\n<b>Резерв!</b>\n{rezerv}\n{message}'
            elif number == 2:
                end_name_mylist = data[limit_player - 1]
                if '+1' in end_name_mylist:
                    end_name_mylist = data[limit_player - 1][6:]
                end_name_username = db.get_username_by_name(end_name_mylist)
                end_name_display = f"@{end_name_username}" if end_name_username else end_name_mylist

                return f'<b>Резерв!</b>\n{rezerv}\n@{end_name_display} теперь ты или твой игрок в списке\n\n{message}'

    except Exception as e:
        print(f"Ошибка в create_message: {e}")
        return "Ошибка при формировании сообщения"


async def run(update: Update, context: ContextTypes):
    """Основной обработчик сообщений"""
    try:
        chat_id = update.message.chat.id
        bot_state.reset_daily_lists(chat_id)
        user_list = bot_state.get_chat_list(chat_id)

        # Автоматически инициализируем чат если нужно
        db._ensure_chat_initialized(chat_id, update.message.chat.title or "Unknown Chat")

        LIMIT_PLAYER = db.get_limit_player(chat_id)

        user_id = update.message.from_user.id
        user_first_name = update.message.from_user.first_name
        user_name = update.message.from_user.username or ""

        stored_name = db.load_user(user_id, user_first_name, user_name)

        # Получаем время голосования для этого чата
        voting_start, voting_end = time_manager.get_voting_time_for_chat(chat_id)
        current_hour = time_manager.get_moscow_time().hour

        # 🔴 ОБНОВЛЕНО: Проверка времени голосования для конкретного чата
        if not time_manager.is_voting_time_for_chat(chat_id):
            await update.message.reply_text(
                f"Голосование доступно с {voting_start}:00 до {voting_end}:00!",
                quote=True, parse_mode='HTML'
            )
            return

        message_text = update.message.text
        mess = ""
        mess_penalty = ""

        if message_text == '+':
            penalty = db.get_penalty(chat_id, user_id)
            if stored_name not in user_list and penalty and not time_manager.can_add_friends():
                mess = (f'У тебя не погашенный штраф с прошлой игры. Тебе сегодня разрешено голосовать c '
                        f'10:00 часов. Что бы узнать о каком штрафе идет '
                        f'речь и как его исправить вызови команду /shtraf.')
            elif stored_name not in user_list:
                db.update_penalty(chat_id, user_id, False)
                user_list.append(stored_name)

                if user_id == 2063531206:  # Serega - только для специальных сообщений
                    mess = (f'{message_helper.format_serega_message()}\n\n'
                            f'{create_message(user_list, LIMIT_PLAYER, 0, chat_id)}')
                else:
                    mess = message_helper.format_player_added(
                        create_message(user_list, LIMIT_PLAYER, 0, chat_id)
                    )
            else:
                mess = message_helper.format_player_exists(stored_name)

        elif message_text == '-':
            if stored_name in user_list:
                if (len(user_list) == LIMIT_PLAYER and
                        time_manager.is_penalty_time()):
                    db.update_penalty(chat_id, user_id, True)
                    mess_penalty = 'Обрати внимание, теперь ты подвергаешься штрафу. Какому? Узнаешь.\n'

                user_list.remove(stored_name)
                mess = (f'{message_helper.format_player_removed("")}'
                        f'{mess_penalty}\n'
                        f'{create_message(user_list, LIMIT_PLAYER, 2, chat_id)}')
            else:
                mess = message_helper.format_player_not_exists()

        elif message_text == '+1':
            # 🔴 ОБНОВЛЕНО: Проверка времени для добавления друзей
            friends_start_hour = voting_start + 1
            if friends_start_hour >= 24:
                friends_start_hour = 0  # Если начало голосования 23:00, то друзья с 0:00

            if current_hour >= friends_start_hour:
                user_plus_1 = f'+1 от {stored_name}'
                user_list.append(user_plus_1)
                mess = (f'{message_helper.format_friend_added()}\n\n'
                        f'{create_message(user_list, LIMIT_PLAYER, 1, chat_id)}')
            else:
                mess = f'Добавлять друзей можно с {friends_start_hour}:00!'

        elif message_text == '-1':
            user_plus_1 = f'+1 от {stored_name}'
            if user_plus_1 in user_list:
                if (len(user_list) == LIMIT_PLAYER and
                        time_manager.is_penalty_time()):
                    db.update_penalty(chat_id, user_id, True)
                    mess_penalty = 'Обрати внимание, теперь ты подвергаешься штрафу. Какому? Узнаешь.\n'

                user_list.remove(user_plus_1)
                mess = (f'{message_helper.format_friend_removed()}\n'
                        f'{mess_penalty}\n'
                        f'{create_message(user_list, LIMIT_PLAYER, 2, chat_id)}')
            else:
                mess = 'Твоего игрока нет в списке!'

        await update.message.reply_text(mess, quote=True, parse_mode='HTML')

    except Exception as e:
        print(f"Ошибка в run: {e}")
        await update.message.reply_text("Произошла ошибка. Попробуйте позже.", quote=True, parse_mode='HTML')


async def help_command(update: Update, context: CallbackContext):
    """Показывает справку по командам и инициализирует чат при первом использовании"""
    try:
        chat_id = update.message.chat.id
        chat_name = update.message.chat.title or "Unknown Chat"

        # Инициализация чата при первом использовании help
        db._ensure_chat_initialized(chat_id, chat_name)

        # Получаем настройки времени голосования для этого чата
        voting_start, voting_end = time_manager.get_voting_time_for_chat(chat_id)
        friends_start = voting_start + 1
        if friends_start >= 24:
            friends_start = 0
        penalty_start = time_manager.get_penalty_start_hour()

        help_text = (
            "📋 <b>ОСНОВНЫЕ КОМАНДЫ:</b>\n"
            "➕ Добавиться в список: отправь '+'\n"
            "➖ Удалиться из списка: отправь '-'\n"
            "👥 Добавить одного игрока: отправь '+1'\n"
            "👤 Удалить одного игрока: отправь '-1'\n\n"

            "📊 <b>СТАТИСТИКА И НАСТРОЙКИ:</b>\n"
            "/stat - посмотреть статистику текущего сезона\n"
            "/settings - показать все настройки чата\n"
            "/list - показать текущий список игроков\n"
            "/del - обнулить список\n\n"

            "⚙️ <b>УПРАВЛЕНИЕ КОМАНДАМИ:</b>\n"
            "/set_teams Название1 Название2 - изменить названия команд\n"
            f"<i>Пример:</i> /set_teams Зенит Спартак\n\n"

            "🗄️ <b>УПРАВЛЕНИЕ БАЗАМИ ДАННЫХ:</b>\n"
            "/create_db название - создать новую базу данных\n"
            "/switch_db название - переключить активную базу\n"
            "/list_dbs - показать доступные базы данных\n"
            f"<i>Пример:</i> /create_db лето2024\n\n"

            "🎯 <b>НАСТРОЙКИ ИГРЫ:</b>\n"
            "/chg_limit_pl 14 - изменить лимит игроков\n"
            "/chg_name Иван - изменить имя в списке\n"
            "/set_reset_days 3 - изменить период обнуления списка\n"
            "/set_voting_time 9 21 - установить время голосования\n\n"

            "📝 <b>ДОБАВЛЕНИЕ СТАТИСТИКИ:</b>\n"
            "/add 3 3 - добавить результат игры\n"
            "<b>Формат:</b> /add голы_команды1 голы_команды2\n\n"

            "⚠️ <b>ШТРАФЫ:</b>\n"
            "/shtraf - узнать о системе штрафов\n"
            "/uznat_shtraf - проверить свой штраф\n\n"

            f"🕒 <b>ВРЕМЯ ГОЛОСОВАНИЯ (текущие настройки):</b>\n"
            f"• Основное голосование: с {voting_start}:00 до {voting_end}:00\n"
            f"• Добавление друзей: с {friends_start}:00 (через 1 час после начала)\n"
            f"• Штрафное время: с {penalty_start}:00\n\n"

            "💡 <b>ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ:</b>\n"
            "/set_teams Красные Синие - сменить названия\n"
            "/create_db осень2024 - создать сезон\n"
            "/add 5 3 - добавить игру 5:3\n"
            "/chg_limit_pl 16 - лимит 16 игроков\n"
            "/set_reset_days 7 - обнулять список раз в неделю\n"
            "/set_voting_time 9 21 - голосование с 9:00 до 21:00\n"
            "/set_voting_time 0 24 - круглосуточное голосование\n\n"

            "⚡ <b>БЫСТРЫЙ СТАРТ:</b>\n"
            "1. Настрой команды: <code>/set_teams Зенит Спартак</code>\n"
            "2. Установи время: <code>/set_voting_time 9 21</code>\n"
            "3. Добавь первую игру: <code>/add 3 2</code>\n"
            "4. Проверь настройки: <code>/settings</code>"
        )
        await update.message.reply_text(help_text, quote=True, parse_mode='HTML')

    except Exception as e:
        print(f"Ошибка в help_command: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при отображении справки",
            quote=True, parse_mode='HTML'
        )


async def show_list_command(update: Update, context: CallbackContext):
    """Показывает текущий список игроков"""
    chat_id = update.message.chat.id
    user_list = bot_state.get_chat_list(chat_id)
    LIMIT_PLAYER = db.get_limit_player(chat_id)
    message = create_message(user_list, LIMIT_PLAYER, 0, chat_id)  # Добавлен chat_id
    await update.message.reply_text(message, quote=True, parse_mode='HTML')


async def change_limit_player(update: Update, context: CallbackContext):
    """Изменяет лимит игроков"""
    print(f"DEBUG: change_limit_player вызвана")  # Отладка

    try:
        chat_id = update.message.chat.id
        print(f"DEBUG: chat_id = {chat_id}, args = {context.args}")  # Отладка

        if len(context.args) == 1 and context.args[0].isdigit():
            limit_players = int(context.args[0])
            print(f"DEBUG: limit_players = {limit_players}")  # Отладка

            if limit_players % 2 != 0:
                await update.message.reply_text(
                    '❌ <b>Ошибка:</b> Лимит игроков должен быть четным числом',
                    quote=True, parse_mode='HTML'
                )
                return

            if limit_players < 4:
                await update.message.reply_text(
                    '❌ <b>Ошибка:</b> Лимит игроков не может быть меньше 4',
                    quote=True, parse_mode='HTML'
                )
                return

            if limit_players > 30:
                await update.message.reply_text(
                    '❌ <b>Ошибка:</b> Лимит игроков не может быть больше 30',
                    quote=True, parse_mode='HTML'
                )
                return

            # Автоматически инициализируем чат если нужно
            db._ensure_chat_initialized(chat_id, update.message.chat.title or "Unknown Chat")

            print(f"DEBUG: Вызываем db.set_limit_player({chat_id}, {limit_players})")  # Отладка
            success = db.set_limit_player(chat_id, limit_players)
            print(f"DEBUG: db.set_limit_player вернул {success}")  # Отладка

            if success:
                await update.message.reply_text(
                    f'✅ <b>Лимит игроков изменен на {limit_players}</b>\n\n'
                    f'Теперь основной список будет содержать до {limit_players} игроков',
                    quote=True, parse_mode='HTML'
                )
            else:
                await update.message.reply_text(
                    '❌ <b>Ошибка при изменении лимита игроков</b>',
                    quote=True, parse_mode='HTML'
                )
        else:
            await update.message.reply_text(
                '📝 <b>Использование:</b> <code>/chg_limit_pl количество_игроков</code>\n\n'
                '<i>Примеры:</i>\n'
                '<code>/chg_limit_pl 14</code> - установить лимит 14 игроков\n'
                '<code>/chg_limit_pl 16</code> - установить лимит 16 игроков\n'
                '<code>/chg_limit_pl 12</code> - установить лимит 12 игроков\n\n'
                '⚠️ <i>Лимит должен быть четным числом (кратным 2)</i>',
                quote=True, parse_mode='HTML'
            )

    except Exception as e:
        print(f"Ошибка в change_limit_player: {e}")
        import traceback
        traceback.print_exc()  # Печать полной трассировки ошибки
        await update.message.reply_text(
            "❌ Произошла ошибка при изменении лимита игроков",
            quote=True
        )


# bots_commands.py - обновить функцию add_goals

# Обновляем функцию add_goals в bots_commands.py

async def add_goals(update: Update, context: CallbackContext):
    """Добавляет статистику игры с веселым отчетом и основной статистикой"""
    try:
        if len(context.args) == 2 and context.args[0].isdigit() and context.args[1].isdigit():
            team1_score = int(context.args[0])
            team2_score = int(context.args[1])

            chat_id = update.message.chat.id

            # Автоматически инициализируем чат если нужно
            db._ensure_chat_initialized(chat_id, update.message.chat.title or "Unknown Chat")

            active_db = db.get_active_database(chat_id)
            team1_name, team2_name = db.get_team_names(chat_id)

            # Получаем текущий список игроков для обновления статистики
            user_list = bot_state.get_chat_list(chat_id)

            # Обновляем статистику игроков
            if user_list:
                db.update_player_stats(chat_id, user_list, active_db)

            if db.add_game_stats(chat_id, active_db, team1_score, team2_score):
                # Получаем топы игроков
                top_attendance = db.get_top_players(chat_id, 'games_played', 3)
                top_friends = db.get_top_players(chat_id, 'friends_added', 3)

                # Проверяем ничью
                is_draw = team1_score == team2_score

                if is_draw:
                    # Фразы для ничьей
                    result_phrase = random.choice(Constants.DRAW_RESULT_PHRASES)
                    best_phrase_template = random.choice(Constants.DRAW_BEST_PLAYER_PHRASES)
                    worst_phrase_template = random.choice(Constants.DRAW_WORST_PLAYER_PHRASES)
                    advice_phrase = random.choice(Constants.DRAW_ADVICE_PHRASES)
                else:
                    # Фразы для обычного матча
                    winning_team = team1_name if team1_score > team2_score else team2_name
                    losing_team = team2_name if team1_score > team2_score else team1_name

                    result_phrase = random.choice(Constants.GAME_RESULT_PHRASES).format(
                        winning_team=winning_team, losing_team=losing_team
                    )
                    best_phrase_template = random.choice(Constants.BEST_PLAYER_PHRASES)
                    worst_phrase_template = random.choice(Constants.WORST_PLAYER_PHRASES)
                    advice_phrase = random.choice(Constants.ADVICE_PHRASES).format(
                        losing_team=losing_team
                    )

                # Выбираем лучшего и худшего игрока
                best_player, worst_player = select_best_worst_players(user_list)
                best_player_display = format_player_display(best_player)
                worst_player_display = format_player_display(worst_player)

                # Случайное количество голов для фраз
                winning_score = max(team1_score, team2_score)
                best_goals = random.randint(1, min(winning_score, 3))
                worst_goals = random.randint(1, min(winning_score, 3))

                # Форматируем фразы с игроками
                best_phrase = best_phrase_template.format(
                    player=best_player_display, goals=best_goals
                )
                worst_phrase = worst_phrase_template.format(
                    player=worst_player_display, goals=worst_goals
                )

                # Генерируем смешную статистику
                funny_stats = []
                for _ in range(3):
                    stat = random.choice(Constants.FUNNY_STATS)
                    random_count = random.randint(5, 12)
                    funny_stats.append(stat.format(random_count=random_count))

                # Форматируем топы игроков
                attendance_text = ""
                top_attendance = db.get_top_players(chat_id, 'games_played', 3)

                if top_attendance:
                    for i, (name, count) in enumerate(top_attendance, 1):
                        username = db.get_username_by_name(name)
                        display_name = f"@{username}" if username else name
                        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
                        attendance_text += f"{medal} {display_name} - {count} игр\n"
                    attendance_text += "\n"
                else:
                    attendance_text += "<i>Пока нет данных о посещаемости</i>\n\n"

                # Топ по друзьям - ТОЛЬКО если есть игроки с друзьями
                friends_text = ""
                top_friends = db.get_top_players(chat_id, 'friends_added', 3)

                if top_friends:
                    for i, (name, count) in enumerate(top_friends, 1):
                        username = db.get_username_by_name(name)
                        display_name = f"@{username}" if username else name
                        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
                        friends_text += f"{medal} {display_name} - {count} друг"
                        # Правильные окончания
                        if count == 1:
                            friends_text += "\n"
                        elif count in [2, 3, 4]:
                            friends_text += "а\n"
                        else:
                            friends_text += "ей\n"
                    friends_text += "\n"
                else:
                    friends_text = "Пока никто не пригласил друзей\n\n"

                # Получаем основную статистику для отображения
                stats_message = stat_create(chat_id)
                if team1_score > team2_score:
                    score_line = f"⚽ <b>Счет:</b> <b><u>{team1_name}</u></b> {team1_score} - {team2_score} {team2_name}\n"
                elif team2_score > team1_score:
                    score_line = f"⚽ <b>Счет:</b> {team1_name} {team1_score} - {team2_score} <b><u>{team2_name}</u></b>\n"
                else:
                    score_line = f"⚽ <b>Счет:</b> {team1_name} {team1_score} - {team2_score} {team2_name}\n"
                # Формируем полный отчет
                report_message = (
                    f"🍻 <b>ОТЧЕТ ОБ ИГРЕ | {db.get_current_date()}</b>\n\n"
                    f"{score_line}\n"
                    f"{result_phrase}\n\n"
                    f"🏆 <b><u>ГЕРОИ ДНЯ</u></b>\n"
                    f"🥇 <b>{best_phrase}</b>\n"  
                    f"📉 <b>{worst_phrase}</b>\n\n"
                    f"📊 <b><u>СТАТИСТИКА МАТЧА</u></b>\n"
                    f"• {funny_stats[0]}\n"
                    f"• {funny_stats[1]}\n"
                    f"• {funny_stats[2]}\n\n"
                    f"💡 <i>СОВЕТ НА СЛЕДУЮЩУЮ ИГРУ:</i>\n"
                    f"<b>{advice_phrase}</b>\n"
                    f"─────────────────────\n\n"
                    f"🏆 <b>ТОП-3 ПО ПОСЕЩАЕМОСТИ:</b>\n{attendance_text}\n"
                    f"👥 <b>ТОП-3 ПО ПРИВЕДЕННЫМ ДРУЗЬЯМ:</b>\n{friends_text}\n"
                    f"─────────────────────\n\n"
                    f"{stats_message}"
                )

                await update.message.reply_text(report_message, quote=True, parse_mode='HTML')
            else:
                await update.message.reply_text(
                    '❌ <u>Ошибка при добавлении статистики.</u>',
                    quote=True, parse_mode='HTML'
                )
        else:
            await update.message.reply_text(
                '📝 <b>Использование:</b> /add голы_первой_команды голы_второй_команды\n\n'
                '<i>Примеры:</i>\n'
                '/add 3 2 - 🔵 команда 3 : 2 🟠 команда\n'
                '/add 0 0 - ничья 0:0\n'
                '/add 5 1 - победа 5:1\n\n'
                '💡 <i>Примечание: можно добавить только одну игру в день. '
                'При повторном использовании команды результат обновится.</i>',
                quote=True, parse_mode='HTML'
            )

    except Exception as e:
        print(f"Ошибка в add_goals: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при добавлении статистики",
            quote=True
        )


def select_best_worst_players(user_list: List[str]) -> tuple:
    """Выбирает лучшего и худшего игрока из списка"""
    try:
        # Фильтруем только основных игроков (без +1)
        main_players = [player for player in user_list if '+1 от' not in player]

        if len(main_players) >= 2:
            # Если есть хотя бы 2 основных игрока - выбираем случайных
            best_player, worst_player = random.sample(main_players, 2)
        elif len(main_players) == 1:
            # Если только один основной игрок
            best_player = main_players[0]
            # Пытаемся найти другого игрока (даже с +1)
            other_players = [player for player in user_list if player != best_player]
            if other_players:
                worst_player = random.choice(other_players)
            else:
                worst_player = best_player  # fallback - один игрок в обеих ролях
        else:
            # Если нет основных игроков (только +1)
            if len(user_list) >= 2:
                best_player, worst_player = random.sample(user_list, 2)
            elif len(user_list) == 1:
                best_player = user_list[0]
                worst_player = user_list[0]
            else:
                # Пустой список
                best_player = "Неизвестный игрок"
                worst_player = "Неизвестный игрок"

        return best_player, worst_player

    except Exception as e:
        print(f"Ошибка в select_best_worst_players: {e}")
        return "Неизвестный игрок", "Неизвестный игрок"


def format_player_display(player_name: str) -> str:
    """Форматирует имя игрока для отображения - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    try:
        # Если это основной игрок
        if '+1 от' not in player_name:
            username = db.get_username_by_name(player_name)
            # 🔴 ИСПРАВЛЕНИЕ: если username нет, используем name
            return f"@{username}" if username else player_name
        else:
            # Если это +1 игрок, извлекаем основное имя
            main_player = player_name.replace('+1 от ', '')
            username = db.get_username_by_name(main_player)
            # 🔴 ИСПРАВЛЕНИЕ: если username нет, используем оригинальное имя
            return f"+1 от @{username}" if username else player_name

    except Exception as e:
        print(f"Ошибка в format_player_display: {e}")
        return player_name


async def change_name(update: Update, context: CallbackContext):
    """Изменяет имя пользователя в списке"""
    chat_id = update.message.chat.id
    user_list = bot_state.get_chat_list(chat_id)

    if 0 < len(context.args) < 3:
        new_name = ' '.join([sanitize_input(arg.title()) for arg in context.args])
        user_id = update.message.from_user.id
        user_name = update.message.from_user.username or ""

        old_name = db.update_user(user_id, new_name, user_name)
        if old_name:
            # Обновляем имя в текущем списке
            user_list[:] = [new_name if x == old_name else x for x in user_list]
            user_list[:] = [f'+1 от {new_name}' if x == f'+1 от {old_name}' else x for x in user_list]

            await update.message.reply_text(
                f'<u>Имя {old_name} изменено на {new_name}.</u>',
                quote=True, parse_mode='html'
            )
        else:
            await update.message.reply_text(
                f'<u>Имя {update.message.from_user.first_name} изменено на {new_name}.</u>',
                quote=True, parse_mode='html'
            )
    else:
        await update.message.reply_text(
            '<u>Ошибка при добавлении имени. Введи /help для помощи</u>',
            quote=True, parse_mode='html'
        )


async def del_command(update: Update, context: ContextTypes):
    """Очищает список игроков"""
    chat_id = update.message.chat.id
    user_list = bot_state.get_chat_list(chat_id)
    user_list.clear()
    await update.message.reply_text("Эээ, список кто-то ёбнул", quote=True)


async def tela_tela(context: ContextTypes):
    """Напоминание о футболе"""
    try:
        for chat_id in bot_state.group_lists:
            user_list = bot_state.group_lists[chat_id]
            LIMIT_PLAYER = get_cached_limit_player()

            if len(user_list) < LIMIT_PLAYER:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text='Тела, тела, тела, тела, тела, тела....',
                    parse_mode='Markdown'
                )
    except Exception:
        pass


# bots_commands.py - обновить функцию stats_command

async def stats_command(update: Update, context: CallbackContext):
    """Показывает компактную сводную статистику с историей игр"""
    try:
        chat_id = update.message.chat.id
        active_db = db.get_active_database(chat_id)
        records, team1_points, team2_points, goals_team1, goals_team2, draws, team1_wins, team2_wins = db.get_game_stats(
            chat_id, active_db)
        team1_name, team2_name = db.get_team_names(chat_id)

        if not records:
            await update.message.reply_text(
                "📊 <b>Статистика пока пуста</b>\n\n"
                "Добавьте первую игру командой:\n"
                "<code>/add 3 2</code>",
                quote=True, parse_mode='HTML'
            )
            return

        total_games = len(records)
        current_year = datetime.now().year

        # Получаем статистику игроков только для топов
        top_attendance = db.get_top_players(chat_id, 'games_played', 3)
        top_friends = db.get_top_players(chat_id, 'friends_added', 3)

        # Расчет средней забиваемости
        team1_avg_goals = goals_team1 / total_games
        team2_avg_goals = goals_team2 / total_games

        # Текущие серии
        streaks = _calculate_current_streaks(records)

        # Самые результативные игры (топ-3)
        top_games = sorted(records, key=lambda x: x[1] + x[2], reverse=True)[:3]

        # Динамика по месяцам текущего года
        monthly_stats = _calculate_monthly_stats_current_year(records)

        # История последних игр (последние 5)
        recent_games = records[-5:] if len(records) >= 5 else records

        # Форматируем сообщение
        message = f"📊 <b>ПОЛНАЯ СТАТИСТИКА СЕЗОНА {current_year}</b>\n\n"

        # Общий счет
        message += f"🏆 <b>ОБЩИЙ СЧЕТ:</b>\n"
        message += f"🔵 {team1_name}   {team1_points} : {team2_points}   🟠 {team2_name}\n\n"

        # Голы
        message += f"⚽ <b>ЗАБИТЫЕ ГОЛЫ:</b>\n"
        message += f"🔵 {team1_name}: {goals_team1} голов ({team1_avg_goals:.2f} за игру)\n"
        message += f"🟠 {team2_name}: {goals_team2} голов ({team2_avg_goals:.2f} за игру)\n\n"

        # Побед и ничьих с цветами
        message += f"🎯 <b>РЕЗУЛЬТАТЫ:</b>\n"
        message += f"🟢 <b>Побед:</b> {team1_name} - {team1_wins}, {team2_name} - {team2_wins}\n"
        message += f"🤝 <b>Ничьих:</b> {draws}\n\n"

        # Топ по посещаемости
        message += f"🏅 <b>ТОП ПО ПОСЕЩАЕМОСТИ:</b>\n"
        if top_attendance:
            for i, (name, count) in enumerate(top_attendance, 1):
                username = db.get_username_by_name(name)
                display_name = f"@{username}" if username else name
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
                message += f"{medal} {display_name} - {count} игр\n"
        else:
            message += "Пока нет данных\n"
        message += "\n"

        # Топ по друзьям
        message += f"🤝 <b>ТОП ПО ПРИВЕДЕННЫМ ДРУЗЬЯМ:</b>\n"
        if top_friends:
            for i, (name, count) in enumerate(top_friends, 1):
                username = db.get_username_by_name(name)
                display_name = f"@{username}" if username else name
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
                message += f"{medal} {display_name} - {count} друзей\n"
        else:
            message += "Пока нет данных\n"
        message += "\n"

        # Остальные блоки:

        # Динамика по месяцам
        message += f"📈 <b>ДИНАМИКА ПОБЕД ПО МЕСЯЦАМ:</b>\n"
        if monthly_stats:
            for month, stats in monthly_stats.items():
                month_name = _format_month_name_short(month)
                message += f"{month_name}: 🔵{stats['team1_wins']}-{stats['team2_wins']}🟠"
                if stats['draws'] > 0:
                    message += f" ({stats['draws']}🤝)"
                message += "\n"
        else:
            message += "<i>Нет данных по месяцам</i>\n"
        message += "\n"

        # Самые результативные игры
        message += f"🎯 <b>САМЫЕ РЕЗУЛЬТАТИВНЫЕ ИГРЫ:</b>\n"
        if top_games:
            for game in top_games:
                date_str = game[0][8:10] + "." + game[0][5:7]  # DD.MM формат
                message += f"• {date_str}: {team1_name} {game[1]} - {game[2]} {team2_name}\n"
        else:
            message += "<i>Нет данных об играх</i>\n"
        message += "\n"

        # Текущие серии
        message += f"🔥 <b>ТЕКУЩАЯ СЕРИЯ:</b>\n"
        streak1_msg = _format_streak_compact(streaks["team1_streak"], streaks["team1_type"], team1_name)
        streak2_msg = _format_streak_compact(streaks["team2_streak"], streaks["team2_type"], team2_name)

        if streak1_msg:
            message += f"{streak1_msg}\n"
        if streak2_msg:
            message += f"{streak2_msg}\n"

        if not streak1_msg and not streak2_msg:
            message += "<i>Нет активных серий</i>\n"

        message += "\n"

        # История последних игр
        message += f"📅 <b>ИСТОРИЯ ПОСЛЕДНИХ ИГР:</b>\n"
        if recent_games:
            # Реверсируем чтобы последняя игра была внизу
            recent_games_display = list(reversed(recent_games))
            for game in recent_games_display:
                date_str = game[0][8:10] + "." + game[0][5:7]  # DD.MM формат
                # Добавляем эмодзи в зависимости от результата
                if game[1] > game[2]:
                    result_emoji = "✅"
                elif game[1] < game[2]:
                    result_emoji = "❌"
                else:
                    result_emoji = "⚪"

                message += f"{result_emoji} {date_str}: {team1_name} {game[1]} - {game[2]} {team2_name}\n"
        else:
            message += "<i>Нет данных об играх</i>\n"

        await update.message.reply_text(message, quote=True, parse_mode='HTML')

    except Exception as e:
        print(f"Ошибка в stats_command: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при получении статистики",
            quote=True, parse_mode='HTML'
        )


def _calculate_monthly_stats_current_year(records):
    """Рассчитывает статистику по месяцам текущего года"""
    current_year = datetime.now().year
    monthly_stats = {}

    for record in records:
        date_str = record[0]
        year = int(date_str[:4])

        # Только игры текущего года
        if year == current_year:
            year_month = date_str[:7]  # YYYY-MM

            if year_month not in monthly_stats:
                monthly_stats[year_month] = {
                    "team1_wins": 0,
                    "team2_wins": 0,
                    "draws": 0
                }

            if record[1] > record[2]:
                monthly_stats[year_month]["team1_wins"] += 1
            elif record[2] > record[1]:
                monthly_stats[year_month]["team2_wins"] += 1
            else:
                monthly_stats[year_month]["draws"] += 1

    # Сортируем по месяцам
    return dict(sorted(monthly_stats.items()))


def _format_month_name_short(month_str):
    """Форматирует короткое название месяца"""
    months = {
        "01": "Янв", "02": "Фев", "03": "Мар", "04": "Апр",
        "05": "Май", "06": "Июн", "07": "Июл", "08": "Авг",
        "09": "Сен", "10": "Окт", "11": "Ноя", "12": "Дек"
    }

    year, month = month_str.split("-")
    month_name = months.get(month, month)
    return month_name


def _format_streak_compact(streak_count, streak_type, team_name):
    """Компактное форматирование серии"""
    if streak_count == 0:
        return ""

    if streak_type == "win":
        return f"{team_name}: {streak_count} победы подряд"
    elif streak_type == "lose":
        return f"{team_name}: {streak_count} поражение"
    elif streak_type == "draw":
        return f"{team_name}: {streak_count} ничьих подряд"

    return ""


async def fine_command(update: Update, context: CallbackContext):
    """Объясняет систему штрафов"""
    try:
        penalty_start = time_manager.get_penalty_start_hour()

        await update.message.reply_text(
            f'<b>Ты получил штраф, потому что одновременно совпало 4 условия:</b>\n'
            f'1) Ты поставил "-" или "-1".\n'
            f'2) Было это сделано после {penalty_start}:00 ч.\n'
            f'3) Был уже полный набор списка игроков.\n'
            f'4) Не было в резерве игроков.\n\n'
            f'<b>В общем ты подвел ребят. Не делай так больше.</b>\n'
            f'Когда ты придешь на игру, штраф исчезнет.\n\n'
            f"<code>/uznat_shtraf</code> - узнать есть у тебя штраф или нет",
            quote=True, parse_mode='HTML'
        )
    except Exception as e:
        print(f"Ошибка в fine_command: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при отображении информации о штрафах",
            quote=True, parse_mode='HTML'
        )


async def fine_get(update: Update, context: CallbackContext):
    """Показывает статус штрафа пользователя"""
    try:
        chat_id = update.message.chat.id
        user_id = update.message.from_user.id

        # Автоматически инициализируем чат если нужно
        db._ensure_chat_initialized(chat_id, update.message.chat.title or "Unknown Chat")

        has_penalty = db.get_penalty(chat_id, user_id)

        if has_penalty:
            message = (
                "⚠️ К сожалению, у тебя ЕСТЬ штраф!\n\n"
                "📋 Что это значит:\n"
                "• Ты не сможешь добавляться в список до 10:00\n"
                "• Штраф снимается автоматически при следующей игре\n\n"
                "💡 Как снять штраф:\n"
                "Просто приди на следующую игру и добавься в список"
            )
        else:
            message = (
                "✅ Поздравляю, у тебя НЕТ штрафа!\n\n"
                "Ты можешь свободно добавляться в список в любое время голосования"
            )

        await update.message.reply_text(message, quote=True, parse_mode='Markdown')

    except Exception as e:
        print(f"Ошибка в fine_get: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при проверке штрафа",
            quote=True
        )


async def set_teams_command(update: Update, context: CallbackContext):
    """Устанавливает названия команд"""
    chat_id = update.message.chat.id

    if len(context.args) == 2:
        team1 = context.args[0]
        team2 = context.args[1]

        if db.set_team_names(chat_id, team1, team2):
            await update.message.reply_text(
                f'<u>Названия команд изменены:\n{team1} vs {team2}</u>',
                quote=True, parse_mode='html'
            )
        else:
            await update.message.reply_text(
                '<u>Ошибка при изменении названий команд.</u>',
                quote=True, parse_mode='html'
            )
    else:
        await update.message.reply_text(
            '<u>Использование: /set_teams Название1 Название2</u>',
            quote=True, parse_mode='html'
        )


async def create_db_command(update: Update, context: CallbackContext):
    """Создает новую базу данных"""
    chat_id = update.message.chat.id

    if len(context.args) == 1:
        db_name = context.args[0]

        if db.create_database(db_name, chat_id, update.message.chat.title or "Unknown Chat"):
            # Получаем активную базу для подтверждения
            active_db = db.get_active_database(chat_id)
            await update.message.reply_text(
                f'✅ <b>База данных "{db_name}" создана и активирована!</b>\n\n'
                f'📊 <i>Активная база:</i> <code>{active_db}</code>\n'
                f'💡 <i>Теперь вся статистика будет сохраняться в эту базу</i>\n\n'
                f'Используйте команды:\n'
                f'<code>/add 3 2</code> - добавить игру\n'
                f'<code>/list_dbs</code> - посмотреть все базы\n'
                f'<code>/switch_db название</code> - переключить базу',
                quote=True, parse_mode='HTML'
            )
        else:
            await update.message.reply_text(
                f'❌ <b>Ошибка:</b> База данных "{db_name}" уже существует!\n\n'
                f'Используйте другое название или переключитесь на неё:\n'
                f'<code>/switch_db {db_name}</code>',
                quote=True, parse_mode='HTML'
            )
    else:
        await update.message.reply_text(
            '📝 <b>Использование:</b> <code>/create_db название_базы</code>\n\n'
            '<i>Примеры:</i>\n'
            '<code>/create_db лето2024</code> - создать базу для летнего сезона\n'
            '<code>/create_db осень2024</code> - создать базу для осеннего сезона\n'
            '<code>/create_db тестовая</code> - создать тестовую базу\n\n'
            '💡 <i>После создания база сразу становится активной</i>',
            quote=True, parse_mode='HTML'
        )


async def switch_db_command(update: Update, context: CallbackContext):
    """Переключает активную базу данных"""
    chat_id = update.message.chat.id

    if len(context.args) == 1:
        db_name = context.args[0]

        if db.switch_database(chat_id, db_name):
            # Получаем активную базу для подтверждения
            active_db = db.get_active_database(chat_id)
            await update.message.reply_text(
                f'✅ <b>Активная база данных изменена на "{db_name}"</b>\n\n'
                f'📊 <i>Теперь активна:</i> <code>{active_db}</code>\n'
                f'💡 <i>Вся новая статистика будет сохраняться в эту базу</i>',
                quote=True, parse_mode='HTML'
            )
        else:
            await update.message.reply_text(
                f'❌ <b>Ошибка:</b> База данных "{db_name}" не найдена!\n\n'
                f'Используйте <code>/list_dbs</code> чтобы посмотреть доступные базы\n'
                f'Или создайте новую: <code>/create_db {db_name}</code>',
                quote=True, parse_mode='HTML'
            )
    else:
        # Показать доступные базы данных
        databases = db.get_chat_databases(chat_id)
        active_db = db.get_active_database(chat_id)

        if databases:
            message = '<b>📊 Доступные базы данных:</b>\n\n'
            for db_name in databases:
                if db_name == active_db:
                    message += f'• <b>{db_name}</b> (активна) ✅\n'
                else:
                    message += f'• {db_name}\n'

            message += f'\n💡 <b>Использование:</b> <code>/switch_db название_базы</code>'
        else:
            message = '<b>📊 Базы данных:</b>\n\n'
            message += 'Нет созданных баз данных.\n'
            message += 'Создайте первую: <code>/create_db лето2024</code>'

        await update.message.reply_text(message, quote=True, parse_mode='HTML')


async def list_dbs_command(update: Update, context: CallbackContext):
    """Показывает список доступных баз данных"""
    try:
        chat_id = update.message.chat.id

        # Автоматически инициализируем чат если нужно
        db._ensure_chat_initialized(chat_id, update.message.chat.title or "Unknown Chat")

        databases = db.get_chat_databases(chat_id)
        active_db = db.get_active_database(chat_id)

        if databases:
            message = "<u>📊 Доступные базы данных:</u>\n\n"
            for db_name in databases:
                if db_name == active_db:
                    message += f"• <b>{db_name}</b> (активна) ✅\n"
                else:
                    message += f"• {db_name}\n"

            message += f"\n💡 <b>Команды для управления:</b>\n"
            message += f"<code>/create_db название</code> - создать новую базу\n"
            message += f"<code>/switch_db название</code> - переключить базу\n"
            message += f"<code>/add 3 2</code> - добавить игру в активную базу"
        else:
            message = "<u>📊 Базы данных:</u>\n\n"
            message += "Нет созданных баз данных.\n"
            message += "Используйте /create_db название для создания новой базы\n"
            message += "<i>Пример:</i> <code>/create_db лето2024</code>"

        await update.message.reply_text(message, quote=True, parse_mode='HTML')

    except Exception as e:
        print(f"Ошибка в list_dbs_command: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при получении списка баз данных",
            quote=True
        )

    except Exception as e:
        print(f"Ошибка в list_dbs_command: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при получении списка баз данных",
            quote=True
        )


# bots_commands.py - добавить эту функцию

async def set_reset_days_command(update: Update, context: CallbackContext):
    """Устанавливает количество дней между обнулениями списка"""
    chat_id = update.message.chat.id

    if len(context.args) == 1 and context.args[0].isdigit():
        days = int(context.args[0])

        if days < 1 or days > 7:
            await update.message.reply_text(
                '❌ <b>Ошибка:</b> Количество дней должно быть от 1 до 7',
                quote=True, parse_mode='HTML'
            )
            return

        if db.set_reset_days(chat_id, days):
            await update.message.reply_text(
                f'✅ <b>Настройки обновлены!</b>\n\n'
                f'📅 <i>Список игроков теперь будет обнуляться каждые {days} дней</i>\n\n'
                f'💡 <i>Текущий список будет сохранен до следующего обнуления</i>',
                quote=True, parse_mode='HTML'
            )
        else:
            await update.message.reply_text(
                '❌ <b>Ошибка при изменении настроек</b>',
                quote=True, parse_mode='HTML'
            )
    else:
        current_days = db.get_reset_days(chat_id)
        await update.message.reply_text(
            f'📅 <b>Текущие настройки обнуления:</b> каждые {current_days} дней\n\n'
            f'📝 <b>Использование:</b> <code>/set_reset_days количество_дней</code>\n\n'
            f'<i>Примеры:</i>\n'
            f'<code>/set_reset_days 1</code> - обнулять каждый день\n'
            f'<code>/set_reset_days 3</code> - обнулять каждые 3 дня\n'
            f'<code>/set_reset_days 7</code> - обнулять раз в неделю\n\n'
            f'⚠️ <i>Допустимые значения: от 1 до 7 дней</i>',
            quote=True, parse_mode='HTML'
        )

    # bots_commands.py - добавить эту функцию


async def show_chat_settings(update: Update, context: CallbackContext):
    """Показывает все настройки чата"""
    try:
        chat_id = update.message.chat.id
        settings = db.get_all_chat_settings(chat_id)
        start_hour, end_hour = time_manager.get_voting_time_for_chat(chat_id)

        # Форматируем сообщение
        message = (
            f'⚙️ <b>НАСТРОЙКИ ЧАТА</b>\n\n'

            f'📋 <b>Основная информация:</b>\n'
            f'• <b>Название группы:</b> {settings.get("chat_name", "Не указано")}\n'
            f'• <b>ID чата:</b> <code>{chat_id}</code>\n\n'

            f'👥 <b>Настройки игры:</b>\n'
            f'• <b>Лимит игроков:</b> {settings.get("limit_player", "14")}\n'
            f'• <b>Команда 1:</b> {settings.get("team1_name", Constants.DEFAULT_TEAM1_NAME)}\n'
            f'• <b>Команда 2:</b> {settings.get("team2_name", Constants.DEFAULT_TEAM2_NAME)}\n'
            f'• <b>Обнуление списка:</b> каждые {settings.get("reset_days", "1")} дней\n'
            f'• <b>Время голосования:</b> с {start_hour}:00 до {end_hour}:00\n\n'

            f'🗄️ <b>Базы данных:</b>\n'
            f'• <b>Активная база:</b> {settings.get("active_db", "default")}\n'
            f'• <b>Все базы:</b> {settings.get("all_databases", "default")}\n\n'

            f'💡 <b>Команды для изменения:</b>\n'
            f'<code>/set_teams Название1 Название2</code> - изменить названия команд\n'
            f'<code>/chg_limit_pl 14</code> - изменить лимит игроков\n'
            f'<code>/set_reset_days 3</code> - изменить период обнуления\n'
            f'<code>/switch_db название</code> - переключить базу данных\n'
            f'<code>/create_db название</code> - создать новую базу'
        )

        await update.message.reply_text(message, quote=True, parse_mode='HTML')

    except Exception as e:
        print(f"Ошибка в show_chat_settings: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при получении настроек чата",
            quote=True, parse_mode='HTML'
        )


def _calculate_current_streaks(records):
    """Рассчитывает текущие серии побед/поражений"""
    if not records:
        return {"team1_streak": 0, "team2_streak": 0, "team1_type": "", "team2_type": ""}

    # Берем последние игры для анализа серий
    recent_games = records[-10:]  # Анализируем последние 10 игр
    recent_games.reverse()  # Сначала последние игры

    team1_streak = 0
    team2_streak = 0
    team1_type = ""
    team2_type = ""

    # Анализ для команды 1
    for game in recent_games:
        team1_score, team2_score = game[1], game[2]

        if team1_type == "":
            if team1_score > team2_score:
                team1_type = "win"
                team1_streak = 1
            elif team1_score < team2_score:
                team1_type = "lose"
                team1_streak = 1
            else:
                team1_type = "draw"
                team1_streak = 1
        else:
            if (team1_type == "win" and team1_score > team2_score) or \
                    (team1_type == "lose" and team1_score < team2_score) or \
                    (team1_type == "draw" and team1_score == team2_score):
                team1_streak += 1
            else:
                break

    # Анализ для команды 2
    for game in recent_games:
        team1_score, team2_score = game[1], game[2]

        if team2_type == "":
            if team2_score > team1_score:
                team2_type = "win"
                team2_streak = 1
            elif team2_score < team1_score:
                team2_type = "lose"
                team2_streak = 1
            else:
                team2_type = "draw"
                team2_streak = 1
        else:
            if (team2_type == "win" and team2_score > team1_score) or \
                    (team2_type == "lose" and team2_score < team1_score) or \
                    (team2_type == "draw" and team2_score == team1_score):
                team2_streak += 1
            else:
                break

    return {
        "team1_streak": team1_streak,
        "team2_streak": team2_streak,
        "team1_type": team1_type,
        "team2_type": team2_type
    }


async def set_voting_time_command(update: Update, context: CallbackContext):
    """Устанавливает время голосования для чата"""
    chat_id = update.message.chat.id

    if len(context.args) == 2 and context.args[0].isdigit() and context.args[1].isdigit():
        start_hour = int(context.args[0])
        end_hour = int(context.args[1])

        # Проверка валидности времени
        if not (0 <= start_hour <= 23 and 0 <= end_hour <= 24):
            await update.message.reply_text(
                '❌ <b>Ошибка:</b> Часы должны быть от 0 до 23, конечный час от 0 до 24',
                quote=True, parse_mode='HTML'
            )
            return

        # Проверка что начало < конец (минимальный интервал 1 час)
        if start_hour >= end_hour:
            await update.message.reply_text(
                '❌ <b>Ошибка:</b> Время начала должно быть меньше времени окончания',
                quote=True, parse_mode='HTML'
            )
            return

        # Проверка минимального интервала (1 час)
        if end_hour - start_hour < 1:
            await update.message.reply_text(
                '❌ <b>Ошибка:</b> Минимальный интервал голосования - 1 час',
                quote=True, parse_mode='HTML'
            )
            return

        if db.set_voting_time(chat_id, start_hour, end_hour):
            await update.message.reply_text(
                f'✅ <b>Время голосования установлено!</b>\n\n'
                f'🕒 <i>Голосование теперь доступно:</i>\n'
                f'• <b>С {start_hour}:00 до {end_hour}:00</b>\n\n'
                f'💡 <i>Чтобы сделать голосование круглосуточным, используйте:</i>\n'
                f'<code>/set_voting_time 0 24</code>',
                quote=True, parse_mode='HTML'
            )
        else:
            await update.message.reply_text(
                '❌ <b>Ошибка при изменении времени голосования</b>',
                quote=True, parse_mode='HTML'
            )
    else:
        # Показываем текущие настройки
        start_hour, end_hour = time_manager.get_voting_time_for_chat(chat_id)

        await update.message.reply_text(
            f'🕒 <b>Текущее время голосования:</b> с {start_hour}:00 до {end_hour}:00\n\n'
            f'📝 <b>Использование:</b> <code>/set_voting_time начало_час конец_час</code>\n\n'
            f'<i>Примеры:</i>\n'
            f'<code>/set_voting_time 9 21</code> - с 9:00 до 21:00\n'
            f'<code>/set_voting_time 0 24</code> - круглосуточно\n'
            f'<code>/set_voting_time 18 23</code> - с 18:00 до 23:00\n\n'
            f'⚠️ <i>Минимальный интервал - 1 час</i>',
            quote=True, parse_mode='HTML'
        )
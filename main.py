# main.py
from config import TOKEN
from telegram.ext import CommandHandler, MessageHandler, filters, ApplicationBuilder, CallbackQueryHandler
from bots_commands import *

app = ApplicationBuilder().token(TOKEN).build()
filter_text = ['+', '-', '+1', '-1']

app.add_handler(CommandHandler("help", help_command))  # помощь
app.add_handler(CommandHandler("shtraf", fine_command))
app.add_handler(CommandHandler("uznat_shtraf", fine_get))
app.add_handler(CommandHandler("stat", stats_command))  # показать статистику
app.add_handler(CommandHandler("list", show_list_command))  # показать текущий список ← ДОБАВИТЬ ЭТУ СТРОЧКУ
app.add_handler(MessageHandler(filters.Text(filter_text), callback=run))  # работа со списком
app.add_handler(CommandHandler("del", del_command))  # очистить список
app.add_handler(CommandHandler("add", add_goals))  # добавить голы в статистику
app.add_handler(CommandHandler("chg_name", change_name))  # поменять имя в списке
app.add_handler(CommandHandler("chg_limit_pl", change_limit_player))  # поменять лимит игроков списка
app.add_handler(CommandHandler("set_teams", set_teams_command))  # изменить названия команд
app.add_handler(CommandHandler("create_db", create_db_command))  # создать новую базу
app.add_handler(CommandHandler("switch_db", switch_db_command))  # переключить базу
app.add_handler(CommandHandler("list_dbs", list_dbs_command))
app.add_handler(CommandHandler("set_reset_days", set_reset_days_command))  # настройка дней обнуления
app.add_handler(CommandHandler("settings", show_chat_settings))
app.add_handler(CommandHandler("set_voting_time", set_voting_time_command))
# app.add_handler(CallbackQueryHandler(button))  # кнопки
# app.add_handler(MessageHandler(filters.TEXT, callback=log)) # логирование

# app.job_queue.run_repeating(tela_tela, interval=6000, first=18000) # теле тела тела

print('start')
app.run_polling(stop_signals=None)
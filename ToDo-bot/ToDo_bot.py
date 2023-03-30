import telebot
from telebot import types
import sqlite3
import datetime
from datetime import date

# Создаем объект бота
bot = telebot.TeleBot('TOKEN')

# создаем подключение к базе данных
conn = sqlite3.connect('tasks.db', check_same_thread=False)

# создаем таблицу "tasks"
conn.execute("""CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, task TEXT, priority INTEGER, date TEXT);""")

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start_handler(message):
    bot.send_message(message.chat.id, 'Привет! Я бот для управления ToDo листом. Чтобы увидеть список команд, нажми /help')

# обработчик команды /help
@bot.message_handler(commands=['help'])
def help_handler(message):
    commands_text = '/start - начать работу с ботом\n' \
                    '/add_task [Приоритет] [Задача] [DD.MM.YYYY] - добавить задачу с приоритетом от 1 до 9 с определённым сроком сдачи\n' \
                    '/view_tasks - просмотреть список задач\n' \
                    '/date_tasks [DD.MM.YYYY] - посмотреть задачи, поставленные на данную дату\n' \
                    '/delete_task [Номер задачи] - удалить задачу\n' \
                    '/help - просмотреть список команд'
    bot.send_message(message.chat.id, f'Доступные команды:\n{commands_text}')

# Обработчик команды /add_task
@bot.message_handler(commands=['add_task'])
def add_task_handler(message):
    # Получаем id пользователя
    user_id = message.from_user.id
    # Получаем текст задачи
    task_text = message.text.replace('/add_task ', '')
    # Получаем приоритет
    priority = task_text[0]
    task_date = task_text[-10:]
    try:
        task_date = datetime.datetime.strptime(task_date, '%d.%m.%Y')
    except:
        bot.send_message(message.chat.id, f'Дата указана неверно.')
    if priority.isnumeric() == False:
        bot.send_message(message.chat.id, f'Приоритет указан неверно.')
    elif int(priority) > 9 or int(priority) < 0:
        bot.send_message(message.chat.id, f'Приоритет указан неверно.')
    elif task_date.year < date.today().year:
        bot.send_message(message.chat.id, f'Указанный год уже прошёл.')
    elif task_date.year == date.today().year and task_date.month < date.today().month:
        bot.send_message(message.chat.id, f'Указанный месяц уже прошёл.')
    elif task_date.year == date.today().year and task_date.month == date.today().month and task_date.day < date.today().day:
        bot.send_message(message.chat.id, f'Указанная дата уже прошла.')
    else:
        # Добавляем задачу в список
        conn.execute("""INSERT INTO tasks (user_id, task, priority, date) VALUES (?, ?, ?, ?)""",
                    (user_id, task_text[2:], int(priority), str(task_date)))
        conn.commit()
        # Выводим сообщение об успешном выполнении
        bot.send_message(message.chat.id, f'Задача {task_text[2:-9]} добавлена с приоритетом {priority} на {task_date.date()}.')

# Обработчик команды /view_tasks
@bot.message_handler(commands=['view_tasks'])
def view_tasks_handler(message):
    # Получаем id пользователя
    user_id = message.from_user.id
    # Создаём список задач, уникальный для пользователя
    cursor = conn.execute("""SELECT task FROM tasks WHERE user_id = ? ORDER BY date, priority DESC""", (user_id,))
    tasks = [row[0] for row in cursor.fetchall()]
    # Выводим список
    if tasks:
        tasks_text = '\n'.join([f'{i + 1}. {task} ' for i, task in enumerate(tasks)])
        bot.send_message(message.chat.id, f'Список задач:\n{tasks_text}')
    else:
        # Если список задач пуст, сообщаем об этом
        bot.send_message(message.chat.id, 'Список задач пуст.')

# Обработчик команды /delete_task
@bot.message_handler(commands=['delete_task'])
def delete_task_handler(message):
    # Получаем id пользователя
    user_id = message.from_user.id
    # Получаем номер задачи, которую нужно удалить
    cursor = conn.execute("""SELECT task FROM tasks WHERE user_id = ? ORDER BY date, priority DESC""", (user_id,))
    tasks = [row[0] for row in cursor.fetchall()]
    # Проверяем номер удаляемой задачи
    task_number = message.text.replace('/delete_task ', '')
    if task_number.isnumeric() == False:
        bot.send_message(message.chat.id, f'Номер здачи введён неверно.')
    elif int(task_number) - 1 >= len(tasks):
        # Сообщаем о несуществовании задачи с данными номером
        bot.send_message(message.chat.id, f'Задачи с таким номером не существует.')
    else:
        # Выбираем нужную задачу
        deleted_task = tasks[int(task_number)-1]
        conn.execute("""DELETE FROM tasks WHERE user_id = ? AND task = ?""", (user_id, deleted_task))
        conn.commit()
        # Удаляем задачу из списка
        bot.send_message(message.chat.id, f'Задача "{deleted_task}" удалена.')

@bot.message_handler(commands=['date_tasks'])
def show_date_tasks(message):
    user_id = message.from_user.id
    date = message.text.replace('/date_tasks ', '')
    try:
        task_date = datetime.datetime.strptime(date, '%d.%m.%Y')
        cursor = conn.execute("""SELECT task FROM tasks WHERE user_id = ? AND date = ? ORDER BY priority DESC""", (user_id, str(task_date)))
        tasks = cursor.fetchall()
        if tasks:
            task_list = '\n'.join([f'{i+1}. {task[0]}' for i, task in enumerate(tasks)])
            bot.reply_to(message, f'Список задач на дату {task_date.date()}:\n{task_list}')
        else:
            bot.reply_to(message, f'На дату {task_date.date()} задач нет.')
    except:
        bot.send_message(message.chat.id, f'Дата указана неверно.')

def send_reminder():
    year = datetime.now().strftime('%Y')
    month = datetime.now().strftime('%m')
    day = datetime.now().strftime('%d')

    cursor = conn.execute("""SELECT task FROM tasks WHERE user_id=? AND date=?""", (user_id, datetime.now().strftime('%Y-%m-%d')))
    tasks = cursor.fetchall()
    if tasks:
        for task in tasks:
            bot.send_message(chat_id='CHAT_ID', text=f'Напоминаю, что сегодня нужно выполнить задачу "{task[0]}".')

# Запускаем бота
bot.polling()
schedule.every().day.at("10:00").do(send_reminder)

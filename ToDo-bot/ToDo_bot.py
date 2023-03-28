import telebot
from telebot import types
import sqlite3

# Создаем объект бота
bot = telebot.TeleBot('TOKEN')

# создаем подключение к базе данных
conn = sqlite3.connect('tasks.db', check_same_thread=False)

# создаем таблицу "tasks"
conn.execute("""CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, task TEXT);""")

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start_handler(message):
    bot.send_message(message.chat.id, 'Привет! Я бот для управления ToDo листом. Чтобы увидеть список команд, нажми /help')

# обработчик команды /help
@bot.message_handler(commands=['help'])
def help_handler(message):
    commands_text = '/start - начать работу с ботом\n' \
                    '/add_task [текст задачи] - добавить задачу\n' \
                    '/view_tasks - просмотреть список задач\n' \
                    '/delete_task [номер задачи] - удалить задачу\n' \
                    '/help - просмотреть список команд'
    bot.send_message(message.chat.id, f'Доступные команды:\n{commands_text}')

# Обработчик команды /add_task
@bot.message_handler(commands=['add_task'])
def add_task_handler(message):
    # Получаем id пользователя
    user_id = message.from_user.id
    # Получаем текст задачи
    task_text = message.text.replace('/add_task ', '')
    # Добавляем задачу в список
    conn.execute("""INSERT INTO tasks (user_id, task) VALUES (?, ?)""", (user_id, task_text))
    conn.commit()
    # Выводим сообщение об успешном выполнении
    bot.send_message(message.chat.id, f'Задача "{task_text}" добавлена.')

# Обработчик команды /view_tasks
@bot.message_handler(commands=['view_tasks'])
def view_tasks_handler(message):
    # Получаем id пользователя
    user_id = message.from_user.id
    # Создаём список задач, уникальный для пользователя
    cursor = conn.execute("""SELECT task FROM tasks WHERE user_id = ?""", (user_id,))
    tasks = [row[0] for row in cursor.fetchall()]
    # Выводим список
    if tasks:
        tasks_text = '\n'.join([f'{i + 1}. {task}' for i, task in enumerate(tasks)])
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
    cursor = conn.execute("""SELECT task FROM tasks WHERE user_id = ?""", (user_id,))
    tasks = [row[0] for row in cursor.fetchall()]
    task_number = int(message.text.replace('/delete_task ', '')) - 1
    # Проверяем номер удаляемой задачи
    if task_number < len(tasks):
        # Выбираем нужную задачу
        deleted_task = tasks[task_number]
        conn.execute("""DELETE FROM tasks WHERE user_id = ? AND task = ?""", (user_id, deleted_task))
        conn.commit()
        # Удаляем задачу из списка
        bot.send_message(message.chat.id, f'Задача "{deleted_task}" удалена.')
    else:
        # Сообщаем о несуществовании задачи с данными номером
        bot.send_message(message.chat.id, f'Задачи с таким номером не существует.')

# Запускаем бота
bot.polling()
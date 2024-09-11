import sqlite3


def create_task_table():
    # Подключение к базе данных (или создание базы данных, если она не существует)
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()

    # Создание таблицы Task с колонками user_id, task_name, task_desc
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Task (
            id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Автоматический первичный ключ
            user_id INTEGER,  -- Поле user_id типа INT, не является PK
            task_name TEXT NOT NULL,  -- Поле task_name типа TEXT
            task_desc TEXT NOT NULL,  -- Поле task_desc типа TEXT
            task_start DATE,
            task_deadline DATE,
            completed INTEGER DEFAULT 0       
        )
    ''')

    # Сохранение изменений и закрытие соединения
    conn.commit()
    conn.close()


def insert_into_table(chat_id, task_name, task_desc, task_start_date, task_deadline):
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()

    # Проверка на существование задачи с таким же названием у пользователя
    cursor.execute('''
        SELECT * FROM Task WHERE user_id = ? AND task_name = ?
    ''', (chat_id, task_name))

    existing_task = cursor.fetchone()  # Извлекаем первую найденную задачу

    if existing_task:
        # Если задача с таким же названием уже существует
        print('Задача с таким названием уже существует для этого пользователя.')
    else:
        # Если задачи с таким названием нет, выполняем вставку
        cursor.execute('''
            INSERT INTO Task (user_id, task_name, task_desc, task_start, task_deadline) VALUES (?,?,?,?,?)
        ''', (chat_id, task_name, task_desc, task_start_date, task_deadline))

        conn.commit()
        print('Задача добавлена')

    # Закрываем курсор и соединение
    cursor.close()
    conn.close()


def get_tasks_via_chat_id(chat_id):
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM Task WHERE user_id = ?
    ''', (chat_id,))
    result = cursor.fetchall()
    cursor.close()
    return result


def get_all_tasks():
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute('''
            SELECT * FROM Task
        ''')
    result = cursor.fetchall()
    cursor.close()
    return result


def delete_task_via_chat_id_and_name(chat_id, task_name):
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM Task WHERE user_id = ? and task_name = ?;
    ''', (chat_id, task_name))
    conn.commit()
    cursor.close()
    conn.close()


def mark_as_completed(chat_id, task_name):
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE Task SET completed = 1 WHERE user_id = ? and task_name = ?
    ''', (chat_id, task_name))
    conn.commit()
    cursor.close()
    conn.close()


def drop_table_task():
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM Task;')

    # Сохранение изменений
    conn.commit()

    # Сброс автоинкремента с использованием VACUUM
    cursor.execute('VACUUM;')

    # Закрытие курсора и соединения
    cursor.close()
    conn.close()

# drop_table_task()
# create_task_table()

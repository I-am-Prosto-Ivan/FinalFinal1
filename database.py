import sqlite3


def create_table(db_name="speech_kit.db"):
    try:
        # Создаём подключение к базе данных
        with sqlite3.connect(db_name) as conn:
            cursor = conn.cursor()
            # Создаём таблицу messages
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                message TEXT,
                answer TEXT,
                tts_symbols INTEGER,
                stt_blocks INTEGER,
                tokens INTEGER)
            ''')
            # Сохраняем изменения
            conn.commit()
    except Exception as e:(
        print(f"Error: {e}"))


def insert_row(user_id, message, answer,stt_blocks, tts_symbols ,tokens, db_name="speech_kit.db"):
    try:
        # Подключаемся к базе
        with sqlite3.connect(db_name) as conn:
            cursor = conn.cursor()
            # Вставляем в таблицу новое сообщение
            cursor.execute('''INSERT INTO messages (user_id, message, answer, tts_symbols, stt_blocks, tokens)VALUES (?, ?, ?, ?, ?, ?)''',
                           (user_id, message, answer, tts_symbols, stt_blocks, tokens))
            # Сохраняем изменения
            conn.commit()
    except Exception as e:(
        print(f"Error: {e}"))


def count_all_symbol(user_id, db_name="speech_kit.db"):
    try:
        # Подключаемся к базе
        with sqlite3.connect(db_name) as conn:
            cursor = conn.cursor()
            # Считаем, сколько символов использовал пользователь
            cursor.execute('''SELECT SUM(tts_symbols) FROM messages WHERE user_id=?''', (user_id,))
            data = cursor.fetchone()
            # Проверяем data на наличие хоть какого-то полученного результата запроса
            # И на то, что в результате запроса мы получили какое-то число в data[0]
            if data and data[0]:
                # Если результат есть и data[0] == какому-то числу, то
                return data[0]  # возвращаем это число - сумму всех потраченных символов
            else:
                # Результата нет, так как у нас ещё нет записей о потраченных символах
                return 0  # возвращаем 0
    except Exception as e:
        print(f"Error: {e}")


def count_all_blocks(user_id, db_name="speech_kit.db"):
    try:
        # Подключаемся к базе
        with sqlite3.connect(db_name) as conn:
            cursor = conn.cursor()
            # Считаем, сколько аудиоблоков использовал пользователь
            cursor.execute('''SELECT SUM(stt_blocks) FROM messages WHERE user_id=?''', (user_id,))
            data = cursor.fetchone()
            # Проверяем data на наличие хоть какого-то полученного результата запроса
            # И на то, что в результате запроса мы получили какое-то число в data[0]
            if data and data[0]:
                # Если результат есть и data[0] == какому-то числу, то
                return data[0]  # возвращаем это число - сумму всех потраченных аудиоблоков
            else:
                # Результата нет, так как у нас ещё нет записей о потраченных аудиоблоках
                return 0  # возвращаем 0
    except Exception as e:
        print(f"Error: {e}")


def find_users(username):
    connection = sqlite3.connect('speech_kit.db')
    cursor = connection.cursor()
    cursor.execute('SELECT user_id FROM messages WHERE user_id = ?', (username,))
    lid = (len(cursor.fetchall()))
    if username == 0:
        cursor.execute('SELECT * FROM messages')
        lid = (len(cursor.fetchall()))
    connection.commit()
    connection.close()
    return lid



import asyncio
import sqlite3


# Функция для проверки существования пользователя в базе данных
async def check_user(user_id):
    with sqlite3.connect("data/database/bot.db") as con:
        cursor = con.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id=?', (user_id,))
        return cursor.fetchone()


# Функция для получения класса пользователя
async def check_user_class(user_id):
    with sqlite3.connect("data/database/bot.db") as con:
        cursor = con.cursor()
        cursor.execute('SELECT user_class FROM users WHERE user_id=?', (user_id,))
        return cursor.fetchone()


# Функция для добавления пользователя в базу данных
async def add_user(user_id, user_class):
    with sqlite3.connect("data/database/bot.db") as con:
        cursor = con.cursor()
        cursor.execute('INSERT INTO users (user_id, user_class) VALUES (?, ?)', (user_id, user_class))
        con.commit()


# Функция для обновления класса пользователя в базе данных
async def update_user_class(user_id, new_user_class):
    with sqlite3.connect("data/database/bot.db") as con:
        cursor = con.cursor()
        cursor.execute('UPDATE users SET user_class=? WHERE user_id=?', (new_user_class, user_id))
        con.commit()


# Функция для проверки существования пользователя в базе данных
async def check_google_query(user_id):
    with sqlite3.connect("data/database/bot.db") as con:
        cursor = con.cursor()
        cursor.execute('SELECT google_query FROM users WHERE user_id=?', (user_id,))
        return cursor.fetchone()


# Функция для добавления google-запроса пользователя
async def add_google_query(user_id, user_query):
    with sqlite3.connect("data/database/bot.db") as con:
        cursor = con.cursor()
        cursor.execute('UPDATE users SET google_query=? WHERE user_id=?', (user_query, user_id))
        con.commit()


# Функция для удаления google-запроса пользователя
async def delete_google_query(user_id):
    with sqlite3.connect("data/database/bot.db") as con:
        cursor = con.cursor()
        cursor.execute('UPDATE users SET google_query=NULL WHERE user_id=?', (user_id,))
        con.commit()


# Функция для получения книг класса пользователя
async def check_textbooks(user_class, book_subject):
    with sqlite3.connect("data/database/bot.db") as con:
        cursor = con.cursor()
        cursor.execute(f'SELECT book_name FROM class_{user_class}_books WHERE book_subject=?',
                       (book_subject,))
        return cursor.fetchall()


# Функция для получения книг класса пользователя
async def check_textbook_url(user_class, book_name):
    with sqlite3.connect("data/database/bot.db") as con:
        cursor = con.cursor()
        cursor.execute(f'SELECT book_url, book_url_2 FROM class_{user_class}_books WHERE book_name=?',
                       (book_name,))
        return cursor.fetchone()


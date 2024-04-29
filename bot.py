import logging
import asyncio
import os
import sqlite3

from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import ParseMode
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from config import BOT_TOKEN
from functions import text_extract, translate_text

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())


# Функция для проверки существования пользователя в базе данных
async def check_user(user_id):
    with sqlite3.connect("bot.db") as con:
        cursor = con.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id=?', (user_id,))
        return cursor.fetchone()


# Функция для добавления пользователя в базу данных
async def add_user(user_id, user_class):
    with sqlite3.connect("bot.db") as con:
        cursor = con.cursor()
        cursor.execute('INSERT INTO users (user_id, user_class) VALUES (?, ?)', (user_id, user_class))
        con.commit()


# Функция для обновления класса пользователя в базе данных
async def update_user_class(user_id, new_user_class):
    with sqlite3.connect("bot.db") as con:
        cursor = con.cursor()
        cursor.execute('UPDATE users SET user_class=? WHERE user_id=?', (new_user_class, user_id))
        con.commit()


# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    user_id = message.from_user.id
    user_data = await check_user(user_id)

    if not user_data:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = [types.KeyboardButton(text="9"), types.KeyboardButton(text="10"), types.KeyboardButton(text="11")]
        keyboard.add(*buttons)
        await message.answer("Привет! Вы не зарегистрированы. Выберите ваш класс:", reply_markup=keyboard)
        return

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [types.KeyboardButton(text="Отсканировать текст 📸"), types.KeyboardButton(text="Перевести текст 🌐")]
    keyboard.add(*buttons)
    buttons = [types.KeyboardButton(text="Изменить класс 🎒")]
    keyboard.add(*buttons)
    await message.reply(f"Привет, {message.from_user.first_name}",
                        reply_markup=keyboard)


# Обработчик выбора класса
@dp.message_handler(lambda message: message.text in ["9", "10", "11"])
async def choose_class(message: types.Message):
    user_id = message.from_user.id
    user_data = await check_user(user_id)

    if not user_data:
        user_class = int(message.text)
        await add_user(user_id, user_class)
        await message.answer(f"Вы успешно зарегистрированы! Ваш класс {user_class}-ый.")
    else:
        new_class = int(message.text)
        await update_user_class(user_id, new_class)
        await message.answer(f"Ваш класс успешно изменен на {new_class}!")
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [types.KeyboardButton(text="Отсканировать текст 📸"), types.KeyboardButton(text="Перевести текст 🌐")]
    keyboard.add(*buttons)
    buttons = [types.KeyboardButton(text="Изменить класс 🎒")]
    keyboard.add(*buttons)
    await message.reply(f"Привет, {message.from_user.first_name}",
                        reply_markup=keyboard)


# Обработчик кнопки изменения класса
@dp.message_handler(commands=['change_class'])
@dp.message_handler(lambda message: message.text == "Изменить класс 🎒")
async def change_class(message: types.Message):
    user_id = message.from_user.id
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [types.KeyboardButton(text="9"), types.KeyboardButton(text="10"), types.KeyboardButton(text="11")]
    keyboard.add(*buttons)
    await message.answer("Выберите новый класс:", reply_markup=keyboard)


# Состояния бота для сканирования фото
class ScanText(StatesGroup):
    waiting_for_photo = State()


# Обработчик команды /scan_text
@dp.message_handler(commands=['scan_text'])
@dp.message_handler(Text(equals="Отсканировать текст 📸"))
async def scan_text_button(message: types.Message, state: FSMContext):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton(text="/cancel"))
    await message.reply("Пришли мне фото, чтобы я мог его отсканировать.", reply_markup=keyboard)
    await ScanText.waiting_for_photo.set()


# Обработчик сканирования фото
@dp.message_handler(content_types=types.ContentType.PHOTO, state=ScanText.waiting_for_photo)
async def handle_photo(message: types.Message, state: FSMContext):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [types.KeyboardButton(text="Отсканировать текст 📸"), types.KeyboardButton(text="Перевести текст 🌐")]
    keyboard.add(*buttons)
    buttons = [types.KeyboardButton(text="Изменить класс 🎒")]
    keyboard.add(*buttons)

    user_id = message.from_user.id
    photo = message.photo[-1]
    file_info = await bot.get_file(photo.file_id)
    file_path = file_info.file_path
    file = await bot.download_file(file_path)
    file_name = os.path.join("photos", f"{user_id}.jpg")
    with open(file_name, 'wb') as new_file:
        new_file.write(file.getvalue())
    await message.answer(text_extract(file_name), reply_markup=keyboard)
    await state.finish()


SUPPORTED_LANGUAGES = ["Английский", "Русский"]


# Состояния бота для команды /translate
class TranslationStates(StatesGroup):
    choose_source_language = State()
    choose_target_language = State()
    translating = State()


# Обработчик команды /translate
@dp.message_handler(commands=['translate'])
@dp.message_handler(Text(equals="Перевести текст 🌐"))
async def cmd_translate(message: types.Message):
    keyboard = types.InlineKeyboardMarkup()
    for lang in SUPPORTED_LANGUAGES:
        keyboard.add(types.InlineKeyboardButton(text=lang, callback_data=f"source_language:{lang}"))

    await message.reply("Выберите язык, с которого нужно перевести:", reply_markup=keyboard)
    await TranslationStates.choose_source_language.set()


# Обработка выбора языка источника
@dp.callback_query_handler(lambda c: c.data.startswith('source_language'), state=TranslationStates.choose_source_language)
async def process_source_language(callback_query: types.CallbackQuery, state: FSMContext):
    source_language = callback_query.data.split(":")[1]
    await state.update_data(source_language=source_language)

    keyboard = types.InlineKeyboardMarkup()
    for lang in SUPPORTED_LANGUAGES:
        keyboard.add(types.InlineKeyboardButton(text=lang, callback_data=f"target_language:{lang}"))

    await bot.edit_message_text(chat_id=callback_query.message.chat.id,
                                message_id=callback_query.message.message_id,
                                text="Теперь выберите язык, на который нужно перевести:",
                                reply_markup=keyboard)
    await TranslationStates.choose_target_language.set()


# Обработка выбора языка назначения
@dp.callback_query_handler(lambda c: c.data.startswith('target_language'), state=TranslationStates.choose_target_language)
async def process_target_language(callback_query: types.CallbackQuery, state: FSMContext):
    target_language = callback_query.data.split(":")[1]
    await state.update_data(target_language=target_language)

    await bot.edit_message_text(chat_id=callback_query.message.chat.id,
                                message_id=callback_query.message.message_id,
                                text="Отлично! Теперь отправьте текст для перевода:")
    await TranslationStates.translating.set()


# Обработка текста для перевода
@dp.message_handler(state=TranslationStates.translating)
async def process_translation(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        source_language = data.get('source_language')
        target_language = data.get('target_language')

    if not source_language or not target_language:
        await message.reply("Что-то пошло не так. Пожалуйста, попробуйте еще раз.")
        return

    await bot.send_message(chat_id=message.chat.id,
                           text=translate_text(message.text, source_language, target_language))
    await state.finish()


# Обработчик для команды /cancel
@dp.message_handler(commands=['cancel'], state='*')
async def cancel_translation(message: types.Message, state: FSMContext):
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - 1)

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [types.KeyboardButton(text="Отсканировать текст 📸"), types.KeyboardButton(text="Перевести текст 🌐")]
    keyboard.add(*buttons)
    buttons = [types.KeyboardButton(text="Изменить класс 🎒")]
    keyboard.add(*buttons)

    await bot.send_message(chat_id=message.chat.id,
                           text="Действие отменено.", reply_markup=keyboard)
    await state.finish()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

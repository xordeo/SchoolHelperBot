import logging
import os
import asyncio

import aiogram.utils.exceptions
from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from data.config import BOT_TOKEN
from data.database.base import (add_user, update_user_class, check_user, check_user_class,
                                check_google_query, add_google_query, delete_google_query,
                                check_textbooks, check_textbook_url)
from data.functions import text_extract, translate_text, SUPPORTED_LANGUAGES, google_query, get_images_url
from data.states_groups.classes import ScanText, TranslationStates, GDZStates
from data.keyboards.main_menu import main_menu_kb
from data.keyboards.classes import classes_kb
from data.keyboards.subjects import class_9_subjects_kb, class_10_subjects_kb, class_11_subjects_kb

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())


# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    user_id = message.from_user.id
    user_data = await check_user(user_id)

    if not user_data:
        await message.answer("Привет! Вы не зарегистрированы. Выберите ваш класс:", reply_markup=keyboard)
        return

    await message.reply(f"Привет, {message.from_user.first_name}",
                        reply_markup=main_menu_kb)


@dp.message_handler(commands=['help'])
@dp.message_handler(lambda message: message.text == "Помощь ❓")
async def help_command(message: types.Message):
    await message.reply("🔧 Все доступные команды бота:\n\n"
                        "/help — открытие этого сообщения\n"
                        "/scan_text — получить текст с изображения\n"
                        "/translate — перевести текст с одного языка на другой\n"
                        "/search {ваш запрос} — запрос в Google\n"
                        "/gdz — открыть ГДЗ для вашего класса\n"
                        "/add_bot_to — добавить бота в вашу беседу\n"
                        "/change_class — изменить свой класс\n"
                        "/cancel — отмена текущей команды\n\n"
                        f"🌐 Поддерживаемые языки перевода:\n [ {', '.join(SUPPORTED_LANGUAGES)} ]\n\n"
                        "Создатель бота: @xordeo\n"
                        "Спасибо за использование моего бота! ☺", reply_markup=main_menu_kb)


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
        await message.answer(f"Ваш класс успешно изменён на {new_class}!")

    await message.reply(f"Привет, {message.from_user.first_name}",
                        reply_markup=main_menu_kb)


# Обработчик кнопки изменения класса
@dp.message_handler(commands=['change_class'])
@dp.message_handler(lambda message: message.text == "Изменить класс 🎒")
async def change_class(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [types.KeyboardButton(text="9"), types.KeyboardButton(text="10"), types.KeyboardButton(text="11")]
    keyboard.add(*buttons)
    await message.answer("Выберите новый класс:", reply_markup=classes_kb)


# Обработчик команды /scan_text
@dp.message_handler(commands=['scan_text'])
@dp.message_handler(Text(equals="Сканировать текст 📸"))
async def scan_text_button(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton(text="/cancel"))
    await message.reply("Пришли мне фото, чтобы я мог его отсканировать.", reply_markup=keyboard)
    await ScanText.waiting_for_photo.set()


# Обработчик сканирования фото
@dp.message_handler(content_types=types.ContentType.PHOTO, state=ScanText.waiting_for_photo)
async def handle_photo(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    photo = message.photo[-1]
    file_info = await bot.get_file(photo.file_id)
    file_path = file_info.file_path
    file = await bot.download_file(file_path)
    file_name = os.path.join("data/photos", f"{user_id}.jpg")

    with open(file_name, 'wb') as new_file:
        new_file.write(file.getvalue())
    text = await text_extract(file_name)
    await message.answer(text, reply_markup=main_menu_kb)
    await state.finish()


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
@dp.callback_query_handler(lambda c: c.data.startswith('source_language'),
                           state=TranslationStates.choose_source_language)
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
@dp.callback_query_handler(lambda c: c.data.startswith('target_language'),
                           state=TranslationStates.choose_target_language)
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
        await message.reply("Что-то пошло не так. Пожалуйста, попробуйте ещё раз.")
        return

    text = await translate_text(message.text, source_language, target_language)

    await bot.send_message(chat_id=message.chat.id,
                           text=text)
    await state.finish()


# Обработчик кнопки добавления бота в беседу
@dp.message_handler(commands=['add_bot_to'])
@dp.message_handler(lambda message: message.text == "Добавить бота в беседу 👥")
async def add_bot_to(message: types.Message):
    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - 1)
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - 2)
    except aiogram.utils.exceptions.MessageCantBeDeleted:
        pass
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(types.InlineKeyboardButton(text="Выбрать беседу 👥", url="https://t.me/xordeo_bot?startgroup=start"))
    await message.answer("Чтобы добавить бота в беседу, нажмите на кнопку ниже ⬇", reply_markup=keyboard)
    await message.answer("Возвращение в меню ↩", reply_markup=main_menu_kb)


# Обработчик кнопки google-запроса
@dp.message_handler(lambda message: message.text == "Загуглить вопрос 🔎")
async def google_question(message: types.Message):
    await message.answer("Чтобы загуглить вопрос, напишите:\n\n"
                         "/search {ваш запрос}\n\n"
                         "Для отмены действия введите /cancel\n"
                         "Важно: перед использованием других команд, пропишите /cancel")


async def search_links(user_id, query):
    user_query = await check_google_query(user_id)
    if user_query[0] is None:
        get_google_query = await google_query(query)
        user_google_query = ", ".join(get_google_query)
        await add_google_query(user_id, user_google_query)
        user_google_query = await check_google_query(user_id)
        return user_google_query[0].split(", ")
    else:
        user_google_query = await check_google_query(user_id)
        return user_google_query[0].split(", ")


async def send_link(chat_id, index, links, user_id, reply_to_message_id):
    if not links:
        return  # Если список ссылок пустой, просто выходим

    if not 0 <= index < len(links):
        return  # Если индекс находится вне допустимого диапазона, просто выходим

    keyboard = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    if index > 0:
        buttons.append(types.InlineKeyboardButton(
            text="⬅ Назад", callback_data=f"backward_{index}_{user_id}_{reply_to_message_id}"))
    if index < len(links) - 1:
        buttons.append(types.InlineKeyboardButton(
            text="Вперёд ➡", callback_data=f"forward_{index}_{user_id}_{reply_to_message_id}"))
    keyboard.add(*buttons)

    # Отправляем новое сообщение или редактируем существующее, если оно уже было отправлено
    message_text = (f"Ссылка на возможный ответ:\n"
                    f"{links[index]}\n"
                    f"Перед использованием другой команды, пропишите /cancel")
    if hasattr(send_link, 'last_message'):
        try:
            await bot.edit_message_text(message_text, chat_id, send_link.last_message.message_id, reply_markup=keyboard)
        except aiogram.utils.exceptions.MessageToEditNotFound:
            send_link.last_message = await bot.send_message(chat_id, message_text, reply_markup=keyboard,
                                                            reply_to_message_id=reply_to_message_id)
    else:
        send_link.last_message = await bot.send_message(chat_id, message_text, reply_markup=keyboard,
                                                        reply_to_message_id=reply_to_message_id)


@dp.message_handler(commands=['search'])
async def search_handler(message: types.Message):
    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - 1)
    except aiogram.utils.exceptions.MessageCantBeDeleted:
        pass
    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - 2)
    except aiogram.utils.exceptions.MessageCantBeDeleted:
        pass
    user_id = message.from_user.id
    await delete_google_query(user_id)
    query = message.get_args()
    links = await search_links(user_id, query)
    if links:
        await send_link(message.chat.id, 0, links, user_id, message.message_id)


@dp.callback_query_handler(lambda c: c.data.startswith(('forward', 'backward')))
async def callback_handler(callback_query: types.CallbackQuery):
    index = int(callback_query.data.split('_')[1])  # Получаем индекс из данных обратного вызова
    links = await search_links(int(callback_query.data.split('_')[2]), "")
    await bot.answer_callback_query(callback_query.id)
    if not links:
        return  # Если список ссылок пустой, просто выходим

    if not 0 <= index < len(links):
        return  # Если индекс находится вне допустимого диапазона, просто выходим

    if callback_query.data.startswith('forward'):
        index += 1
    elif callback_query.data.startswith('backward'):
        index -= 1

    await send_link(callback_query.message.chat.id, index, links, int(callback_query.data.split('_')[2]),
                    int(callback_query.data.split('_')[3]))


@dp.message_handler(commands=['gdz'])
@dp.message_handler(Text(equals="Открыть ГДЗ 📚"))
async def choose_subject(message: types.Message):
    user_class = await check_user_class(message.from_user.id)
    if user_class[0] == 9:
        await message.reply("Выберите предмет:", reply_markup=class_9_subjects_kb)
    elif user_class[0] == 10:
        await message.reply("Выберите предмет:", reply_markup=class_10_subjects_kb)
    elif user_class[0] == 11:
        await message.reply("Выберите предмет:", reply_markup=class_11_subjects_kb)


@dp.callback_query_handler(lambda c: c.data.startswith('subject:'))
async def choose_textbook(callback_query: types.CallbackQuery):
    subject = callback_query.data.split(':')[1]
    user_class = callback_query.data.split(':')[2]
    textbooks = await check_textbooks(user_class, subject)
    keyboard = types.InlineKeyboardMarkup()
    for textbook in textbooks:
        keyboard.add(types.InlineKeyboardButton(textbook[0], callback_data=f'textbook:{textbook[0].rstrip()}'))
    await bot.edit_message_text("Выберите учебник:", callback_query.message.chat.id,
                                callback_query.message.message_id, reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data.startswith('textbook:'))
async def choose_task(callback_query: types.CallbackQuery, state: FSMContext):
    textbook = callback_query.data.split(':')[1]
    await state.update_data(textbook=textbook)
    await bot.edit_message_text("Введите номер задания:", callback_query.message.chat.id,
                                callback_query.message.message_id)
    await GDZStates.choosing_task.set()


# Обработка номера задания
@dp.message_handler(state=GDZStates.choosing_task)
async def choosing_task(message: types.Message, state: FSMContext):
    data = await state.get_data()
    textbook = data.get('textbook')
    url = await check_textbook_url(textbook.split()[0], textbook)
    message_text = message.text
    if "." in message_text:
        message_text = message_text.replace(".", "-")
    textbook_url = url[0] + message_text + url[1]
    images = await get_images_url(textbook_url)
    if images:
        for image in images:
            await bot.send_message(chat_id=message.chat.id,
                                   text=image)
        await state.finish()
    else:
        await bot.send_message(chat_id=message.chat.id,
                               text="Не нашлость такого задания или решения для него.\n"
                                    "Проверьте правильность ввода задания и попробуйте снова.")


# Обработчик для команды /cancel
@dp.message_handler(commands=['cancel'], state='*')
async def cancel_translation(message: types.Message, state: FSMContext):
    await bot.send_message(chat_id=message.chat.id,
                           text="Действие отменено.", reply_markup=main_menu_kb)
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - 1)
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - 2)

    await state.finish()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

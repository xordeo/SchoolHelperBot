from aiogram import types


main_menu_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
buttons = [types.KeyboardButton(text="Сканировать текст 📸"), types.KeyboardButton(text="Перевести текст 🌐")]
main_menu_kb.add(*buttons)
buttons = [types.KeyboardButton(text="Загуглить вопрос 🔎"), types.KeyboardButton(text="Открыть ГДЗ 📚")]
main_menu_kb.add(*buttons)
buttons = [types.KeyboardButton(text="Изменить класс 🎒"), types.KeyboardButton(text="Добавить бота в беседу 👥")]
main_menu_kb.add(*buttons)
buttons = [types.KeyboardButton(text="Помощь ❓")]
main_menu_kb.add(*buttons)

from aiogram import types


classes_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
buttons = [types.KeyboardButton(text="9"), types.KeyboardButton(text="10"), types.KeyboardButton(text="11")]
classes_kb.add(*buttons)

from aiogram import types

class_9_subjects = ["Алгебра"]
class_9_subjects_kb = types.InlineKeyboardMarkup()
for subject in class_9_subjects:
    class_9_subjects_kb.add(types.InlineKeyboardButton(subject, callback_data=f'subject:{subject}:9'))


class_10_subjects = ["Алгебра", "Геометрия"]
class_10_subjects_kb = types.InlineKeyboardMarkup()
for subject in class_10_subjects:
    class_10_subjects_kb.add(types.InlineKeyboardButton(subject, callback_data=f'subject:{subject}:10'))


class_11_subjects = ["Алгебра"]
class_11_subjects_kb = types.InlineKeyboardMarkup()
for subject in class_11_subjects:
    class_11_subjects_kb.add(types.InlineKeyboardButton(subject, callback_data=f'subject:{subject}:11'))

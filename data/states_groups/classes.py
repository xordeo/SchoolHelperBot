from aiogram.dispatcher.filters.state import State, StatesGroup


# Состояния бота для сканирования фото
class ScanText(StatesGroup):
    waiting_for_photo = State()


# Состояния бота для команды /translate
class TranslationStates(StatesGroup):
    choose_source_language = State()
    choose_target_language = State()
    translating = State()


# Состояни бота для команды /gdz
class GDZStates(StatesGroup):
    choosing_task = State()

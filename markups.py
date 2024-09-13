from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup


def start_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    btn = InlineKeyboardButton(text='Добавить задачу', callback_data='add_task_btn')
    btn2 = InlineKeyboardButton(text='Удалить задачу', callback_data='del_task_btn')
    btn3 = InlineKeyboardButton(text='Показать все мои задачи', callback_data='show_tasks')
    btn4 = InlineKeyboardButton(text='Отметить одну из задач выполненной', callback_data='mark_as_completed')
    btn5 = InlineKeyboardButton(text='Показать все невыполненные задачи', callback_data='show_uncompleted')
    markup.row(btn, btn2)
    markup.add(btn3)
    markup.row(btn4)
    markup.row(btn5)
    return markup


def cancel():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn = KeyboardButton(text='Отмена')
    markup.add(btn)
    return markup

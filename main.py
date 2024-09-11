from aiogram.types import Message, CallbackQuery
from aiogram import Dispatcher, Bot, executor
from aiogram import types
from database import insert_into_table, get_tasks_via_chat_id, get_all_tasks, delete_task_via_chat_id_and_name, \
    mark_as_completed
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from config import TOKEN
from markups import start_menu, cancel
from functions import is_valid_date, check_text
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
from functions import show_task, show_many_tasks

storage = MemoryStorage()
bot = Bot(TOKEN)

dp = Dispatcher(bot=bot, storage=storage)

scheduler = AsyncIOScheduler()

current_date = datetime.now().strftime('%Y-%m-%d')


class Todo(StatesGroup):
    task_name = State()
    task_desc = State()
    task_start_date = State()
    task_deadline = State()


class TaskDelete(StatesGroup):
    task_name = State()
    confirmation = State()


class TaskUpdate(StatesGroup):
    task_name = State()


# -----------------------------------------------START BOT-------------------------------------------------------------
@dp.message_handler(commands=['start'])
async def start(message: Message):
    chat_id = message.from_user.id
    await bot.send_message(chat_id, '👋 Привет! Нажмите на кнопку, чтобы начать работу с задачами:',
                           reply_markup=start_menu())


# ----------------------------------------------------------------------------------------------------------------------
# -----------------------------------------------TASK ADDING BLOCK------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
# -----------------------------------------------HANDLE ADD TASK BTN----------------------------------------------------
@dp.callback_query_handler(lambda c: c.data == 'add_task_btn')
async def add_task_ask_for_name(callback: CallbackQuery):
    chat_id = callback.from_user.id
    await bot.send_message(chat_id, '📝 Пожалуйста, введите название вашей задачи:', reply_markup=cancel())
    await Todo.task_name.set()
    await callback.answer()


# -----------------------------------------------HANDLE task_name STATE-------------------------------------------------
@dp.message_handler(state=Todo.task_name)
async def confirm_name_ask_desc(message: Message, state: FSMContext):
    chat_id = message.from_user.id
    task_name = message.text
    if check_text(task_name):
        await handle_cancel(message, state)
        return

    existing_tasks = get_tasks_via_chat_id(chat_id)
    for task in existing_tasks:
        if task_name == task[2]:
            await bot.send_message(
                chat_id,
                '❗ Задача с таким названием уже существует. Пожалуйста, введите другое название задачи.'
            )
            await Todo.task_name.set()
            return
    await state.update_data(task_name=task_name)
    await bot.send_message(chat_id, '✏️ Введите описание задачи:', reply_markup=cancel())
    await Todo.task_desc.set()


# -----------------------------------------------HANDLE task_desc STATE-------------------------------------------------
@dp.message_handler(state=Todo.task_desc)
async def confirm_desc_insert_to_db(message: Message, state: FSMContext):
    chat_id = message.from_user.id
    task_desc = message.text
    if check_text(task_desc):
        await handle_cancel(message, state)
        return

    await state.update_data(task_desc=task_desc)
    await bot.send_message(chat_id, '📅 Введите дату начала задачи (в формате YYYY.MM.DD):', reply_markup=cancel())
    await Todo.task_start_date.set()


# -----------------------------------------------HANDLE task_start_date STATE-------------------------------------------
@dp.message_handler(state=Todo.task_start_date)
async def confirm_start_date_ask_deadline(message: Message, state: FSMContext):
    chat_id = message.from_user.id
    task_start_date = message.text
    if check_text(task_start_date):
        await handle_cancel(message, state)
        return

    is_valid = is_valid_date(task_start_date)
    if not is_valid:
        await bot.send_message(chat_id,
                               '🚫 Неправильный формат даты или неправильное количество дней. Пожалуйста, введите дату в формате YYYY.MM.DD',
                               reply_markup=cancel())
        await Todo.task_start_date.set()
        return
    else:
        await state.update_data(task_start_date=task_start_date)
        await bot.send_message(chat_id,
                               '✅ Дата начала задачи сохранена. Введите дату завершения задачи (в формате YYYY.MM.DD):',
                               reply_markup=cancel())
        await Todo.task_deadline.set()


# -------------------------------------------HANDLE task_deadline STATE AND SAVE TASK TO DB-----------------------------
@dp.message_handler(state=Todo.task_deadline)
async def confirm_deadline_save_to_db(message: Message, state: FSMContext):
    chat_id = message.from_user.id
    task_deadline = message.text
    if check_text(task_deadline):
        await handle_cancel(message, state)
        return
    is_valid = is_valid_date(task_deadline)
    if not is_valid:
        await bot.send_message(chat_id,
                               '🚫 Неправильный формат даты или неправильное количество дней. Пожалуйста, введите дату в формате YYYY.MM.DD',
                               reply_markup=cancel())
        await Todo.task_deadline.set()
        return
    else:
        await state.update_data(task_deadline=task_deadline)
        data = await state.get_data()
        start_date = data.get('task_start_date')
        deadline = data.get('task_deadline')
        start_date_obj = datetime.strptime(start_date, '%Y.%m.%d')
        task_deadline_obj = datetime.strptime(task_deadline, '%Y.%m.%d')
        if task_deadline_obj < start_date_obj:
            await bot.send_message(
                chat_id,
                '🚫 Дата завершения задачи не может быть раньше даты начала задачи. Пожалуйста, введите корректную дату завершения задачи.',
                reply_markup=cancel()
            )
            await Todo.task_deadline.set()
            return
        task_name = data.get('task_name')
        task_desc = data.get('task_desc')
        start_date = start_date.replace('.', '-')
        deadline = deadline.replace('.', '-')
        try:
            insert_into_table(chat_id, task_name, task_desc, start_date, deadline)
            await bot.send_message(chat_id, show_task(get_tasks_via_chat_id(chat_id)[-1]), parse_mode='HTML',
                                   reply_markup=start_menu())
        except Exception as e:
            print(e)
            await bot.send_message(chat_id, '❌ Не удалось сохранить задачу. Попробуйте еще раз.')
        await state.finish()


# ----------------------------------------------------------------------------------------------------------------------
# -----------------------------------------------TASKS SHOWING BLOCK----------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
@dp.callback_query_handler(lambda c: c.data == 'show_tasks')
async def show_all_tasks(callback: CallbackQuery):
    chat_id = callback.from_user.id
    await callback.answer()
    await bot.send_message(chat_id, show_many_tasks(get_tasks_via_chat_id(chat_id)), parse_mode='HTML',
                           reply_markup=start_menu())


# ----------------------------------------------------------------------------------------------------------------------
# -----------------------------------------------TASKS DELETING BLOCK---------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------

# -----------------------------------------------DELETE BTN HANDLER-----------------------------------------------------
@dp.callback_query_handler(lambda c: c.data == 'del_task_btn')
async def ask_for_name_to_delete(callback: CallbackQuery):
    chat_id = callback.from_user.id
    await bot.send_message(chat_id, '🗑️ Введите название задачи, которую вы хотите удалить:')
    await bot.send_message(chat_id, f'📝 Вот все ваши задачи: \n{show_many_tasks(get_tasks_via_chat_id(chat_id))}',
                           parse_mode='HTML')
    await TaskDelete.task_name.set()


@dp.message_handler(state=TaskDelete.task_name)
async def confirm_name_ask_confirmation(message: Message, state: FSMContext):
    chat_id = message.from_user.id
    task_name = message.text
    existing_tasks = get_tasks_via_chat_id(chat_id)

    # Флаг для отслеживания существования задачи
    task_found = False

    for task in existing_tasks:
        if task_name == task[2]:
            task_found = True
            await bot.send_message(chat_id,
                                   '❓ Вы уверены, что хотите удалить задачу? Если да, то напишите "ДА", иначе "НЕТ".')
            await state.update_data(task_name=task_name)
            await TaskDelete.confirmation.set()
            return  # Завершаем выполнение функции, если задача найдена

    # Если задача не найдена, отправляем сообщение
    if not task_found:
        await bot.send_message(chat_id, '❌ Задачи с таким именем не существует.')


@dp.message_handler(state=TaskDelete.confirmation)
async def confirm_deletion(message: Message, state: FSMContext):
    chat_id = message.from_user.id
    confirmation = message.text
    data = await state.get_data()
    task_name = data.get('task_name')
    if confirmation.upper() == 'ДА':
        delete_task_via_chat_id_and_name(chat_id, task_name)
        await bot.send_message(chat_id, '✅ Задача успешно удалена!', reply_markup=start_menu())
    else:
        await bot.send_message(chat_id, '🔄 Перенаправляем вас в начало...')
        await start(message)
    await state.finish()


# ----------------------------------------------------------------------------------------------------------------------
# -----------------------------------------------TASKS UPDATING BLOCK---------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------

@dp.callback_query_handler(lambda c: c.data == 'mark_as_completed')
async def ask_for_task_name_to_mark(callback: CallbackQuery):
    chat_id = callback.from_user.id
    await callback.answer()
    await bot.send_message(chat_id, '✅ Введите название задачи, которую вы хотите отметить выполненной:')
    await bot.send_message(chat_id, f'📝 Вот все ваши задачи: \n{show_many_tasks(get_tasks_via_chat_id(chat_id))}',
                           parse_mode='HTML')
    await TaskUpdate.task_name.set()


@dp.message_handler(state=TaskUpdate.task_name)
async def mark_as_completed_func(message: Message, state: FSMContext):
    task_name = message.text
    existing_tasks = get_tasks_via_chat_id(message.from_user.id)
    task_found = False
    for task in existing_tasks:
        if task_name == task[2]:
            task_found = True
            mark_as_completed(chat_id=message.from_user.id, task_name=task_name)
            await bot.send_message(message.from_user.id,
                                   '✅ Задача успешно отмечена выполненной!', reply_markup=start_menu())
            await state.update_data(task_name=task_name)
            await state.finish()
            return
        if not task_found:
            await bot.send_message(message.from_user.id, '❌ Задачи с таким именем не существует.')


# ----------------------------------------------------------------------------------------------------------------------
# ---------------------------------------------------------FUNCTIONS----------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
@dp.message_handler(regexp='Отмена', state='*')
async def handle_cancel(message: Message, state: FSMContext):
    chat_id = message.from_user.id
    await state.finish()
    await bot.send_message(chat_id=chat_id, text='🔄 Перенаправляем вас назад...', reply_markup=start_menu())


# ------------------------------------------------------REMINDER---------------------------------------------------------
async def send_reminders():
    print('Начало оповещения')
    all_tasks = get_all_tasks()
    for task in all_tasks:
        if task[-3] == current_date:
            chat_id = task[1]
            task_name = task[2]
            await bot.send_message(chat_id,
                                   f'🔔 Напоминаем, что вы поставили задачу: "{task_name}" на сегодняшнюю дату {task[4]}.')


# ------------------------------------------------------AUTO TASKS DELETE-----------------------------------------------
async def tasks_auto_delete():
    current_date = datetime.now().strftime('%Y-%m-%d')
    all_tasks = get_all_tasks()

    for task in all_tasks:
        c_date = datetime.strptime(current_date, '%Y-%m-%d')
        task_deadline = datetime.strptime(task[-2], '%Y-%m-%d')

        # Проверяем, если дедлайн уже прошел
        if task_deadline < c_date:
            chat_id = task[1]
            task_name = task[2]

            delete_task_via_chat_id_and_name(chat_id, task_name)

            await bot.send_message(chat_id,
                                   f'🗑️ Удаляем задачу: {task_name}, так как дедлайн уже прошел.')


try:
    print(get_all_tasks()[-1])
except Exception as e:
    print(e)

scheduler.add_job(send_reminders, 'interval', hours=24)
scheduler.add_job(tasks_auto_delete, 'interval', hours=24)
scheduler.start()

executor.start_polling(dp, skip_updates=True)

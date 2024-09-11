from datetime import datetime


def is_valid_date(date_string):
    try:
        # Попытка преобразовать строку в дату
        datetime.strptime(date_string, '%Y.%m.%d')
        return True
    except ValueError:
        # Если произошла ошибка, дата недопустима
        return False


def get_day_word(days):
    if days % 10 == 1 and days % 100 != 11:
        return "день"
    elif 2 <= days % 10 <= 4 and not (12 <= days % 100 <= 14):
        return "дня"
    else:
        return "дней"


def show_task(lst: tuple) -> str:
    if lst[-1] == 0:
        completed = 'Нет❌'
    else:
        completed = 'Да✅'
    start_date_obj = datetime.strptime(lst[-3], '%Y-%m-%d')
    deadline_date_obj = datetime.strptime(lst[-2], '%Y-%m-%d')
    if lst[-1] == 0:
        days_difference = (deadline_date_obj - start_date_obj).days
        days_difference = f'{days_difference} {get_day_word(days_difference)}'
    else:
        days_difference = 'Задача уже выполнена'
    return f'''<b>Задача успешно создана✅</b>
<b>Название:</b> {lst[2]}
<b>Описание:</b> {lst[3]}
<b>Дата начала задачи:</b> {lst[-3]}
<b>Дата окончания задачи:</b> {lst[-2]}
<b>Выполнена: {completed}</b>
<b>Осталось времени: {days_difference}</b>'''


def show_many_tasks(lst: list):
    tasks_quantity = len(lst)
    result = []
    if tasks_quantity <= 0:
        return 'У вас пока нет задач'
    else:
        for index, task in enumerate(lst, start=1):
            if task[-1] == 0:
                completed = 'Нет❌'
            else:
                completed = 'Да✅'
            start_time = task[-3]
            deadline = task[-2]
            start_date_obj = datetime.strptime(start_time, '%Y-%m-%d')
            deadline_date_obj = datetime.strptime(deadline, '%Y-%m-%d')
            if task[-1] == 0:
                days_difference = (deadline_date_obj - start_date_obj).days
                days_difference = f'{days_difference} {get_day_word(days_difference)}'
            else:
                days_difference = 'Задача уже выполнена'

            answer = f'''<b>Номер задачи:</b> {index}
<b>Название:</b> {task[2]}
<b>Описание:</b> {task[3]}
<b>Дата начала задачи:</b> {task[-3]}
<b>Дата окончания задачи:</b> {task[-2]}
<b>Осталось времени: {days_difference}</b>
<b>Выполнено: {completed}</b>'''
            result.append(answer)
        result.append(str(f'<b>Количество задач:</b> {tasks_quantity}'))
        result = '\n\n'.join(result)
        return result


def check_text(msg) -> bool:
    if '/start' in msg or 'Отмена' in msg:
        return True
    else:
        return False

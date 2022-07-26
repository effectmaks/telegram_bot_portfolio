import logging
from datetime import datetime
from typing import Dict
from decimal import Decimal

from peewee import TextField, IntegerField, DateTimeField, Model

from base.models.eventbank import EventBank
from base.sqlite.connectSqlite import ConnectSqlite, ExceptionSelect, ExceptionInsert
from business_model.choice.choicedate import ChoiceDate


class TaskViewItem:
    def __init__(self):
        self.dict_task = {}
        self.date_next: datetime = None

    def __copy__(self):
        task = TaskViewItem()
        task.dict_task = self.dict_task.copy()
        task.date_next = self.date_next
        return task


class TaskStatus:
    DELETED = "DELETED"
    RUN = "RUN"
    COMPLETED = "COMPLETED"


class Task(Model):
    """
    База данных таблица Заданий
    """
    id = IntegerField()
    date_time = DateTimeField()
    id_user = IntegerField()
    type = TextField()
    desc = TextField()
    status = TextField()

    class Meta:
        table_name = 'task'
        database = ConnectSqlite.get_connect()


class ModelTask:
    __name_model = 'task'

    @classmethod
    def create(cls, id_user: int = 0, task_type: str = "", desc: str = "",
               status: str = "", date_time: datetime = None) -> int:
        """
        Добавляет задание в базу
        :param date_time:
        :param status:
        :param id_user: ID юзера
        :param task_type: Тип
        :param desc: Описание задачи
        :return: ID задания
        """
        logging.info('Команда добавить задание в базу')
        try:
            id_task = Task.create(id_user=id_user, type=task_type, desc=desc, status=status, date_time=date_time)
            logging.info(f'Добавлено задание ID:{id_task} status:{status}')
            return id_task
        except Exception as err:
            raise ExceptionInsert(cls.__name_model, str(err))

    @classmethod
    def get_list_run(cls, id_user: int = 0) -> list:
        """
        Возвращает лист с ID в статусе TaskStatus.RUN
        :param id_user: ID юзера
        :return: Лист с ID task
        """
        logging.info(f'Команда выгрузить все записи у ID юзера:{id_user} в статусе TaskStatus.RUN')
        try:
            list_out = []
            list_task = Task.select().where(Task.id_user == id_user, Task.status == TaskStatus.RUN)
            for task in list_task:
                list_out.append(task.id)
            if list_out:
                logging.info(f'Нужно удалить запущенные задания.')
            else:
                logging.info(f'Запущенных заданий нет.')
            return list_out
        except Exception as err:
            raise ExceptionSelect(cls.__name_model, str(err))

    @classmethod
    def get_dict_completed(cls, id_user: int = 0,
                           task_type: str = "",
                           date_time_next: datetime = None,
                           count_limit: int = 6,
                           id_task: int = 0) -> TaskViewItem:
        """
        Возвращает объект с заданиями и их информацией status = "COMPLETED"
        :param count_limit: Кол-во сколько искать записей
        :param date_time_next: Дата и время старше которой надо вывести задания
        :param task_type: Тип задания(input, convert, ...)
        :param id_user: ID юзера
        :return: объект TaskViewItem: словарь с заданиями, и старшей датой из этого словаря
        """
        task_view_item = TaskViewItem()
        date_time_filter: str = ""
        if date_time_next:
            date_time_filter = f'and task.date_time < "{date_time_next}"'
        id_task_filter: str = ""
        if id_task:
            id_task_filter = f'and task.id = {id_task}'
        try:
            logging.info('Возвращает лист с ID в status = "COMPLETED"')
            connect = ConnectSqlite.get_connect()
            task_list = connect.execute_sql('select task.id, task.date_time, task.desc, task.type, '
                                            'eventbank.comment, cashsell_task.count_task_subject '
                                            'from task '
                                            'join eventbank '
                                            'on eventbank.id_task = task.id '
                                            'left join '
                                            '(select id_task, id_cash, count(id_task) as count_task_subject '
                                            'from cashsell group by id_cash) as cashsell_task '
                                            'on cashsell_task.id_cash = eventbank.id_cash_buy '
                                            'and not cashsell_task.id_task = eventbank.id_task ' 
                                            'where status = "COMPLETED" '
                                            'and task.id_user = {} '
                                            'and task.type = "{}" '
                                            '{} {} '
                                            'order by task.date_time desc limit {}'.
                                            format(id_user,
                                                   task_type,
                                                   date_time_filter,
                                                   id_task_filter,
                                                   count_limit))
            if task_list:
                date_next: datetime = None
                for task in task_list:
                    task_view_item.dict_task[task[0]] = cls.task_desc(task[0], task[1], task[3],
                                                                      task[2], task[4], task[5])
                    date_next = task[1]
                task_view_item.date_next = date_next
                logging.info('Запрос выполнен')
            else:
                logging.info(f'В таблице {cls.__name_model} у сейфа ID:{id_user} нет выполненных статусов '
                             f'с типом {task_type}.')
            return task_view_item
        except Exception as err:
            raise ExceptionSelect(cls.__name_model, str(err))

    @classmethod
    def set_delete_status(cls, id_task: int):
        """
        Помечает статус задания с _id_task как TaskStatus.DELETED
        :param id_user: ID юзера
        """
        cls._set_status(id_task=id_task, type_status=TaskStatus.DELETED)

    @classmethod
    def set_run_status(cls, id_task: int):
        """
        Помечает статус задания с _id_task как TaskStatus.RUN
        :param id_user: ID юзера
        """
        cls._set_status(id_task=id_task, type_status=TaskStatus.RUN)

    @classmethod
    def set_completed_status(cls, id_task: int):
        """
        Помечает статус задания с _id_task как TaskStatus.DELETED
        :param id_user: ID юзера
        """
        cls._set_status(id_task=id_task, type_status=TaskStatus.COMPLETED)

    @classmethod
    def _set_status(cls, id_task: int, type_status: str):
        """
        Помечает статус задания с _id_task как type_status
        :param id_user: ID юзера
        :param type_status: Тип статуса
        """
        logging.info(f'Команда пометить ID_задание:{id_task} - статус:{type_status}')
        try:
            command_update = Task.update(status=type_status).where(Task.id == id_task)
            command_update.execute()
            logging.info(f'Успешно обновлен статус задания.')
            return id_task
        except Exception as err:
            raise ExceptionInsert(cls.__name_model, str(err))

    @classmethod
    def desc_in_or_out(self, znak: str, safe_name: str,  coin: str, amount: Decimal, fee: Decimal, type_command: str = '',
                        id_task: int = 0, date_time: str = '', comment: str = '') -> str:
        """
        Создает комментарий команд input или output для сохранения в базу
        :param znak: "+" пополнение, "-" снятие
        :param safe_name: Название сейфа
        :param coin: Название монеты
        :param amount: Объем
        :param fee: Объем комиссии
        :param type_command: Тип команды (input, output.)
        :param id_task: ID задания
        :param date_time: Дата и время операции
        :param comment: Комментарий к заданию.
        :return: Строка с описанием
        """
        desc_task = ''
        if id_task:
            desc_task = f'#{id_task}\n'
        desc_date_time = ''
        if date_time:
            desc_date_time = f'{ChoiceDate.convert_to_str(date_time)}\n'
        desc_type_command = ''
        if type_command:
            desc_type_command = f'{type_command}\n'
        desc_comment = ''
        if comment:
            desc_comment = f'\n"{comment}"'
        return f'{desc_task}{desc_date_time}{desc_type_command}{znak} {safe_name} {coin}:{amount}\nfee: {fee}{desc_comment}'

    @classmethod
    def desc_convertation_transfer(self, coin_sell: str, amount_sell: Decimal, coin_buy: str, amount_buy: Decimal,
                           type_command: str = '', id_task: int = 0, date_time: str = '',
                           comment: str = '', safe_sell: str = '', safe_buy: str = '', fee: Decimal = None) -> str:
        """
        Создает комментарий convertation или transfer для сохранения в базу
        :param coin_sell: Монета продажи
        :param amount_sell: Объем продажи
        :param coin_buy: Монета покупки
        :param amount_buy: Объем покупки
        :param type_command: Тип команды (convertation, transfer)
        :param id_task: ID задания
        :param date_time: Дата и время
        :param comment: Комментарий к заданию
        :param safe_sell: Имя сейфа продажи (режим transfer)
        :param safe_buy: Имя сейфа покупки (режим transfer)
        :param fee: Комиссия
        :return: Строка с описанием
        """
        desc_task = ''
        if id_task:
            desc_task = f'#{id_task}\n'
        desc_date_time = ''
        if date_time:
            desc_date_time = f'{ChoiceDate.convert_to_str(date_time)}\n'
        desc_type_command = ''
        if type_command:
            desc_type_command = f'{type_command}\n'
        desc_comment = ''
        if comment:
            desc_comment = f'\n"{comment}"'
        desc_safe_sell = ''
        if safe_sell:
            desc_safe_sell = f'{safe_sell}'
        desc_safe_buy = ''
        if safe_buy:
            desc_safe_buy = f'{safe_buy}'
        desc_fee = ''
        if fee:
            desc_fee = f'fee: {fee}\n'
        return f'{desc_task}{desc_date_time}{desc_type_command}' \
               f'- {desc_safe_sell} {coin_sell}:{amount_sell}\n+ {desc_safe_buy} {coin_buy}:{amount_buy}\n' \
               f'{desc_fee}{desc_comment}'

    @classmethod
    def task_desc(self, task_id: int, date_time_str: str, task_type: str, desc: str, comment: str,
                  task_id_subject_count: int = 0, date_time_dt: datetime = None) -> str:
        """
        Для юзера информация о задании
        :param task_id_subject_count: ID зависимого задания
        :param task_id: ID задания
        :param date_time_str: Дата и время задания
        :param task_type: Тип задания (input, output, convertation, transfer)
        :param desc: Описания задания с базы
        :param comment: Комментария пользователя
        :return:
        """
        desc_task_count_subject: str = ''
        if task_id_subject_count:
            desc_task_count_subject = f'Зависимых заданий: {task_id_subject_count} шт.\n'
            desc_date_time: str = ''
        if date_time_str:
            desc_date_time = f'{ChoiceDate.convert_to_str(date_time_str)}'
        elif date_time_dt:
            desc_date_time = f'{date_time_dt.strftime("%d.%m.%Y, %H:%M:%S")}'
        return f'# {task_id}\n{desc_task_count_subject}{desc_date_time}\nКоманда: {task_type}\n' \
               f'{desc}\n"{comment}"'

    @classmethod
    def get_info(cls, id_task: int) -> str:
        """
        Команда выгрузить инфо ID_задания:{id_task}
        :param id_task: ID задания
        :return: Инфо задания
        """

        logging.info(f'Команда выгрузить инфо ID_задания:{id_task}.')
        try:
            items = Task.select(Task.id, EventBank.comment, Task.date_time, Task.type, Task.desc).join(EventBank, on=(EventBank.id_task == Task.id)).where(Task.id == id_task)
            info_str = ""
            for item in items:
                info_str = cls.task_desc(item.id, "", item.type, item.desc, item.eventbank.comment,
                                         date_time_dt=item.date_time)
            logging.info(f'Успешно выгружено инфо.')
            return info_str
        except Exception as err:
            raise ExceptionSelect(cls.__name_model, str(err))

    @classmethod
    def get_dict_task_subject(cls, id_task: int) -> Dict[int, str]:
        """
        Выгрузить зависимые от ID_задания:{id_task}
        :param id_task: ID задания
        :return: Словарь с описанием заданий
        """

        logging.info(f'Выгрузить зависимые от ID_задания:{id_task}.')
        dict_out: Dict[int, str] = {}
        try:
            connect = ConnectSqlite.get_connect()
            task_list = connect.execute_sql('SELECT c_s.id_task from eventbank as ev_bank '
                                            'join cashsell as c_s '
                                            'on c_s.id_cash = ev_bank.id_cash_buy '
                                            'and not c_s.id_task = ev_bank.id_task '
                                            'where ev_bank.id_task = {}'.
                                            format(id_task))

            if task_list:
                for task in task_list:
                    dict_out[task[0]] = cls.get_info(task[0])
            return dict_out
        except Exception as err:
            raise ExceptionSelect(cls.__name_model, str(err))




import logging

from telegram_bot.api.commandsWork import CommandsWork
from telegram_bot.api.telegramApi import ConnectTelebot
from .choice.choicecoin import ChoiceCoin

from .nextfunction import NextFunction
from business_model.taskrule import TaskRule
from business_model.choice.choicedate import ChoiceDate
from business_model.choice.choicesafe import ChoiceSafe


class ExceptionOperationBank(Exception):
    def __init__(self, err_message: str = ''):
        logging.error(err_message)
        super().__init__(err_message)


class OperationBank:
    """
    Операции ввода, вывода и конвертации средств
    """
    def __init__(self, connect_telebot: ConnectTelebot, command_now: str):
        logging.info('Создание объекта OperationBank')
        self._command_now = command_now
        self._connect_telebot = connect_telebot
        self._next_function = NextFunction(OperationBank.__name__)
        self._simple_date: ChoiceDate = None
        self._choice_safe: ChoiceSafe = None
        self._choice_coin: ChoiceCoin = None
        self._task_rule: TaskRule

    def work(self):
        """
        Работа класса, в зависимости от команды, опрашивает пользователя
        """
        if self._next_function.work():  # функция выполнилась
            return
        if self._command_now == CommandsWork.COMMAND_INPUT:
            self._task_rule = TaskRule(id_user=self._connect_telebot.id_user, command_type=CommandsWork.COMMAND_INPUT)
            self._work_simple_date()

    def _work_simple_date(self):
        """
        Команда сформировать дату и время
        """
        if not self._simple_date:
            self._simple_date = ChoiceDate(self._connect_telebot)
        working: bool = self._simple_date.work()
        if working:
            self._next_function.set(self._work_simple_date)
        else:
            self._check_simple_date()  # далее выполнить

    def _check_simple_date(self):
        """
        Команда проверить наличие даты и времени
        """
        if self._simple_date.result:
            logging.info('Выбрана дата и время')
            self._work_choice_safe()
        else:
            raise ExceptionOperationBank('ChoiceDate завершил свою работу, но даты в результате нет.')

    def _work_choice_safe(self):
        """
        Команда сформировать id_safe_user
        """
        if not self._choice_safe:
            self._choice_safe = ChoiceSafe(self._connect_telebot)
        working: bool = self._choice_safe.work()
        if working:
            self._next_function.set(self._work_choice_safe)
        else:
            self._work_choice_coin()  # далее выполнить

    def _work_choice_coin(self):
        """
        Команда сформировать coin
        """
        if not self._choice_coin:
            self._choice_coin = ChoiceCoin(self._connect_telebot, self._choice_safe.result.id_safe)
        working: bool = self._choice_coin.work()
        if working:
            self._next_function.set(self._work_choice_coin)
        else:
            self._input_amount_question()  # далее выполнить

    def _input_amount_question(self):
        """
        Режим вопроса, какой объем пополняется?
        """
        logging.info(f'Режим вопроса объем пополнения')
        self._connect_telebot.send_text(f'Введите объем пополнения:')
        self._next_function.set(self._input_amount_answer)

    def _input_amount_answer(self):
        """
        Режим проверка объема пополнения пользователя
        :return:
        """
        logging.info(f'Режим проверки объема пополнения')
        amount = self._isfloat(self._connect_telebot.message)
        if amount:
            self._task_rule.amount = amount
            logging.info(f'Выбран объем - {self._task_rule.amount}')
            self._input_fee_question()
        else:
            self._connect_telebot.send_text('Невозможно преобразовать число.')
            raise ExceptionOperationBank(f'Невозможно преобразовать число - {self._connect_telebot.message}')

    def _isfloat(self, value_str: str) -> float:
        try:
            value_str = value_str.replace(',', '.')
            return float(value_str)
        except ValueError:
            pass

    def _input_fee_question(self):
        """
        Режим вопроса, какая комиссия снялась?
        """
        logging.info(f'Режим вопроса комиссия')
        self._connect_telebot.send_text(f'Введите комиссию:')
        self._next_function.set(self._input_fee_answer)

    def _input_fee_answer(self):
        """
        Режим проверка комиссия пользователя
        :return:
        """
        logging.info(f'Режим проверки комиссии')
        amount = self._isfloat(self._connect_telebot.message)
        if amount:
            self._task_rule.fee = amount
            logging.info(f'Введена комиссия - {self._task_rule.fee}')
            self._input_comment_question()
        else:
            self._connect_telebot.send_text('Невозможно преобразовать число.')
            raise ExceptionOperationBank(f'Невозможно преобразовать число - {self._connect_telebot.message}')

    def _input_comment_question(self):
        """
        Режим вопроса, введите комментарий
        """
        logging.info(f'Режим ввода комментария')
        self._connect_telebot.send_text(f'Введите комментарий:')
        self._next_function.set(self._input_comment_answer)

    def _input_comment_answer(self):
        """
        Проверка комментария
        :return:
        """
        logging.info(f'Режим проверки комментария')
        self._task_rule.comment = self._connect_telebot.message
        logging.info(f'Выбран комментарий - "{self._task_rule.comment}"')
        self._input_create_task()

    def _input_create_task(self):
        """
        Создание задания на создание счета юзера
        """
        self._task_rule.run()
        self._connect_telebot.send_text('Команда выполнена.')

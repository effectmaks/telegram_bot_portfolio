import logging
from peewee import SqliteDatabase


class ExceptionBase(Exception):
    def __init__(self, err_message: str = ''):
        logging.error(err_message)
        super().__init__(err_message)


class ExceptionInsert(Exception):
    def __init__(self, name_table: str = '', err_script_message: str = ''):
        err_message = f'Ошибка создания записи в таблице {name_table}'
        logging.error(err_message)
        logging.error(err_script_message)
        super().__init__(err_message)


class ExceptionSelect(Exception):
    def __init__(self, name_table: str = '', err_script_message: str = ''):
        err_message = f'Ошибка чтения записи в таблице {name_table}'
        logging.error(err_message)
        logging.error(err_script_message)
        super().__init__(err_message)


class ExceptionDelete(Exception):
    def __init__(self, name_table: str = '', err_script_message: str = ''):
        err_message = f'Ошибка удаления записи в таблице {name_table}'
        logging.error(err_message)
        logging.error(err_script_message)
        super().__init__(err_message)


class ExceptionUpdate(Exception):
    def __init__(self, name_table: str = '', err_script_message: str = ''):
        err_message = f'Ошибка обновления записи в таблице {name_table}'
        logging.error(err_message)
        logging.error(err_script_message)
        super().__init__(err_message)


class ConnectSqlite:
    """
    Класс Singleton выдает один и тот же объект
    """
    __connect = None

    @classmethod
    def get_connect(cls):
        if not cls.__connect:
            try:
                cls.__connect = SqliteDatabase('base/sqlite/db.sqlite3')
            except Exception as err:
                raise ExceptionBase(f'Ошибка подключения БД: {str(err)}')
        return cls.__connect


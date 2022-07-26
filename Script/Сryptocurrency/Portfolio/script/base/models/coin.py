import logging
from peewee import TextField, Model, fn
from base.sqlite.connectSqlite import ConnectSqlite, ExceptionSelect, ExceptionInsert


class Coin(Model):
    """
    База данных таблица Счета в сейфе
    """
    name = TextField()

    class Meta:
        table_name = 'coin'
        database = ConnectSqlite.get_connect()


class ModelCoin:
    __name_model = 'coin'

    @classmethod
    def __check(cls, name: str) -> bool:
        """
        Проверка есть ли такая монета
        """
        try:
            list_coin = Coin.select(fn.COUNT(Coin.name).alias('count_name')).where(Coin.name == name)
            for sel in list_coin:
                if sel.count_name == 1:
                    logging.info(f'В таблице {cls.__name_model} уже есть монета {name}')
                    return True  # монета есть
                elif sel.count_name > 1:
                    logging.warning(f'В таблице {cls.__name_model} больше одной монеты {name} = {sel.count_name} шт.')
                    return True  # монеты есть
                return False  # цикл дальше продолжать не надо
            return False  # пустой ответ на запрос - монет нет
        except Exception as err:
            raise ExceptionSelect(cls.__name_model, str(err))

    @classmethod
    def __create(cls, name: str):
        """
        Добавляет монету в базу
        """
        try:
            Coin.create(name=name)
        except Exception as err:
            raise ExceptionInsert(cls.__name_model, str(err))

    @classmethod
    def command_create(cls, name: str):
        """
        Проверка есть ли такая монета.
        Если монеты нет, создаем.
        """
        logging.info(f'Проверка есть ли монета: {name}?')
        have_coin = cls.__check(name)
        if have_coin:
            return
        cls.__create(name)

    @classmethod
    def get_list(cls) -> list:
        """
        Выгрузить все монеты
        """
        list_out = []
        try:
            coin_select = Coin.select().order_by(Coin.name)
            if coin_select:
                for coin in coin_select:
                    if coin.name != ' ':  # пустая строка в базе
                        list_out.append(coin.name)
                return list_out
            else:
                logging.warning(f'В таблице {cls.__name_model} нет монет.')
        except Exception as err:
            raise ExceptionSelect(cls.__name_model, str(err))

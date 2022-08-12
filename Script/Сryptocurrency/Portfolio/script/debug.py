import logging
import sys
from datetime import datetime

from base.models.cash import Cash, ModelCash
from business_model.taskrule import TaskRule
from telegram_bot.api.commandsWork import CommandsWork

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("telegram_bot/debug.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

if __name__ == '__main__':
    cash = ModelCash.get_cash_coin()



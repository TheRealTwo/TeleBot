# Бот с диспетчером, для второстепенных файлов

# files
import config as cfg
# libs
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import logging
import urlextract as urle

# Класс для извлечения ссылок (для handlers.py (90))
extractor = urle.URLExtract()

bot = Bot(token=cfg.TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
# уровень логирования
logging.basicConfig(filename='logs/work_process.log',
                    format='%(asctime)s %(levelname)s %(name)s %(message)s',
                    level=logging.INFO)
logging.basicConfig(
    filename='logs/error.log',
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
    level=logging.ERROR
)

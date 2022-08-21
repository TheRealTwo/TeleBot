#files
import config as cfg
from states import *
from callbacks import *
from commands import *
from classes import *
from sec_funcs import *
from handlers import *
from bot import *
#libs
import logging
from aiogram import executor
from aiogram.utils.exceptions import Unauthorized
import asyncio

# run long-polling
if __name__ == '__main__':
    load_config()
    logging.info('------------MAIN.PY HAS STARTED------------')
    try:
        executor.start_polling(dp, skip_updates=True)
    except Exception as e:
        logging.exception(e)
    finally:
        save_config()

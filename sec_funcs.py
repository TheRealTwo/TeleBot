# Вспомогательные функции без хэндлеров

# files
from bot import *
from classes import *
# libs
from aiogram import types
import logging
import sys
import traceback


buttons = None

# на команды /post и /(un)silence
# Клавиатура для выбора чатов (нет больше идей, как это сделать)
async def choose_chats(message: types.Message, act: str):
    global buttons
    chooser = await ChatChooser(bot, act).get()
    buttons = await chooser.get_buttons()
    await message.answer('Выбрано: 0', reply_markup=buttons)
    logging.info('Chat ADMIN: Choose buttons were spawned')
    if act == 'post':
        await PM_state.post.set()

def log(log, exception=None):
    if exception:
        traceback.print_exc(file=sys.stderr)
        print(exception)
        logging.exception(log)
    else:
        logging.info(log)
    print(log)

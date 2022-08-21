# Вспомогательные функции без хэндлеров

# files
import config as cfg
from bot import *
from classes import *
# libs
from aiogram import types
import json
import logging


buttons = None

# на команды /post и /(un)silence
# Клавиатура для выбора чатов (нет больше идей, как это сделать)
async def choose_chats(message: types.Message, act: str):
    global buttons
    chooser = ChatChooser(bot, act)
    buttons = await chooser.get_buttons()
    await message.answer('Выбрано: 0', reply_markup=buttons)
    logging.info('Chat ADMIN: Choose buttons were spawned')
    if act == 'post':
        await PM_state.post.set()

def save_config(filename=cfg.SAVE_FILE):
    data = {'blacklist': list(cfg.blacklist),
            'post_chats': list(cfg.post_chats),
            'silenced_chats': list(cfg.silenced_chats),
            'non_authorized': cfg.non_authorized,
            'last_messages': cfg.last_messages,
            'usernames': cfg.usernames}
    with open(filename, mode='wt', encoding='utf-8') as file:
        json.dump(data, file)
    logging.info(f'Config was saved into {filename}')

def load_config(filename=cfg.SAVE_FILE):
    try:
        with open(filename, mode='rt', encoding='utf-8') as file:
            data = json.load(file)
        blacklist = set(data['blacklist'])
        post_chats = set(data['post_chats'])
        silenced_chats = set(data['silenced_chats'])
        non_authorized = data['non_authorized']
        last_messages = data['last_messages']
        usernames = data['usernames']
        logging.info(f'Config was loaded from {filename}')
    except Exception as e:
        logging.info(f'Some problems with reading {filename}. Setting default values to config')
        blacklist = set()
        non_authorized = {}
        last_messages = {}
        usernames = {}
        post_chats = set()
        silenced_chats = set()
    finally:
        cfg.blacklist = blacklist
        cfg.post_chats = post_chats
        cfg.silenced_chats = silenced_chats
        cfg.non_authorized = non_authorized
        cfg.last_messages = last_messages
        cfg.usernames = usernames

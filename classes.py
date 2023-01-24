# Все используемые классы

# files
import config as cfg
import database.database_adapter as db
# libs
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.callback_data import CallbackData
from aiogram.dispatcher import FSMContext
import random
import asyncio




class Captcha:
    def __init__(self):
        self.emoji = random.choice(list(cfg.CAPTCHA.keys()))
        self.secret = cfg.CAPTCHA[self.emoji]
        self.choices = set(random.sample(list(map(lambda x: x[1], cfg.CAPTCHA.items())), random.randint(3, 6)) + [self.secret])
        self.message_id = -1

    def set_message_id(self, id):
        self.message_id = id

    def get_buttons(self):
        captcha_buttons = InlineKeyboardMarkup()
        for word in self.choices:
            if word == self.secret:
                captcha_buttons.add(InlineKeyboardButton(word, callback_data='right_captcha_answer'))
            else:
                captcha_buttons.add(InlineKeyboardButton(word, callback_data='wrong_captcha_answer'))
        return captcha_buttons

    def get_emoji(self):
        return self.emoji

    def get_message_id(self):
        return self.message_id

class ChatChooser:
    def __init__(self, bot, act):
        self.bot = bot
        self.act = act
        self.chats = []
    async def get(self):
        # Если act == 'post', то после нажатия бот будет ожидать сообщение в качестве поста
        # Если act == 'silence', то сразу после нажатия чаты будут глушиться
        # Если act == 'unsilence', то как silence, но кнопки будут не со всеми чатами, а с заглушенными
        sql = db.SqlAdapter()
        chats = await sql.get_chat(all=True)
        if self.act == 'unsilence':
            chats = list(filter(lambda x: x.is_silenced, chats))
        self.chats = list(map(lambda y: str(y.id), chats))
        return self
    async def get_buttons(self):
        sql = db.SqlAdapter()
        choose_buttons = InlineKeyboardMarkup()
        choose_buttons.add(InlineKeyboardButton(text='--Все чаты--', callback_data=f'all_chats:{self.act}'))
        for chat_id in self.chats:
            chat_name = await sql.get_chat(chat_id)
            chat_name = chat_name.title
            choose_buttons.add(InlineKeyboardButton(text=chat_name or 'Undefined', callback_data=f'one_chat:{self.act}:{chat_id}'))
        return choose_buttons

# Состояния (для /post)
class PM_state(StatesGroup):
    post = State()

# Функции на нажатия кнопок (коллбеки)

# files
import config as cfg
from classes import PM_state
from bot import *
# libs
from aiogram import types
from aiogram.utils.callback_data import CallbackData
from aiogram.dispatcher import FSMContext
import datetime as dt




# Непрпавильный ответ на каптчу
@dp.callback_query_handler(lambda c: c.data == 'wrong_captcha_answer')
async def captcha_is_wrong(call: types.CallbackQuery):
    user_id = str(call.from_user.id)
    chat_id = str(call.message.chat.id)
    if user_id in cfg.non_authorized[chat_id]:
        await call.message.chat.kick(call.from_user.id)
        await bot.unban_chat_member(chat_id=chat_id, user_id=user_id)
        logging.info(f'Chat {chat_id}: User {user_id} was kicked because of wrong captcha')
        cfg.non_authorized[chat_id].remove(user_id)
        await call.message.delete()

# Правильный ответ на каптчу
@dp.callback_query_handler(lambda c: c.data == 'right_captcha_answer')
async def captcha_is_solved(call: types.CallbackQuery):
    user_id = str(call.from_user.id)
    chat_id = str(call.message.chat.id)
    if user_id in cfg.non_authorized[chat_id]:
        cfg.non_authorized[chat_id].remove(user_id)
        await call.message.delete()
        # Права на первые 24 часа
        await bot.restrict_chat_member(chat_id=chat_id, user_id=user_id, permissions=types.ChatPermissions(can_send_media_messages=False, can_invite_users=False, can_send_other_messages=False), until_date=dt.timedelta(days=1))
        # Права, оставленные навечно
        await bot.restrict_chat_member(chat_id=chat_id, user_id=user_id, permissions=types.ChatPermissions(can_send_messages=True), until_date=dt.timedelta(seconds=10))



# Выбраны все чаты для поста
@dp.callback_query_handler(text_startswith='all_chats', state=PM_state.post)
async def choose_all_chats_for_post(call: types.CallbackQuery, state: FSMContext):
    cfg.post_chats = set(list(cfg.non_authorized.keys()))
    await call.message.answer('Выбраны все чаты! Теперь отправьте ваш пост')
    await call.message.delete()


# Выбран какой-то чат для поста
@dp.callback_query_handler(text_startswith='one_chat', state=PM_state.post)
async def choose_specific_chat_for_post(call: types.CallbackQuery, state: FSMContext):
    act = call.data.split(':')[1]
    chat_id = call.data.split(':')[-1]
    if chat_id not in cfg.post_chats:
        cfg.post_chats.add(chat_id)
        await call.message.edit_text(f'Выбрано: {len(cfg.post_chats)}', reply_markup=call.message.reply_markup)





# Выбраны все чаты для поста
@dp.callback_query_handler(text_startswith='all_chats')
async def choose_all_chats_for_silencing(call: types.CallbackQuery):
    act = call.data.split(':')[-1]
    if act == 'unsilence':
        cfg.silenced_chats = set()
        await call.message.answer('Все чаты выведены из тихого режима!')
        await call.message.delete()
        logging.info(f'Chat ADMIN: All ({len(list(cfg.non_authorized.keys()))}) chats were unsilenced!')
    else:
        cfg.silenced_chats = set(list(cfg.non_authorized.keys()))
        await call.message.answer('Все чаты теперь в тихом режиме!')
        await call.message.delete()
        logging.info(f'Chat ADMIN: All ({len(list(cfg.non_authorized.keys()))}) chats were silenced!')

# Выбран какой-то чат для поста
@dp.callback_query_handler(text_startswith='one_chat')
async def choose_specific_chat_for_silencing(call: types.CallbackQuery):
    act = call.data.split(':')[1]
    chat_id = call.data.split(':')[-1]
    if act == 'silence':
        if chat_id not in cfg.silenced_chats:
            cfg.silenced_chats.add(chat_id)
            await call.message.edit_text(f'Чатов в тихом режиме: {len(cfg.silenced_chats)}', reply_markup=call.message.reply_markup)
            logging.info(f'Chat {chat_id}: Chat was silenced')
    else:
        if chat_id in cfg.silenced_chats:
            cfg.silenced_chats.remove(chat_id)
            await call.message.edit_text(f'Чатов в тихом режиме: {len(cfg.silenced_chats)}', reply_markup=call.message.reply_markup)
            logging.info(f'Chat {chat_id}: Chat was unsilenced')

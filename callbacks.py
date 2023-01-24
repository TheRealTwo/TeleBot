# Функции на нажатия кнопок (коллбеки)

# files

import config as cfg
from classes import PM_state
from bot import *
import database.database_adapter as db
from sec_funcs import log
# libs
import asyncio
from aiogram import types
from aiogram.utils.callback_data import CallbackData
from aiogram.dispatcher import FSMContext
import datetime as dt




# Непрпавильный ответ на каптчу
@dp.callback_query_handler(lambda c: c.data == 'wrong_captcha_answer')
async def captcha_is_wrong(call: types.CallbackQuery):
    user_id = str(call.from_user.id)
    chat_id = str(call.message.chat.id)
    sql = db.SqlAdapter()
    user = await sql.get_user(user_id)

    if not user.is_authorized:
        await call.message.chat.kick(user_id)
        await bot.unban_chat_member(chat_id=chat_id, user_id=user_id)
        log(f'Chat {chat_id}: User {user_id} was kicked because of wrong captcha')
        await sql.delete_user(user_id)
        await call.message.delete()
    else:
        msg = await call.message.answer("Так.\n*Не баловаться!*\nИначе бан!", parse_mode='Markdown')
        await asyncio.sleep(3)
        await msg.delete()



# Правильный ответ на каптчу
@dp.callback_query_handler(lambda c: c.data == 'right_captcha_answer')
async def captcha_is_solved(call: types.CallbackQuery):
    user_id = str(call.from_user.id)
    chat_id = str(call.message.chat.id)

    sql = db.SqlAdapter()
    user = await sql.get_user(user_id)

    if not user.is_authorized:
        user.is_authorized = True
        await sql.set_user(user)
        await call.message.delete()
        # Права, оставленные навечно
        await bot.restrict_chat_member(chat_id=chat_id, user_id=user_id, permissions=types.ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_invite_users=True, can_send_other_messages=True), until_date=dt.timedelta(seconds=10))
        # Права на первые 24 часа
        await bot.restrict_chat_member(chat_id=chat_id, user_id=user_id, permissions=types.ChatPermissions(can_send_messages=True, can_send_media_messages=False, can_invite_users=False, can_send_other_messages=False), until_date=dt.timedelta(days=1))



# Выбраны все чаты для поста
@dp.callback_query_handler(text_startswith='all_chats', state=PM_state.post)
async def choose_all_chats_for_post(call: types.CallbackQuery, state: FSMContext):
    cfg.post_chats = ['all']
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





# Выбраны все чаты НЕ для поста
@dp.callback_query_handler(text_startswith='all_chats')
async def choose_all_chats_for_silencing(call: types.CallbackQuery):
    act = call.data.split(':')[-1]
    sql = db.SqlAdapter()
    chats = await sql.get_chat(all=True)
    if act == 'unsilence':
        for chat in chats:
            chat.is_silenced = False
            await sql.set_chat(chat)
        await call.message.answer('Все чаты выведены из тихого режима!')
        await call.message.delete()
        log(f'Chat ADMIN: All ({len(chats)}) chats were unsilenced!')
    else:
        for chat in chats:
            chat.is_silenced = True
            await sql.set_chat(chat)
        await call.message.answer('Все чаты теперь в тихом режиме!')
        await call.message.delete()
        log(f'Chat ADMIN: All ({len(chats)}) chats were silenced!')

# Выбран какой-то чат НЕ для поста
@dp.callback_query_handler(text_startswith='one_chat')
async def choose_specific_chat_for_silencing(call: types.CallbackQuery):
    act = call.data.split(':')[1]
    chat_id = call.data.split(':')[-1]
    sql = db.SqlAdapter()
    chat = await sql.get_chat(chat_id)
    if act == 'silence':
        if not chat.is_silenced:
            chat.is_silenced = True
            await sql.set_chat(chat)
            await call.message.edit_text(f'Чат {chat.title} теперь в тихом режиме!', reply_markup=call.message.reply_markup)
            log(f'Chat {chat_id}: Chat was silenced')
    else:
        if chat.is_silenced:
            chat.is_silenced = False
            await sql.set_chat(chat)
            await call.message.edit_text(f'Чат {chat.title} теперь не в тихом режиме!', reply_markup=call.message.reply_markup)
            log(f'Chat {chat_id}: Chat was unsilenced')

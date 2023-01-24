# Функции для состояний (FSM)

# files
import config as cfg
from classes import PM_state
from bot import *
import database.database_adapter as db
# libs
from aiogram import types
from aiogram.dispatcher import FSMContext
import logging

# Постим контент
@dp.message_handler(state=PM_state.post, content_types=['any'])
async def post_content(message: types.Message, state: FSMContext):
    if message.text.startswith("/cancel"):
        cfg.post_chats = set()
        await state.finish()
        await message.answer('Пост отменен')
        return None
    if str(message.from_user.id) not in cfg.ADMINS_ID or message.chat.type in ("group", "supergroup"):
        # Если пост отправляет левый пользователь или не в ЛС
        return None
    if cfg.post_chats:
        if 'all' in cfg.post_chats:
            sql = db.SqlAdapter()
            chats = await sql.get_chat(all=True)
            chats = list(map(lambda x: str(x.id), chats))
        else:
            chats = cfg.post_chats
        for chat_id in chats:
            await bot.copy_message(chat_id=chat_id, from_chat_id=message.chat.id, message_id=message.message_id)
            logging.info(f'Chat {chat_id}: content was posted')
        cfg.post_chats = set()
        await state.finish()
        await message.answer('Пост успешно отправлен!')

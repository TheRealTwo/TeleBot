# Функции с обычными хэндлерами

# files
import config as cfg
from bot import *
from classes import Captcha
import database.database_adapter as db
from sec_funcs import log
# libs
from aiogram import types
from aiogram.dispatcher import FSMContext
import datetime as dt
from emoji import emojize
import asyncio
import datetime as dt



# **Не работает в тихом режиме**
# Удаление сообщений об уходе
@dp.message_handler(content_types=['left_chat_member'])
async def on_user_leaving(message: types.Message):
    user_id = str(message.left_chat_member.id)
    chat_id = str(message.chat.id)
    sql = db.SqlAdapter()
    chat = await sql.get_chat(chat_id)
    if chat.is_silenced:
        # Если чат в тихом режиме
        return None
    if user_id == cfg.BOT_ID:
        # Если удалили бота
        log(f'Chat {chat_id}: Bot was kicked from chat')
        await sql.delete_chat(chat_id)
        return None
    else:
        await message.delete()

# **Не работает в тихом режиме, только выдача прав (как после 24ч.) и удаление сообщения**
# Создание каптчи при входе нового юзера
@dp.message_handler(content_types=['new_chat_members'])
async def on_user_joining(message: types.Message):
    user_id = str(message.new_chat_members[0].id)
    chat_id = str(message.chat.id)

    sql = db.SqlAdapter()
    if user_id == cfg.BOT_ID:
        chat_title = await bot.get_chat(chat_id=chat_id)
        chat = db.Chat({'id': int(chat_id), 'title': chat_title.title, 'is_silenced': False})
        await sql.set_chat(chat)
        log(f'Chat {chat_id}: Bot was invited in chat')
        cfg.last_messages[chat_id] = []
        return None



    user = await sql.get_user(user_id)
    if not user:
        # Создание данных о юзере
        api_user = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        name = api_user.user.username
        if not name:
            name = api_user.user.first_name
        user = db.User({'id': int(user_id), 'name': name, 'is_authorized': False})
        await sql.set_user(user)
    log(f'Chat {chat_id}: User {user_id} was added to chat')

    # То, что нельзя делать никому
    await bot.set_chat_permissions(chat_id=chat_id, permissions=types.ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_invite_users=True, can_send_other_messages=True, can_send_polls=False, can_add_web_page_previews=False, can_change_info=False, can_pin_messages=False))
    await message.delete()
    chat = await sql.get_chat(chat_id)
    if chat.is_silenced:
        # Если чат в тихом режиме
        return None

    member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
    if not isinstance(member, types.ChatMemberOwner) and not isinstance(member, types.ChatMemberAdministrator) and not user.is_authorized:
        # Если рядовой юзер
        await bot.restrict_chat_member(chat_id=chat_id, user_id=user_id, permissions=types.ChatPermissions(can_send_messages=False, can_send_media_messages=False, can_invite_users=False, can_send_other_messages=False), until_date=dt.timedelta(seconds=10))
        # Махинации с каптчей
        captcha = Captcha()
        msg = await message.answer(f'С подключением, юзернейм! Введу тебя в курс дела:\n\n- Первые 24 часа после вступления запрещены:\nИнвайт\nЛюбые ссылки и @name обращения\nДобавление медиа, аудио, голос\nМожно только писать текст\n\n- Через 24 часа можно:\nПересылать сообщения\nПостить текст и фото\nОбращаться по @name\nРазрешать приглашать друзей\n\n\nА теперь докажи, что в тебе есть хоть капля человечности, и скажи, что это: {emojize(captcha.get_emoji())}', reply_markup=captcha.get_buttons())
        captcha.set_message_id(msg.message_id)
        await asyncio.sleep(cfg.CAPTCHA_TIME)
        user = await sql.get_user(user_id)
        if not user.is_authorized:
            await message.chat.kick(user_id)
            await bot.unban_chat_member(chat_id=chat_id, user_id=user_id)
            log(f'Chat {chat_id}: User {user_id} was kicked out of chat because of captcha timeout')
            await bot.delete_message(chat_id=int(chat_id), message_id=captcha.get_message_id())
            await sql.delete_user(user_id)


# **Не работает в тихом режиме**
# Обработка обычных сообщений (@name, ссылки, спам)
@dp.message_handler()
async def regular_message(message: types.Message):
    if message.chat.type in ('group', 'supergroup'):
        if message.text:
            chat_id = str(message.chat.id)
            user_id = str(message.from_user.id)
            sql = db.SqlAdapter()
            if not cfg.last_messages.get(chat_id, False):
                cfg.last_messages[chat_id] = []

            # Добавление чата, если нет
            chat = await sql.get_chat(chat_id)
            if not chat:
                api_chat = await bot.get_chat(chat_id=chat_id)
                chat = db.Chat({'id': int(chat_id), 'title': api_chat.title, 'is_silenced': False})
                chat.id = int(chat_id)
                chat.title = api_chat.title
                chat.is_silenced = False
                await sql.set_chat(chat)
                cfg.last_messages[chat_id] = []
                log(f'Chat {chat_id}: A chat was added')

            # Добавление юзера, если нет
            user = await sql.get_user(user_id)
            if not user:
                # Создание данных о юзере
                name = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
                name = name.user.username
                if not name:
                    name = name.user.first_name
                user = db.User({'id': int(user_id), 'name': name, 'is_authorized': True})
                await sql.set_user(user)
                log(f'Chat {chat_id}: User {user_id} was added to chat')


            member = await bot.get_chat_member(chat_id, user_id)
            if not isinstance(member, types.ChatMemberOwner) and not isinstance(member, types.ChatMemberAdministrator):
                # Если сообщение от рядового юзера
                chat = await sql.get_chat(chat_id)
                if chat.is_silenced:
                    # Если чат в тихом режиме
                    return None
                if message.chat.type not in ("group", "supergroup"):
                    # Если пишут в ЛС
                    return None
                # Проверка на наличие @name
                user = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
                if not user.can_invite_users:
                    text = message.text.split()
                    for word in text:
                        if word.startswith('@') and word != '@':
                            await message.delete()
                            return None


                # Проверка на наличие ссылок
                links = extractor.find_urls(message.html_text)
                if links:
                    if user.can_invite_users:
                        for link in links:
                            db_link = await sql.get_link(link)
                            if db_link:
                                await message.delete()
                                chats = await sql.get_chat(all=True)
                                for chat_id in list(map(lambda x: str(x.id), chats)): # Баним юзера из всех чатов
                                    await bot.ban_chat_member(chat_id=chat_id, user_id=message.from_user.id, revoke_messages=True)
                                log(f'User {user_id} was banned from all chats because of a forbidden link')
                                break
                    else:
                        await message.delete()
                    return None

            # Проверка на спам (cfg.last_messages)
            # Добавление сообщения в стек последних текстовых сообщений
                cfg.last_messages[chat_id] = cfg.last_messages[chat_id] + [(str(message.message_id), message.text)] if len(cfg.last_messages[chat_id]) < 5 else cfg.last_messages[chat_id][1:] + [(str(message.message_id), message.text)]
                # Проверка на наличие спама (3+ одинаковых сообщений)
                if len(list(filter(lambda x: x[1] == message.text, cfg.last_messages[chat_id]))) > 2:
                    for i in range(len(cfg.last_messages[chat_id])):
                        msg = cfg.last_messages[chat_id][i]
                        if msg[1] == message.text:
                            cfg.last_messages[chat_id][i] = (msg[0], '')
                            await bot.delete_message(chat_id=chat_id, message_id=msg[0])
                    log(f'Chat {chat_id}: spam messages were deleted')

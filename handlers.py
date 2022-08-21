# Функции с обычными хэндлерами

# files
import config as cfg
from bot import *
from classes import Captcha
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
    if str(message.chat.id) in cfg.silenced_chats or message.from_user.id == cfg.BOT_ID:
        # Если чат в тихом режиме или удалили бота
        return None
    await message.delete()

# **Не работает в тихом режиме, только выдача прав (как после 24ч.) и удаление сообщения**
# Создание каптчи при входе нового юзера + получение id чата
@dp.message_handler(content_types=['new_chat_members'])
async def on_user_joining(message: types.Message):
    user_id = str(message.new_chat_members[0].id)
    chat_id = str(message.chat.id)
    member = await bot.get_chat_member(chat_id, user_id)
    # Получение id чата, в который добавили бота
    # Необходимо для корректировки данных в config.py (non-authorized, last_messages и т.д.)
    if user_id == cfg.BOT_ID:
        cfg.non_authorized[chat_id] = []
        cfg.last_messages[chat_id] = []
        logging.info(f'Chat {chat_id}: Bot was invited in chat')
        return


    # Связывание username и id
    username = member.user.username
    if not username:
        username = member.user.first_name
    username = username[1:] if username.startswith('@') else username
    cfg.usernames[username] = user_id
    logging.info(f'Chat {chat_id}: User {user_id} was added to chat')

    # То, что нельзя делать никому
    await bot.set_chat_permissions(chat_id=chat_id, permissions=types.ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_invite_users=True, can_send_other_messages=True, can_send_polls=False, can_add_web_page_previews=False, can_change_info=False, can_pin_messages=False))
    await message.delete()
    if str(message.chat.id) in cfg.silenced_chats:
        # Если чат в тихом режиме
        return None

    if not isinstance(member, types.ChatMemberOwner) and not isinstance(member, types.ChatMemberAdministrator):
        # Если рядовой юзер
        await bot.restrict_chat_member(chat_id=chat_id, user_id=user_id, permissions=types.ChatPermissions(can_send_messages=False, can_send_media_messages=False, can_invite_users=False, can_send_other_messages=False), until_date=dt.timedelta(seconds=10))
        # Махинации с каптчей
        captcha = Captcha()
        msg = await message.answer(f'С подключением, юзернейм! Введу тебя в курс дела:\n\n- Первые 24 часа после вступления запрещены:\nИнвайт\nЛюбые ссылки и @name обращения\nДобавление медиа, аудио, голос\nМожно только писать текст\n\n- Через 24 часа можно:\nПересылать сообщения\nПостить текст и фото\nОбращаться по @name\nРазрешать приглашать друзей\n\n\nА теперь докажи, что в тебе есть хоть капля человечности, и скажи, что это: {emojize(captcha.get_emoji())}', reply_markup=captcha.get_buttons())
        captcha.set_message_id(msg.message_id)
        cfg.non_authorized[chat_id].append(user_id)
        await asyncio.sleep(cfg.CAPTCHA_TIME)
        if user_id in cfg.non_authorized[chat_id]:
            await message.chat.kick(int(user_id))
            await bot.unban_chat_member(chat_id=chat_id, user_id=user_id)
            logging.info(f'Chat {chat_id}: User {user_id} was kicked out of chat because of captcha timeout')
            await bot.delete_message(chat_id=int(chat_id), message_id=captcha.get_message_id())
            cfg.non_authorized[chat_id].remove(user_id)


# **Не работает в тихом режиме**
# Обработка обычных сообщений (@name, ссылки, спам)
@dp.message_handler()
async def regular_message(message: types.Message):
    if message.text:
        chat_id = str(message.chat.id)
        user_id = message.from_user.id
        member = await bot.get_chat_member(chat_id, user_id)
        if not isinstance(member, types.ChatMemberOwner) and not isinstance(member, types.ChatMemberAdministrator):
            # Если сообщение от рядового юзера
            if str(message.chat.id) in cfg.silenced_chats:
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
                        if link.replace('http://', '').replace('https://', '') in cfg.blacklist:
                            await message.delete()
                            for chat_id in list(cfg.non_authorized.keys()): # Баним юзера из всех чатов
                                await bot.ban_chat_member(chat_id=chat_id, user_id=message.from_user.id, revoke_messages=True)
                            logging.info(f'User {user_id} was banned from all chats because of a forbidden link')
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
                logging.info(f'Chat {chat_id}: spam messages were deleted')

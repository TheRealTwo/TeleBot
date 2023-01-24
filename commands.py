# Функции команд

# files
import config as cfg
from bot import *
from sec_funcs import *
import database.database_adapter as db
# libs
from aiogram import types


# Команда бана вида /ban @username
# Банит юзера из всех чатов
@dp.message_handler(commands=["ban"])
async def ban_user(message: types.Message):
    sql = db.SqlAdapter()
    if str(message.from_user.id) not in cfg.ADMINS_ID or message.chat.type in ("group", "supergroup"):
        # Если команду отправляет левый пользователь или не в ЛС
        return None
    username = message.get_args().replace('@', '', 1) if message.get_args().startswith('@') else message.get_args()
    if not username:
        await message.answer('Вы забыли добавить юзернейм!')
        return None
    user = await sql.get_user(name=username)
    if not user:
        await message.answer('Такого юзера я не знаю! Возможно, вы найдёте что-то похожее в /users?')
    chats = await sql.get_chat(all=True)
    count = 0
    for chat_id in list(map(lambda x: str(x.id), chats)):
        await bot.ban_chat_member(chat_id=chat_id, user_id=str(user.id), revoke_messages=True)
        count += 1
    log(f'User {str(user.id)} was banned from all chats because of a command')
    await message.answer(f'Пользователь {username} забанен в {count} чатах!')
    await sql.delete_user(str(user.id))

# Команда вида /post
# Постит сообщение в выбранных чатах
@dp.message_handler(commands=['post'])
async def post_some_content(message: types.Message):
    if str(message.from_user.id) not in cfg.ADMINS_ID or message.chat.type in ("group", "supergroup"):
        # Если команду отправляет левый пользователь или не в ЛС
        return None
    cfg.post_chats = set()
    await message.answer('Выберите чаты, а затем отправьте мне то, что хотите разослать')
    await choose_chats(message, act='post')

# Команда вида /silence
# Вводит выбранные чаты в тихий режим
@dp.message_handler(commands=['silence'])
async def silence_chats(message: types.Message):
    if str(message.from_user.id) not in cfg.ADMINS_ID or message.chat.type in ("group", "supergroup"):
        # Если команду отправляет левый пользователь или не в ЛС
        return None
    await message.answer('Выберите чаты, которые будут в "тихом" режиме (каждый чат войдёт в тихий режим сразу после его нажатия)')
    await choose_chats(message, act='silence')


# Команда вида /unsilence
# Выводит выбранные чаты из тихого режима
@dp.message_handler(commands=['unsilence'])
async def silence_chats(message: types.Message):
    if str(message.from_user.id) not in cfg.ADMINS_ID or message.chat.type in ("group", "supergroup"):
        # Если команду отправляет левый пользователь или не в ЛС
        return None
    await message.answer('Выберите чаты, которые будут выведены из "тихого" режима (каждый чат выйдет из тихого режима сразу после его нажатия)')
    await choose_chats(message, act='unsilence')


# Команда вида /block link
# Добавляет ссылку в чёрный список
@dp.message_handler(commands=['block'])
async def block_link(message: types.Message):
    sql = db.SqlAdapter()
    if str(message.from_user.id) not in cfg.ADMINS_ID or message.chat.type in ("group", "supergroup"):
        # Если команду отправляет левый пользователь или не в ЛС
        return None
    link = message.get_args().replace('https://', '').replace('http://', '')
    if link:
        await sql.set_link(link)
        log(f'Link {link} was blocked')
        await message.answer('Ссылка заблокирована!')
    else:
        await message.answer('Вы забыли добавить ссылку!')


# Команда вида /unlock link
# Убирает ссылку из чёрного списка
@dp.message_handler(commands=['unlock'])
async def block_link(message: types.Message):
    sql = db.SqlAdapter()
    if str(message.from_user.id) not in cfg.ADMINS_ID or message.chat.type in ("group", "supergroup"):
        # Если команду отправляет левый пользователь или не в ЛС
        return None
    link = message.get_args().replace('https://', '').replace('http://', '')
    if not link:
        await message.answer('Вы забыли добавить ссылку!')
        return None
    db_link = await sql.get_link(link)
    if db_link:
        await sql.delete_link(link)
        log(f'Link {link} was unlocked')
        await message.answer('Ссылка разблокирована!')
    else:
        await message.answer('Такая ссылка не заблокирована!')


# Команда вида /show
# Показывает данные из config
@dp.message_handler(commands=['show'])
async def show_config(message: types.Message):
    sql = db.SqlAdapter()
    if str(message.from_user.id) not in cfg.ADMINS_ID or message.chat.type in ("group", "supergroup"):
        # Если команду отправляет левый пользователь или не в ЛС
        return None
    chats = await sql.get_chat(all=True)
    chats = list(map(lambda y: y.title, filter(lambda x: x.is_silenced, chats)))
    links = await sql.get_link(all=True)
    n_char = '\n'
    await message.answer(f"Вот текущие данные:\n\nЗаблокированные ссылки:\n{n_char.join(links)}\n\nЗаглушённые чаты:\n\n{n_char.join(chats)}")

# Команда вида /users
# Показывает users из config.py
@dp.message_handler(commands=['users'])
async def show_config(message: types.Message):
    sql = db.SqlAdapter()
    if str(message.from_user.id) not in cfg.ADMINS_ID or message.chat.type in ("group", "supergroup"):
        # Если команду отправляет левый пользователь или не в ЛС
        return None
    users = await sql.get_user(all=True)
    users = list(map(lambda x: x.name, users))
    text = 'Вот текущий список юзеров:\n\n' + '\n'.join(sorted(users))
    await message.answer(text)


# Команда вида /help или /start
# Выводит все команды с их описанием, а так же почёсывает эго заказчика
@dp.message_handler(commands=['start', 'help'])
async def show_help(message: types.Message):
    if str(message.from_user.id) not in cfg.ADMINS_ID or message.chat.type in ("group", "supergroup"):
        # Если команду отправляет левый пользователь или не в ЛС
        return None
    await message.answer('Поздравляем! Вы одни из тех, кто может управлять ботом (ваш ID есть в конфигурационном файле config.py), вы - элита элит!\n\nВот доступные команды:\n\n/help - вывод этого сообщения\n\n/ban @user или /ban user - бан этого юзера во всех чатах\nВНИМАНИЕ! У некоторых юзеров нет @name, чтобы забанить такого, вместо ника пишите имя (без фамилии, т.е. первое слово)\n\n/post - Постит ваше сообщение\nпосле команды выберите нужные вам чаты, а затем отправьте боту то, что хотите опубликовать\n\n/block link - Заносит ссылку в чёрный список (link - ваша ссылка)\n\n/unlock link - (не путать с unblock) - убирает ссылку из чёрного списка (link - ваша ссылка)\n\n/silence - вводит выбранные чаты в тихий режим\nВНИМАНИЕ! Чаты будут введены сразу после нажатия кнопок, так что потом не нужно ничего отправлять\n\n/unsilence - выводит выбранные чаты из тихого режима\nИзменения вступят в силу сразу же, так же, как и при /silence\n\n\nДля корректной работы бота, не создавайте группу вместе с ботом, а добавляйте его в уже существующую, т.к. в первом случае бот не будет отлавливать это событие, и не будет знать о существовании беседы.\n\n/show - показывает заблокированные ссылки и чаты, работающие в тихом режиме, на данный момент\n\n/users - показывает имена всех пользователей, зафиксированных ботом (именно по этим именам баньте юзеров)\n\nУдачи в использовании!')

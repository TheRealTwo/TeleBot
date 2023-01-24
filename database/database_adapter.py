import pathlib

import aiosqlite
from aiosqlite import Connection, Cursor

SqliteFile = str(pathlib.Path(__file__).parent/"database.db")
# CREATE TABLE Users(id INT PRIMARY KEY, name STRING UNIQUE, is_authorized BOOL);
# CREATE TABLE Chats(id INT PRIMARY KEY, is_silenced BOOL, title TEXT);
# CREATE TABLE Blacklist(link STRING)
class SqlStructure(object):
    def __init__(self, data):
        self._data = data

    def __getattribute__(self, item):
        if item[0] == '_': return super().__getattribute__(item)
        return self._data[item]

    def __setattr__(self, key, value):
        if key[0] == '_': return super().__setattr__(key, value)
        self._data[key] = value

    @property
    def data(self): return self._data


class User(SqlStructure):
    id: int
    name: str
    is_authorized: bool


class Chat(SqlStructure):
    id: int
    title: str
    is_silenced: int


class SqlAdapter:

    async def create_tables(self):
        async with aiosqlite.connect(str(SqliteFile)) as connection:
            await connection.execute("CREATE TABLE IF NOT EXISTS Users(id INT PRIMARY KEY, name STRING UNIQUE, is_authorized BOOL);")
            await connection.execute("CREATE TABLE IF NOT EXISTS Chats(id INT PRIMARY KEY, title STRING, is_silenced BOOL);")
            await connection.execute("CREATE TABLE IF NOT EXISTS Blacklist(link STRING UNIQUE);")
            await connection.commit()


    async def set_user(self, user: User):
        async with aiosqlite.connect(str(SqliteFile)) as connection:
            await connection.execute(
                "INSERT INTO Users(id, name, is_authorized) VALUES (?, ?, ?) ON "
                "CONFLICT(id) DO UPDATE SET is_authorized = ?;",
                (user.id, user.name, user.is_authorized, user.is_authorized))
            await connection.commit()

    async def get_user(self, user_id='', name='', all=None):
        async with aiosqlite.connect(str(SqliteFile)) as connection:
            cursor = await connection.cursor()
            if all:
                await cursor.execute("SELECT * FROM Users")
                item = await cursor.fetchall()
                return [User({'id': i[0], 'name': i[1], 'is_authorized': i[2]}) for i in item] if item else None
            elif user_id:
                await cursor.execute("SELECT * FROM Users WHERE id = ?", (user_id, ))
                item = await cursor.fetchone()
                return User({'id': item[0], 'name': item[1], 'is_authorized': item[2]}) if item else None
            else:
                await cursor.execute("SELECT * FROM Users WHERE name = ?", (name, ))
                item = await cursor.fetchone()
                return User({'id': item[0], 'name': item[1], 'is_authorized': item[2]}) if item else None

    async def delete_user(self, user_id):
        async with aiosqlite.connect(str(SqliteFile)) as connection:
            await connection.execute("DELETE FROM Users WHERE id = ?", (user_id, ))
            await connection.commit()


    async def set_chat(self, chat: Chat):
        async with aiosqlite.connect(str(SqliteFile)) as connection:
            await connection.execute(
                "INSERT INTO Chats(id, title, is_silenced) VALUES (?, ?, ?) ON "
                "CONFLICT(id) DO UPDATE SET is_silenced = ?, title = ?;",
                (chat.id, chat.title, chat.is_silenced, chat.is_silenced, chat.title))
            await connection.commit()

    async def get_chat(self, chat_id='', all=None):
        async with aiosqlite.connect(str(SqliteFile)) as connection:
            cursor = await connection.cursor()
            if all:
                await cursor.execute("SELECT * FROM Chats")
                item = await cursor.fetchall()
                return [Chat({'id': i[0], 'title': i[1], 'is_silenced': i[2]}) for i in item] if item else None
            else:
                await cursor.execute("SELECT * FROM Chats WHERE id = ?", (chat_id, ))
                item = await cursor.fetchone()
                return Chat({'id': item[0], 'title': item[1], 'is_silenced': item[2]}) if item else None

    async def delete_chat(self, chat_id):
        async with aiosqlite.connect(str(SqliteFile)) as connection:
            await connection.execute("DELETE FROM Chats WHERE id = ?", (chat_id, ))
            await connection.commit()

    async def set_link(self, link):
        async with aiosqlite.connect(str(SqliteFile)) as connection:
            await connection.execute("INSERT INTO Blacklist(link) VALUES (?) ON CONFLICT(link) DO UPDATE SET link = ?;", (link, link))
            await connection.commit()

    async def get_link(self, link='', all=None):
        async with aiosqlite.connect(str(SqliteFile)) as connection:
            cursor = await connection.cursor()
            if all:
                await cursor.execute("SELECT * FROM Blacklist")
                item = await cursor.fetchall()
                return [i[0] for i in item] if item else []
            else:
                await cursor.execute("SELECT * FROM Blacklist WHERE link = ?", (link, ))
                item = await cursor.fetchone()
                return item[0] if item else None

    async def delete_link(self, link):
        async with aiosqlite.connect(str(SqliteFile)) as connection:
            await connection.execute("DELETE FROM Blacklist WHERE link = ?;", (link, ))
            await connection.commit()

#files
from states import *
from callbacks import *
from commands import *
from classes import *
from sec_funcs import *
from handlers import *
from bot import *
import database.database_adapter as db
#libs
from aiogram import executor

# run long-polling
if __name__ == '__main__':
    sql = db.SqlAdapter()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(sql.create_tables())
    log('------------MAIN.PY HAS STARTED------------')
    try:
        executor.start_polling(dp, skip_updates=True)
    except Exception as e:
        log(e, exception=e)

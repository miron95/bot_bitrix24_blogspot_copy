from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import webhook, tkn

bot = Bot(tkn)
dp = Dispatcher(bot, storage=MemoryStorage())
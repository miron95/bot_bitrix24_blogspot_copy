import logging

from aiogram import Dispatcher, types
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext

from create_bot import bot
from config import admin_id

logging.basicConfig(level=logging.INFO)

class SpamMessage(StatesGroup):
    message_text = State()
    to_send = State()

async def send_spam(message: types.Message):
    if str(message.from_user.id) != admin_id:
        await message.reply(f'Это только для администратора! Ваш ID: {message.from_user.id}')
    else:
        await message.reply('Напишите текст сообщения')
        await SpamMessage.message_text.set()

async def msg_text_message(message: types.Message, state: FSMContext):
    await state.update_data(text = message.text)
    await message.reply('Введите ID чата для отправки')
    await SpamMessage.next()

async def msg_to_send(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        text = data['text']
        await bot.send_message(message.text, text=text)
        await message.reply(f'Сообщение "{text}"\n\n'
                            f'Было отправлено в чат {message.text}')
    await state.finish()

def register_admin_stages(dp: Dispatcher):
    dp.register_message_handler(send_spam, commands='send_spam')
    dp.register_message_handler(msg_text_message, state=SpamMessage.message_text)
    dp.register_message_handler(msg_to_send, state=SpamMessage.to_send)
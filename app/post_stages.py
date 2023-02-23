import logging
import base64
import io

from fast_bitrix24 import BitrixAsync
from aiogram import Dispatcher, types
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext

from create_bot import bot
from config import webhook, chat_group_id

logging.basicConfig(level=logging.INFO)

b = BitrixAsync(webhook, verbose=False)


class PostBitrix(StatesGroup):
    title_step = State()
    text_step = State()
    url_step = State()
    dep_step = State()
    important_step = State()
    doc_step = State()
    check = State()
    send_message_step = State()


async def start(message: types.Message):
    if str(message.chat.id) != chat_group_id:
        print(str(message.chat.id))
        await message.reply(f'Вы не можете писать в ЛС боту! ID чата: {message.chat.id}')

    else:
        await message.reply('Напишите любое сообщение, чтобы отправить его в Живую ленту в Битрикс')

        await message.answer('Введите заголовок сообщения:')
        await PostBitrix.title_step.set()


async def msg_title_step(message: types.Message, state: FSMContext):
    if message.text == '/stop':
        await message.reply('Создание сообщения прервано пользователем ' + message.from_user.first_name)
        await state.finish()
        return

    await state.update_data(title=message.text)
    await PostBitrix.next()
    await message.reply('Теперь напишите текст сообщения:')


async def msg_text_step(message: types.Message, state: FSMContext):
    if message.text == '/stop':
        await message.reply('Создание сообщения прервано пользователем ' + message.from_user.first_name)
        await state.finish()
        return

    await state.update_data(text=message.text)
    await PostBitrix.next()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton(text='Не добавлять изображение'))

    await message.reply('Если нужно, можете добавить ссылку на изображение.\n'
                        'Если вы не хотите добавлять изображение,\n'
                        'просто нажмите на кнопку <b>"Не добавлять изображение"</b>',
                        reply_markup=markup, parse_mode='HTML')


async def msg_url_step(message: types.Message, state: FSMContext):
    if message.text == '/stop':
        await message.reply('Создание сообщения прервано пользователем ' + message.from_user.first_name)
        await state.finish()
        return

    url = message.text
    if url == 'Не добавлять изображение':
        await state.update_data(url='')
    else:
        if url.startswith('https://') or url.startswith('http://'):
            await state.update_data(url=f'<img src="{url}">')
        else:
            url = 'https://' + url
            await state.update_data(url=f'<img src="{url}">')

    await PostBitrix.next()
    search = await b.call('department.get', None, raw=True)
    search = search.get('result')
    markup = types.ReplyKeyboardMarkup(row_width=1)
    button_list = []
    for dep in search:
        button = types.KeyboardButton(text=dep.get('NAME'))
        button_list.append(button)
    markup.add(*button_list)
    await message.reply(f'Теперь выберите подразделение для отправки\n'
                        f'Если хотите отправить всем сотрудникам,\n выберите <b>"Group Company"</b>',
                        reply_markup=markup, parse_mode='HTML')


async def msg_dep_step(message: types.Message, state: FSMContext):
    if message.text == '/stop':
        await message.reply('Создание сообщения прервано пользователем ' + message.from_user.first_name)
        await state.finish()
        return

    try:
        current_dep = await b.call('department.get', {'NAME': f"{str(message.text)}"}, raw=True)
        current_dep = current_dep.get('result')
        await state.update_data(id_dep=str(current_dep[0]['ID']))
        await state.update_data(name_dep=str(current_dep[0]['NAME']))
    except Exception as e:
        print(e)
        await state.update_data(id_dep='1')
        await state.update_data(name_dep='Group Company')
        await message.reply('<b>Неверно указано подразделение!</b>\n\n'
                            '<b>Сообщение будет отправлено всем пользователям!!!</b>', parse_mode='HTML')

    await PostBitrix.next()
    markup = types.ReplyKeyboardMarkup(row_width=1)
    button_y = types.KeyboardButton(text='ДА')
    button_n = types.KeyboardButton(text='НЕТ')
    markup.add(button_y, button_n)
    await message.reply('Сделать сообщение <b>важным</b>?\n\n'
                        'Выберите ДА / НЕТ', reply_markup=markup, parse_mode='HTML')


async def msg_important_step(message: types.Message, state: FSMContext):
    if message.text == '/stop':
        await message.reply('Создание сообщения прервано пользователем ' + message.from_user.first_name)
        await state.finish()
        return

    if message.text == 'ДА':
        await state.update_data(important='Y')
    else:
        await state.update_data(important='N')

    async with state.proxy() as post_data:
        post_data['files'] = []

    await PostBitrix.next()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('Не добавлять файл'))
    await message.reply('Можете добавить файл(не более 20Мб)\n'
                        'или нажмите на кнопку "Не добавлять файл".'
                        'Добавляйте файлы по одному.', reply_markup=markup)


async def msg_doc_step(message: types.Message, state: FSMContext):
    if message.text == '/stop':
        await message.reply('Создание сообщения прервано пользователем ' + message.from_user.first_name)
        await state.finish()
        return
    elif message.text == 'Не добавлять файл':
        await PostBitrix.next()
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton('Проверить данные'))
        await message.reply('Нажмите "Проверить данные" для проверки', reply_markup=markup)
        return

    if message.content_type == 'document':
        if message.media_group_id is None:
            file_info = await bot.get_file(message.document.file_id)
            binary_file = io.BytesIO()
            await bot.download_file(file_info.file_path, binary_file)
            file = [message.document.file_name, base64.b64encode(binary_file.read()).decode('utf-8')]

            async with state.proxy() as post_data:
                post_data['files'].append(file)
            binary_file.close()

            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(types.KeyboardButton('Не добавлять файл'), types.KeyboardButton('Добавить еще файл'))
            await message.reply('Желаете еще добавить файлы?', reply_markup=markup)
            await PostBitrix.next()
        else:
            await message.reply('Отправляйте документы по одному!!')
    else:
        await message.reply('Вы отправили не документ')


async def check(message: types.Message, state: FSMContext):
    if message.text == 'Добавить еще файл':
        await PostBitrix.doc_step.set()
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton('Не добавлять файл'))
        await message.reply('Загрузите файл или нажмите на кнопку "Не добавлять файл"', reply_markup=markup)
        return
    elif message.text == '/stop':
        await message.reply('Создание сообщения прервано пользователем ' + message.from_user.first_name)
        await state.finish()
        return

    else:

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("ОК"), types.KeyboardButton("ЗАНОВО"))

        async with state.proxy() as post_data:

            if not post_data['files']:
                files_str = ' - '
            else:
                files = []
                for file in post_data['files']:
                    files.append(''.join(file[::2]))
                files_str = '\n'.join(files)

            url = str(post_data['url']).replace('<img src="', '').replace('">', '')
            await message.reply(f'Готово! Проверьте правильность данных:\n\n'
                                f'<b>Заголовок:</b> {post_data["title"]}\n\n'
                                f'<b>Текст:</b> {post_data["text"]}\n\n'
                                f'<b>Ссылка на картинку:</b> {url}\n\n'
                                f'<b>Подразделение для получения:</b> {post_data["name_dep"]},'
                                f' id = {post_data["id_dep"]}\n\n '
                                f'<b>Важное сообщение:</b> {"ДА" if post_data["important"] == "Y" else "НЕТ"}\n\n'
                                f'<b>Файлы:</b>\n{files_str}', parse_mode='HTML')
            await PostBitrix.next()
            await message.answer(f'Нажмите <b>"OK"</b> для отправки ЖЛ.\n\n'
                                 f'Если хотите ввести данные заново, нажмите <b>"ЗАНОВО"</b>',
                                 parse_mode='HTML',
                                 reply_markup=markup)


async def msg_send_step(message: types.Message, state: FSMContext):
    if message.text == '/stop':
        await message.reply('Создание сообщения прервано пользователем ' + message.from_user.first_name)
        await state.finish()
        return

    markup = types.ReplyKeyboardRemove()

    if message.text == "ОК":
        async with state.proxy() as post_data:
            num = await b.call('log.blogpost.add', {'POST_MESSAGE': f'{post_data["text"]}\n'
                                                                    f'{post_data["url"]}',
                                                    'POST_TITLE': post_data["title"],
                                                    'DEST': [f'DR{post_data["id_dep"]}'],
                                                    'IMPORTANT': f'{post_data["important"]}',
                                                    'FILES': post_data["files"]})

            await message.reply(f"Сообщение отправлено в ЖЛ под номером {num}\n"
                                f"Введите /start чтобы создать новое сообщение", reply_markup=markup)
            await state.finish()
    else:
        await message.reply("Сообщение удалено.\n"
                            "Чтобы начать заново введите /start", reply_markup=markup)
        await state.finish()


def register_post_stages(dp: Dispatcher):
    dp.register_message_handler(start, commands='start')
    dp.register_message_handler(msg_title_step, state=PostBitrix.title_step)
    dp.register_message_handler(msg_text_step, state=PostBitrix.text_step)
    dp.register_message_handler(msg_url_step, state=PostBitrix.url_step)
    dp.register_message_handler(msg_dep_step, state=PostBitrix.dep_step)
    dp.register_message_handler(msg_important_step, state=PostBitrix.important_step)
    dp.register_message_handler(msg_doc_step, state=PostBitrix.doc_step, content_types=['document', 'text'])
    dp.register_message_handler(check, state=PostBitrix.check)
    dp.register_message_handler(msg_send_step, state=PostBitrix.send_message_step)

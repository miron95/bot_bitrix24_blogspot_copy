import asyncio
import logging
import sys

from aiogram.types import BotCommand

from create_bot import dp, bot
from app.post_stages import register_post_stages
from app.admin import register_admin_stages


logger = logging.getLogger(__name__)



# Регистрация команд, отображаемых в интерфейсе Telegram
async def set_commands():
    commands = [
        BotCommand(command="/start", description="Создать новое сообщение в ЖЛ"),
        BotCommand(command="/stop", description="Прервать создание сообщения")
    ]
    await bot.set_my_commands(commands)


async def main():
    # Настройка логирования в stdout
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    logger.error("Starting bot")
    logging.getLogger('fast_bitrix24').setLevel(logging.ERROR)







    # Регистрация хэндлеров
    register_post_stages(dp)
    register_admin_stages(dp)

    # Установка команд бота
    await set_commands()

    # Запуск поллинга с пропуском обновлений
    await dp.skip_updates()
    await dp.start_polling()


if __name__ == '__main__':
    asyncio.run(main())

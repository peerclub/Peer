import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ChatPermissions
from dotenv import load_dotenv
import asyncio

# Загрузка токена из .env файла
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# Настройка бота
logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Словарь предупреждений
warnings = {}

# Проверка прав администратора
async def is_admin(message: types.Message):
    chat_admins = [admin.user.id for admin in await message.chat.get_administrators()]
    return message.from_user.id in chat_admins

# Команда /ban
@dp.message_handler(commands=["ban"], is_chat_admin=True)
async def ban_user(message: types.Message):
    if message.reply_to_message:
        await bot.kick_chat_member(message.chat.id, message.reply_to_message.from_user.id)
        await message.reply(f"Пользователь {message.reply_to_message.from_user.full_name} забанен.")

# Команда /unban
@dp.message_handler(commands=["unban"], is_chat_admin=True)
async def unban_user(message: types.Message):
    if len(message.text.split()) > 1:
        user_id = int(message.text.split()[1])
        await bot.unban_chat_member(message.chat.id, user_id)
        await message.reply(f"Пользователь {user_id} разбанен.")

# Команда /mute
@dp.message_handler(commands=["mute"], is_chat_admin=True)
async def mute_user(message: types.Message):
    if message.reply_to_message:
        await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id,
                                       permissions=ChatPermissions(can_send_messages=False))
        await message.reply(f"Пользователь {message.reply_to_message.from_user.full_name} замьючен.")

# Команда /unmute
@dp.message_handler(commands=["unmute"], is_chat_admin=True)
async def unmute_user(message: types.Message):
    if message.reply_to_message:
        await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id,
                                       permissions=ChatPermissions(can_send_messages=True))
        await message.reply(f"Пользователь {message.reply_to_message.from_user.full_name} размьючен.")

# Команда /kick
@dp.message_handler(commands=["kick"], is_chat_admin=True)
async def kick_user(message: types.Message):
    if message.reply_to_message:
        await bot.kick_chat_member(message.chat.id, message.reply_to_message.from_user.id)
        await bot.unban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
        await message.reply(f"Пользователь {message.reply_to_message.from_user.full_name} кикнут.")

# Команда /warn
@dp.message_handler(commands=["warn"], is_chat_admin=True)
async def warn_user(message: types.Message):
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        warnings[user_id] = warnings.get(user_id, 0) + 1
        await message.reply(f"Пользователь {message.reply_to_message.from_user.full_name} получил предупреждение ({warnings[user_id]}/3).")
        if warnings[user_id] >= 3:
            await bot.kick_chat_member(message.chat.id, user_id)
            await message.reply(f"Пользователь {message.reply_to_message.from_user.full_name} забанен за 3 предупреждения.")

# Команда /warnings
@dp.message_handler(commands=["warnings"], is_chat_admin=True)
async def check_warnings(message: types.Message):
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        warn_count = warnings.get(user_id, 0)
        await message.reply(f"У {message.reply_to_message.from_user.full_name} {warn_count} предупреждений.")

# Команда /clearwarns
@dp.message_handler(commands=["clearwarns"], is_chat_admin=True)
async def clear_warnings(message: types.Message):
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        warnings[user_id] = 0
        await message.reply(f"Предупреждения для {message.reply_to_message.from_user.full_name} очищены.")

# Команда /pin
@dp.message_handler(commands=["pin"], is_chat_admin=True)
async def pin_message(message: types.Message):
    if message.reply_to_message:
        await bot.pin_chat_message(message.chat.id, message.reply_to_message.message_id)
        await message.reply("Сообщение закреплено.")

# Команда /unpin
@dp.message_handler(commands=["unpin"], is_chat_admin=True)
async def unpin_message(message: types.Message):
    await bot.unpin_chat_message(message.chat.id)
    await message.reply("Сообщение откреплено.")

# Команда /purge
@dp.message_handler(commands=["purge"], is_chat_admin=True)
async def purge_messages(message: types.Message):
    if len(message.text.split()) > 1:
        count = int(message.text.split()[1])
        chat = message.chat.id
        messages_to_delete = [message.message_id]
        async for msg in bot.iter_chat_history(chat, limit=count):
            messages_to_delete.append(msg.message_id)
        await bot.delete_messages(chat, messages_to_delete)
        await message.reply(f"Удалено {count} сообщений.")

# Запуск бота
async def main():
    await dp.start_polling()

if __name__ == "__main__":
    asyncio.run(main())

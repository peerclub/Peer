import logging
import os
import openai
from aiogram import Bot, Dispatcher, types
from aiogram.types import ChatPermissions
from aiogram.utils import executor
from dotenv import load_dotenv

# Загрузка переменных из .env
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Настройка бота и OpenAI
logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
openai.api_key = OPENAI_API_KEY

# Словарь предупреждений
warnings = {}

# Функция для общения с ИИ
async def get_ai_response(user_message):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": user_message}]
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        logging.error(f"Ошибка OpenAI: {e}")
        return "Что-то пошло не так, попробуй позже."

# Команда /admins — список администраторов
@dp.message_handler(commands=["admins"], is_chat_admin=True)
async def list_admins(message: types.Message):
    chat_admins = await message.chat.get_administrators()
    admin_names = [admin.user.full_name for admin in chat_admins]
    await message.reply(f"Администраторы чата:\n" + "\n".join(admin_names))

# Команды модерации
@dp.message_handler(commands=["ban"], is_chat_admin=True)
async def ban_user(message: types.Message):
    if message.reply_to_message:
        await bot.kick_chat_member(message.chat.id, message.reply_to_message.from_user.id)
        await message.reply(f"Пользователь {message.reply_to_message.from_user.full_name} забанен.")

@dp.message_handler(commands=["unban"], is_chat_admin=True)
async def unban_user(message: types.Message):
    if len(message.text.split()) > 1:
        user_id = int(message.text.split()[1])
        await bot.unban_chat_member(message.chat.id, user_id)
        await message.reply(f"Пользователь {user_id} разбанен.")

@dp.message_handler(commands=["mute"], is_chat_admin=True)
async def mute_user(message: types.Message):
    if message.reply_to_message:
        await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id,
                                       permissions=ChatPermissions(can_send_messages=False))
        await message.reply(f"Пользователь {message.reply_to_message.from_user.full_name} замьючен.")

@dp.message_handler(commands=["unmute"], is_chat_admin=True)
async def unmute_user(message: types.Message):
    if message.reply_to_message:
        await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id,
                                       permissions=ChatPermissions(can_send_messages=True))
        await message.reply(f"Пользователь {message.reply_to_message.from_user.full_name} размьючен.")

@dp.message_handler(commands=["kick"], is_chat_admin=True)
async def kick_user(message: types.Message):
    if message.reply_to_message:
        await bot.kick_chat_member(message.chat.id, message.reply_to_message.from_user.id)
        await bot.unban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
        await message.reply(f"Пользователь {message.reply_to_message.from_user.full_name} кикнут.")

@dp.message_handler(commands=["warn"], is_chat_admin=True)
async def warn_user(message: types.Message):
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        warnings[user_id] = warnings.get(user_id, 0) + 1
        await message.reply(f"Пользователь {message.reply_to_message.from_user.full_name} получил предупреждение ({warnings[user_id]}/3).")
        if warnings[user_id] >= 3:
            await bot.kick_chat_member(message.chat.id, user_id)
            await message.reply(f"Пользователь {message.reply_to_message.from_user.full_name} забанен за 3 предупреждения.")

@dp.message_handler(commands=["warnings"], is_chat_admin=True)
async def check_warnings(message: types.Message):
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        warn_count = warnings.get(user_id, 0)
        await message.reply(f"У {message.reply_to_message.from_user.full_name} {warn_count} предупреждений.")

@dp.message_handler(commands=["clearwarns"], is_chat_admin=True)
async def clear_warnings(message: types.Message):
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        warnings[user_id] = 0
        await message.reply(f"Предупреждения для {message.reply_to_message.from_user.full_name} очищены.")

@dp.message_handler(commands=["pin"], is_chat_admin=True)
async def pin_message(message: types.Message):
    if message.reply_to_message:
        await bot.pin_chat_message(message.chat.id, message.reply_to_message.message_id)
        await message.reply("Сообщение закреплено.")

@dp.message_handler(commands=["unpin"], is_chat_admin=True)
async def unpin_message(message: types.Message):
    await bot.unpin_chat_message(message.chat.id)
    await message.reply("Сообщение откреплено.")

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

# Бот отвечает на любые сообщения в чате с помощью ИИ
@dp.message_handler()
async def chat_with_ai(message: types.Message):
    response = await get_ai_response(message.text)
    await message.reply(response)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)

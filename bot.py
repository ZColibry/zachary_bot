import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile
from aiogram.filters import CommandStart
from aiogram.client.default import DefaultBotProperties

from telethon import TelegramClient
from telethon.errors import UserNotParticipantError
from telethon.tl.functions.channels import GetParticipantRequest

from dotenv import load_dotenv
import os

# Загрузка переменных из .env
load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
channel_username = os.getenv(
    "CHANNEL_USERNAME"
)  # Важно, с @ или без — используй как в Telethon

# === Инициализация ===
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
telethon_client = TelegramClient("checker_session", API_ID, API_HASH)

# === Клавиатуры ===
main_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Книги 📖", callback_data="books"),
            InlineKeyboardButton(text="Сон 💤", callback_data="sleep"),
        ],
        [
            InlineKeyboardButton(
                text="Полезный материал 📝", callback_data="materials"
            ),
            InlineKeyboardButton(text="Обо мне", callback_data="about"),
        ],
    ]
)

books_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Зачем мы спим Меттью Уолкер 💤", callback_data="book_sleep"
            )
        ],
        [
            InlineKeyboardButton(
                text="Магия утра Хэл Элрод 🌅", callback_data="book_morning"
            )
        ],
        [InlineKeyboardButton(text="Назад ⏪", callback_data="back_main")],
    ]
)

subscribe_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Colibry", url="https://t.me/zcolibry")],
        [
            InlineKeyboardButton(
                text="Проверить подписку", callback_data="check_subscribe"
            )
        ],
        [InlineKeyboardButton(text="Назад ⏪", callback_data="back_books")],
    ]
)

back_to_main_menu = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text="Назад ⏪", callback_data="back_main")]]
)

back_to_books_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Назад ⏪", callback_data="back_books")]
    ]
)

# === Память о выборе книги ===
user_book_request = {}


# === Удаление сообщений ===
async def delete_message(message: types.Message | types.CallbackQuery):
    try:
        if isinstance(message, types.CallbackQuery):
            await message.message.delete()
        else:
            await message.delete()
    except:
        pass


# === Проверка подписки ===
async def check_subscription(user_id: int) -> bool:
    await telethon_client.start()
    try:
        await telethon_client(
            GetParticipantRequest(channel=channel_username, participant=user_id)
        )
        return True
    except UserNotParticipantError:
        return False
    except Exception as e:
        print(f"Ошибка Telethon при проверке подписки: {e}")
        return False


# === Обработка /start ===
@dp.message(CommandStart())
async def start_handler(message: types.Message):
    user_name = message.from_user.first_name or "друг"
    text = (
        f"Привет {user_name}, меня зовут Закари, я твой наставник в мир саморазвития и достижений целей🎯\n"
        "Скорей выбери какой пак ты хочешь получить📄:\n"
        '(Если хочешь узнать обо мне больше, жми кнопку: "Обо мне")'
    )
    await message.answer(text, reply_markup=main_menu)


# === Кнопка "Книги" ===
@dp.callback_query(F.data == "books")
async def books_handler(callback: types.CallbackQuery):
    await delete_message(callback)
    await callback.message.answer(
        "Выбери книгу которую хочешь получить📖:", reply_markup=books_menu
    )
    await callback.answer()


# === Нажата книга ===
@dp.callback_query(F.data.in_({"book_sleep", "book_morning"}))
async def send_book(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_book_request[user_id] = callback.data

    await callback.message.delete()  # Удалим предыдущее сообщение

    subscribed = await check_subscription(user_id)
    if not subscribed:
        await callback.message.answer(
            "Перед тем как я отправлю тебе эту книгу, подпишись на мой канал📹.",
            reply_markup=subscribe_menu,
        )
        await callback.answer()
        return

    await send_book_file(callback, user_id, callback.data)


# === Проверка подписки ===
@dp.callback_query(F.data == "check_subscribe")
async def check_subscribe(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    book_data = user_book_request.get(user_id)

    if not book_data:
        await delete_message(callback)
        await callback.message.answer(
            "Выбери книгу которую хочешь получить📖:", reply_markup=books_menu
        )
        await callback.answer()
        return

    subscribed = await check_subscription(user_id)
    if subscribed:
        await callback.message.delete()
        await send_book_file(callback, user_id, book_data)
        user_book_request.pop(user_id, None)
        await callback.answer("Спасибо за подписку! Книга отправлена.")
    else:
        await callback.answer("Вы не подписаны на канал", show_alert=True)


# === Отправка книги (в одном сообщении) ===
async def send_book_file(callback, user_id, book_data):
    if book_data == "book_sleep":
        book_path = "files/zachem_my_spim.epub"
    else:
        book_path = "files/magiya_utra.epub"

    file = FSInputFile(book_path)

    back_button = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Назад ⏪", callback_data="back_main")]
        ]
    )

    await bot.send_document(
        chat_id=user_id, document=file, caption="Держи книгу)", reply_markup=back_button
    )


# === Кнопка "Сон" ===
@dp.callback_query(F.data == "sleep")
async def sleep_handler(callback: types.CallbackQuery):
    await delete_message(callback)
    await callback.message.answer(
        "Совсем скоро здесь появится моя авторская программа по сну)...",
        reply_markup=back_to_main_menu,
    )
    await callback.answer()


# === Кнопка "Полезный материал" ===
@dp.callback_query(F.data == "materials")
async def materials_handler(callback: types.CallbackQuery):
    await delete_message(callback)
    await callback.message.answer(
        "Совсем скоро здесь появятся мои авторские материалы по саморазвитию)...",
        reply_markup=back_to_main_menu,
    )
    await callback.answer()


# === Кнопка "Обо мне" ===
@dp.callback_query(F.data == "about")
async def about_handler(callback: types.CallbackQuery):
    await delete_message(callback)
    await callback.message.answer(
        "Совсем скоро здесь появится вся необходимая информация обо мне)...",
        reply_markup=back_to_main_menu,
    )
    await callback.answer()


# === Назад в главное меню ===
@dp.callback_query(F.data == "back_main")
async def back_to_main_handler(callback: types.CallbackQuery):
    await delete_message(callback)
    user_name = callback.from_user.first_name or "друг"
    text = (
        f"Привет {user_name}, меня зовут Закари, я твой наставник в мир саморазвития и достижений целей🎯\n"
        "Скорей выбери какой пак ты хочешь получить📄:\n"
        '(Если хочешь узнать обо мне больше жми кнопку "Обо мне")'
    )
    await callback.message.answer(text, reply_markup=main_menu)
    await callback.answer()


# === Назад в книги ===
@dp.callback_query(F.data == "back_books")
async def back_to_books_handler(callback: types.CallbackQuery):
    await delete_message(callback)
    await callback.message.answer(
        "Выбери книгу которую хочешь получить📖:", reply_markup=books_menu
    )
    await callback.answer()


# === Запуск бота ===
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

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

from sleep_energy import sleep_energy_menu, energy_materials_back, sleep_calc_start_menu, sleep_result_back
from energy_back_button import energy_back_button
from sleep_calculator_state import SleepCalcState
from aiogram.fsm.context import FSMContext

# Загрузка переменных из .env
load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
channel_username = os.getenv(
    "CHANNEL_USERNAME"
)  # Важно, с @ или без — использовать как в Telephon

# === Инициализация ===
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
telethon_client = TelegramClient("checker_session", API_ID, API_HASH)

# === Клавиатуры ===
main_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="👨🏼‍💻 Обо мне", callback_data="about")
        ],
        [
            InlineKeyboardButton(text="🛌 Сон и энергия", callback_data="sleep_energy"),
            InlineKeyboardButton(text="📌 Мой путь", callback_data="my_way"),
        ],
        [
            InlineKeyboardButton(text="🧩 Полезные материалы", callback_data="materials"),
            InlineKeyboardButton(text="💡 Мотивация", callback_data="motivation"),
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


# === Кнопка "Полезные материалы" ===
@dp.callback_query(F.data == "materials")
async def materials_handler(callback: types.CallbackQuery):
    await delete_message(callback)
    await callback.message.answer(
        "🧩 Здесь ты найдёшь лучшие материалы для саморазвития: книги, чек-листы, подборки, сервисы и многое другое!",
        reply_markup=books_menu,
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
            "🧩 Здесь ты найдёшь лучшие материалы для саморазвития: книги, чек-листы, подборки, сервисы и многое другое!",
            reply_markup=books_menu,
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


# === Отправка книги ===
async def send_book_file(callback, user_id, book_data):
    if book_data == "book_sleep":
        book_path = "files/zachem_my_spim.epub"
    else:
        book_path = "files/magiya_utra.epub"

    file = FSInputFile(book_path)

    buttons = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📘 Инструкция по открытию файла", callback_data="open_guide"
                )
            ],
            [InlineKeyboardButton(text="Назад ⏪", callback_data="back_main")],
        ]
    )

    await bot.send_document(
        chat_id=user_id,
        document=file,
        caption="Держи книгу)",
        reply_markup=buttons,
    )


# === Инструкция по открытию файла ===
@dp.callback_query(F.data == "open_guide")
async def open_guide_handler(callback: types.CallbackQuery):
    await callback.message.answer(
        "🍏 <b>Открытие файла книги на IOS</b>\n\n"
        "1️⃣ Скачай приложение <i>«Книги»</i> (белая книга на оранжевом фоне) из App Store.\n"
        "2️⃣ Открой файл книги и нажми кнопку <i>«Отправить»</i> (иконка коробочки со стрелкой).\n"
        "3️⃣ Выбери приложение <i>«Книги»</i> из списка.\n"
        "4️⃣ Готово ✅ — книга в твоей библиотеке.\n\n"
        "🤖 <b>Открытие файла книги на Android</b>\n\n"
        "1️⃣ Скачай любое приложение для чтения ePub-файлов из Google Play (например, ReadEra или FBReader).\n"
        "2️⃣ Открой файл книги в этом приложении.\n"
        "3️⃣ Готово ✅ — книга в твоей библиотеке.",
        reply_markup=back_to_books_menu,
    )
    await callback.answer()


# === Кнопка "Сон" ===
@dp.callback_query(F.data == "sleep")
async def sleep_handler(callback: types.CallbackQuery):
    await delete_message(callback)
    await callback.message.answer(
        "В разработке👨🏼‍💻 ...",
        reply_markup=back_to_main_menu,
    )
    await callback.answer()


# === Кнопка "Полезные материалы" ===
@dp.callback_query(F.data == "materials")
async def materials_handler(callback: types.CallbackQuery):
    await delete_message(callback)
    await callback.message.answer(
        "🧩 Здесь ты найдёшь лучшие материалы для саморазвития: книги, чек-листы, подборки, сервисы и многое другое!",
        reply_markup=books_menu,
    )
    await callback.answer()


import random
from motivation_quotes import motivation_quotes

# === Кнопка "Мотивация" ===
from motivation_back_button import motivation_back_button
@dp.callback_query(F.data == "motivation")
async def motivation_handler(callback: types.CallbackQuery):
    await delete_message(callback)
    quote = random.choice(motivation_quotes)
    msg = await callback.message.answer(quote, reply_markup=motivation_back_button)
    await callback.answer()

# === Кнопка "Обо мне" ===
@dp.callback_query(F.data == "about")
async def about_handler(callback: types.CallbackQuery):
    await delete_message(callback)
    await callback.message.answer(
        "🔥 Привет! Я — Закари, спортсмен и студент Волгоградского политехнического университета, родом из солнечной Махачкалы, что в Дагестане. Моя жизнь — это постоянный рост, движение вперёд и стремление становиться лучше каждый день.\n\n"
        "🏀 Баскетбол и лёгкая атлетика — мои главные страсти. Они учат меня дисциплине, упорству и вере в свои силы. Спорт — не просто хобби, а часть моего характера. Он заряжает энергией и помогает добиваться целей не только на площадке, но и в жизни.\n\n"
        "💻 Сейчас я активно вхожу в мир программирования и монтажа — изучаю новое и прокачиваю навыки. Пока не профи, но точно знаю: с упорством и временем смогу создавать крутые проекты и делать технологии доступнее для всех.\n\n"
        "📈 Саморазвитие — мой путь. Каждый день я ставлю перед собой задачи, которые помогают стать сильнее, умнее, увереннее. Это не просто красивые слова — это мой стиль жизни.\n\n"
        "🤖 Этот бот — результат моего труда и желания делиться с тобой полезным контентом. Здесь ты найдёшь всё, что поможет развиваться, учиться и вдохновляться прямо сейчас. Я собрал внутри всё, что реально работает и помогает мне самому.\n\n"
        "📬 Есть идея, отзыв или просто хочешь сказать “спасибо”? Напиши мне в Telegram: @colibry_05\n"
        "📸 Или загляни в мой Инстаграмм \"Zcolibry\" — там я делюсь процессом, спортом и собой настоящим.\n\n"
        "Спасибо, что здесь. Погнали дальше! 🚀",
        reply_markup=back_to_main_menu,
    )
    await callback.answer()

# === Кнопка "Мой путь" ===
@dp.callback_query(F.data == "my_way")
async def my_way_handler(callback: types.CallbackQuery):
    await delete_message(callback)
    await callback.message.answer(
        "⏳ Ещё год назад я был как большинство: режим сна в руинах, спорт нестабильный, книги — одна за два месяца, в голове — шум, хаос, отговорки. Но в какой-то момент, примерно 4–5 месяцев назад, что-то внутри щёлкнуло. Я устал быть как все. Устал откладывать, уставать без причины, жить на автопилоте.\n\n"
        "🧠 Я начал менять всё: режим, привычки, питание, мышление. И это оказалось самым трудным — не прокачать тело, а пересобрать самого себя. Стать человеком, который делает, а не мечтает. Честным перед собой. Строгим — но с уважением к себе настоящему.\n\n"
        "📚 Сегодня всё иначе. Я читаю две-три книги в месяц (раньше — одну за два), веду трекер жизни, в котором каждый день отслеживаю ключевые сферы:  \n💤 сон, 🏃‍♂️ спорт, ⚡️ энергия, ⏱️ дисциплина, 🎯 фокус, 💬 уверенность.\n\n"
        "🥗 Я наладил питание, выстроил режим сна. Сейчас, если я не выполняю то, что запланировал — мне реально не по себе. Потому что боль дисциплины — ничто по сравнению с болью сожалений.\n\n"
        "🏃‍♂️ Без какой-либо подготовки я вошёл в лёгкую атлетику. В конце мая 2025 года я пробежал свой первый полумарафон — 21 км — за 1:43:18 (4:57/км). Это был момент, когда я увидел, как далеко можно зайти за короткое время, если действовать по-настоящему.\n\n"
        "💻 Параллельно учусь монтажу и программированию. Уже собрал этого бота с нуля. Сейчас я — новичок, но к концу года хочу выйти на уровень мидла и делать реально полезные проекты.\n\n"
        "🎯 Моя цель на 2025 год:\n– 🏃‍♂️ Пробежать марафон (42 км) за &lt; 5 часов  \n– 📚 Прочитать 25 книг (уже прочитано 12)  \n– 💪 Стать спортивнее и дисциплинированнее  \n– 👨‍💻 Прокачать навыки до уровня мидл  \n– 💬 Быть примером не словами, а делами\n\n"
        "🚀 Мой путь — не идеальный. Но он настоящий. И он только начинается.\n\n"
        "Если ты читаешь это — знай: начать можно в любой момент. Просто с малого. А я рядом — через этот бот, через свои слова и действия.",
        reply_markup=back_to_main_menu,
    )
    await callback.answer()

# === Кнопка "Сон и энергия" ===
from sleep_energy import sleep_energy_menu, energy_materials_back, sleep_calc_start_menu, sleep_result_back
from energy_back_button import energy_back_button
from sleep_calculator_state import SleepCalcState
from aiogram.fsm.context import FSMContext
@dp.callback_query(F.data == "sleep_energy")
async def sleep_energy_handler(callback: types.CallbackQuery):
    await delete_message(callback)
    await callback.message.answer(
        "🛌Сон и энергия: выбери интересующий раздел.",
        reply_markup=sleep_energy_menu,
    )
    await callback.answer()

# --- Мой сон: режим и выводы ---
@dp.callback_query(F.data == "my_sleep")
async def my_sleep_handler(callback: types.CallbackQuery):
    await delete_message(callback)
    await callback.message.answer(
        "😴 Раньше я относился ко сну как к чему-то необязательному. Засыпал под утро, спал по 4–5 часов, думая: «главное — больше работать, а сон — как получится». Но в какой-то момент начал замечать: всё вроде делаю, стараюсь, а энергии нет, фокус теряется, настроение скачет. Ощущение, будто топчусь на месте.\n\n"
        "🔁 Тогда я впервые задумался: а может, причина не в мотивации, не в дисциплине… а просто в недосыпе? С этого и начался мой путь к осознанному подходу ко сну.\n\n"
        "📓 Я начал вести дневник сна, изучать материалы, пробовать разные режимы и внимательно следить за реакцией тела и мозга. С опытом выстроил тот самый режим, который реально подходит мне.\n\n"
        "⏰ Сейчас я сплю 7,5–9 часов ночью + иногда днём 30–40 минут, если чувствую потребность. Ложусь примерно в 23:00, встаю около 7:00–8:00. Режим полностью устраивает: голова работает ясно, настроение стабильное, энергии хватает, а в теле — лёгкость.\n\n"
        "🧠 За это время я понял главное:\nсон — это не враг продуктивности, а её основа.\nОн влияет вообще на всё: на концентрацию, уверенность, здоровье, внешний вид и даже на харизму. Если не спишь — всё остальное рассыпается.\n\n"
        "📂 Поэтому я решил делиться всем, что узнал и применил сам. В этом разделе ты найдёшь:\n ✅ Мои наработки и выводы о сне,\n ✅ Файлы с полезными материалами,\n ✅ Лайфхаки, чек-листы,\n ✅ Мой новый калькулятор сна — интерактивный инструмент, который уже доступен прямо здесь! Он поможет тебе легко подобрать идеальное время для засыпания и пробуждения, чтобы просыпаться бодрым и полным энергии. Попробуй прямо сейчас — это реально удобно и работает!\n\n"
        "📌 Сон — это не просто фоновая вещь в жизни. Это основа. И если ты начнёшь с него — всё остальное станет в разы легче. Я это понял на своём опыте. И теперь делюсь этим с тобой.",
        reply_markup=energy_back_button,
    )
    await callback.answer()

# --- Кнопка Калькулятор сна ---
@dp.callback_query(F.data == "sleep_calc")
async def sleep_calc_intro(callback: types.CallbackQuery, state: FSMContext):
    await delete_message(callback)
    await callback.message.answer(
        "Этот инструмент поможет тебе подобрать оптимальное время пробуждения, чтобы проснуться максимально бодрым и свежим.\n\n"
        "Важно: для качественного сна имеет значение не только его продолжительность, но и то, чтобы просыпаться в конце полного цикла сна.\n\n"
        "Обрати внимание: Эта функция — лишь ориентир и не заменяет индивидуальный подход.\nЭтот калькулятор не гарантирует 100% бодрость — всё зависит от качества сна, твоего эмоционального состояния, питания, физической активности и даже свежести воздуха в комнате.\n\n"
        "Нажми Приступить к расчету 🧮, чтобы начать, или Назад, чтобы вернуться.",
        reply_markup=sleep_calc_start_menu,
    )
    await callback.answer()

@dp.callback_query(F.data == "start_calc")
async def sleep_calc_start(callback: types.CallbackQuery, state: FSMContext):
    await delete_message(callback)
    await state.set_state(SleepCalcState.waiting_for_fall_asleep)
    msg = await callback.message.answer(
        "Сколько минут у тебя обычно уходит на засыпание? (Например: 15)",
        reply_markup=sleep_result_back,
    )
    await state.update_data(last_bot_msg_id=msg.message_id)
    await callback.answer()

@dp.message(SleepCalcState.waiting_for_fall_asleep)
async def process_fall_asleep(message: types.Message, state: FSMContext):
    try:
        fall_asleep = int(message.text.strip())
        if fall_asleep < 0 or fall_asleep > 120:
            raise ValueError
    except Exception:
        await message.delete()
        await message.answer("Пожалуйста, введи число минут (например: 15)")
        return
    await state.update_data(fall_asleep=fall_asleep)
    # Удаляем предыдущий вопрос (если был сохранён)
    data = await state.get_data()
    prev_bot_msg_id = data.get('last_bot_msg_id')
    if prev_bot_msg_id:
        try:
            await message.bot.delete_message(message.chat.id, prev_bot_msg_id)
        except Exception:
            pass
    await message.delete()
    msg = await message.answer("Во сколько ты планируешь лечь сегодня? (Формат: 23:15)", reply_markup=sleep_result_back)
    await state.update_data(last_bot_msg_id=msg.message_id)
    await state.set_state(SleepCalcState.waiting_for_bedtime)

@dp.message(SleepCalcState.waiting_for_bedtime)
async def process_bedtime(message: types.Message, state: FSMContext):
    import re, datetime
    time_pattern = r"^(\d{1,2}):(\d{2})$"
    match = re.match(time_pattern, message.text.strip())
    if not match:
        # Удаляем предыдущий вопрос (если был сохранён)
        data = await state.get_data()
        prev_bot_msg_id = data.get('last_bot_msg_id')
        if prev_bot_msg_id:
            try:
                await message.bot.delete_message(message.chat.id, prev_bot_msg_id)
            except Exception:
                pass
        await message.delete()
        msg = await message.answer("Пожалуйста, введи время в формате ЧЧ:ММ (например: 23:15)")
        await state.update_data(last_bot_msg_id=msg.message_id)
        return
    hour, minute = map(int, match.groups())
    if not (0 <= hour < 24 and 0 <= minute < 60):
        await message.delete()
        await message.answer("Пожалуйста, введи корректное время (например: 23:15)")
        return
    data = await state.get_data()
    fall_asleep = data.get("fall_asleep", 15)
    bedtime = datetime.datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
    # Если время уже прошло сегодня, переносим на завтра
    if bedtime < datetime.datetime.now():
        bedtime += datetime.timedelta(days=1)
    # Показываем только 4, 5 и 6 циклов сна
    cycles = [4, 5, 6]
    results = []
    for c in cycles:
        wake_time = bedtime + datetime.timedelta(minutes=fall_asleep + int(c*90))  # 1 цикл = 90 мин
        results.append(f"{c} цикла: {wake_time.strftime('%H:%M')}")
    await message.delete()
    result_text = "\n".join(results)
    note = ("\n\n⚡️ Это лишь ориентир!\n"
            "Время пробуждения рассчитано исходя из классической длины цикла сна — 90 минут.\n"
            "На качество сна влияют стресс, питание, физическая активность, освещение, температура, свежесть воздуха и даже твои мысли перед сном.\n"
            "Пользуйся калькулятором как подсказкой, но не полагайся на него на 100%. Слушай свой организм! 💤")
    # Удаляем предыдущий вопрос (если был сохранён)
    data = await state.get_data()
    prev_bot_msg_id = data.get('last_bot_msg_id')
    if prev_bot_msg_id:
        try:
            await message.bot.delete_message(message.chat.id, prev_bot_msg_id)
        except Exception:
            pass
    await message.answer(f"Вот когда лучше проснуться после 4, 5 или 6 полных циклов сна:\n{result_text}{note}", reply_markup=sleep_result_back)
    await state.clear()

@dp.callback_query(F.data == "back_to_energy")
async def back_to_energy_handler(callback: types.CallbackQuery, state: FSMContext):
    await delete_message(callback)
    await state.clear()
    await callback.message.answer(
        "🛌Сон и энергия: выбери интересующий раздел.",
        reply_markup=sleep_energy_menu,
    )
    await callback.answer()

# --- Кнопка Полезные материалы (энергия) ---
@dp.callback_query(F.data == "energy_materials")
async def energy_materials_handler(callback: types.CallbackQuery):
    await delete_message(callback)
    await callback.message.answer(
        "✨ Совсем скоро здесь ты найдёшь лучшие подборки, советы и материалы по сну и энергии, которые реально работают! Постоянно обновляю и добавляю новое — возвращайся за свежими инсайтами и практическими фишками!",
        reply_markup=energy_materials_back,
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
        "🧩 Здесь ты найдёшь лучшие материалы для саморазвития: книги, чек-листы, подборки, сервисы и многое другое!", reply_markup=books_menu
    )
    await callback.answer()


# === Запуск бота ===
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

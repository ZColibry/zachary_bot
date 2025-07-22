from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

motivation_back_button = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Назад ⏪", callback_data="back_main")]
    ]
)

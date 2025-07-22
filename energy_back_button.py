from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

energy_back_button = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Назад ⏪", callback_data="back_to_energy")]
    ]
)

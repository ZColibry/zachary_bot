from telethon import TelegramClient
from telethon.errors import UserNotParticipantError
from telethon.tl.functions.channels import GetParticipantRequest
import asyncio
from dotenv import load_dotenv
import os

load_dotenv()

api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
channel_username = os.getenv("CHANNEL_USERNAME").lstrip("@")  # Для Telethon лучше без @

client = TelegramClient('checker_session', api_id, api_hash)

async def check_subscription(user_id: int) -> bool:
    await client.start()
    try:
        await client(GetParticipantRequest(
            channel=channel_username,
            participant=user_id
        ))
        return True
    except UserNotParticipantError:
        return False
    except Exception as e:
        print(f"Ошибка проверки: {e}")
        return False

if __name__ == "__main__":
    uid = int(input("Введите Telegram user_id: "))
    result = asyncio.run(check_subscription(uid))
    print("✅ Подписан" if result else "❌ Не подписан")
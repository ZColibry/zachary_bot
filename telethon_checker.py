from telethon import TelegramClient
from telethon.errors import UserNotParticipantError
from telethon.tl.functions.channels import GetParticipantRequest
import asyncio

api_id = 12627945
api_hash = "4b283be95442ece4c10bd35199ee010a"
channel_username = "zcolibry"

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
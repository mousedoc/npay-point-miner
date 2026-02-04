import asyncio
import os
from telegram import Bot


class TelegramUtil:

    # Telegram setting - 대략적인 형태: 7775956927:AAFxXlFYooWpUmTg9Ljhx9w-u8RAFDvv4OM
    __TELEGRAM_TOKEN = '1234'

    # Telegram Chat Id: 대략적인 형태: -1003089689843
    __CHAT_ID = '5678'

    # 업데이트 테스트 url
    # https://api.telegram.org/bot7775956927:AAFxXlFYooWpUmTg9Ljhx9w-u8RAFDvv4OM/getUpdates

    @classmethod
    def send_message(cls, message):
        try:
            bot = Bot(token=cls.__TELEGRAM_TOKEN)
            async def send():
                await bot.send_message(chat_id=cls.__CHAT_ID, text=message)
            asyncio.run(send())
            print("📦 메시지 전송 완료")
        except Exception as e:
            print("❌ 메시지 전송 실패:", e)

    @classmethod
    def send_file(cls, file_path, caption=None):
        try:
            bot = Bot(token=cls.__TELEGRAM_TOKEN)
            async def send():
                with open(file_path, 'rb') as f:
                    await bot.send_document(chat_id=cls.__CHAT_ID, document=f, caption=caption)
            asyncio.run(send())
            print("📦 파일 전송 완료")
        except Exception as e:
            print("❌ 파일 전송 실패:", e)
        

if __name__ == "__main__":
    # test message 
    TelegramUtil.send_message('이 메세지는 테스트 메세지 입니다')   

    # test file
    file_path = os.path.join(os.path.dirname(__file__), 'test_file.zip')
    TelegramUtil.send_file(file_path, caption="🧾 이건 테스트 파일입니다")
import asyncio
import os
from telegram import Bot


class TelegramUtil:
    # 💡 환경 변수에서 가져오되, 없으면 None으로 설정
    _telegram_token = os.environ.get('TELEGRAM_TOKEN')
    _chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    @classmethod
    def send_message(cls, message):
        # 💡 토큰이나 ID가 없으면 실행하지 않음
        if not cls._telegram_token or not cls._chat_id:
            print("⚠️ Telegram credentials are missing. Skipping message.")
            return

        try:
            bot = Bot(token=cls._telegram_token)
            async def send():
                await bot.send_message(chat_id=cls._chat_id, text=message)
            asyncio.run(send())
            print("📦 메시지 전송 완료")
        except Exception as e:
            print("❌ 메시지 전송 실패:", e)

    @classmethod
    def send_file(cls, file_path, caption=None):
        # 💡 토큰이나 ID가 없으면 실행하지 않음
        if not cls._telegram_token or not cls._chat_id:
            print("⚠️ Telegram credentials are missing. Skipping file upload.")
            return

        try:
            bot = Bot(token=cls._telegram_token)
            async def send():
                with open(file_path, 'rb') as f:
                    await bot.send_document(chat_id=cls._chat_id, document=f, caption=caption)
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
import requests

class TelegramNotifier:
    """ส่งแจ้งเตือนไปยัง Telegram"""
    
    @staticmethod
    def send_message(bot_token: str, chat_id: str, message: str):
        """ส่งข้อความไปยัง Telegram"""
        if not bot_token or not chat_id:
            return
        
        try:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
            requests.post(url, data=data, timeout=5)
        except Exception as e:
            print(f"Failed to send Telegram notification: {e}")

    @staticmethod
    def send_file(bot_token: str, chat_id: str, file_path: str, caption: str = ""):
        """
        ส่งไฟล์ (document) ไปยัง Telegram bot
        """
        try:
            url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
            with open(file_path, 'rb') as f:
                files = {'document': f}
                data = {'chat_id': chat_id, 'caption': caption}
                resp = requests.post(url, data=data, files=files, timeout=20)
                return resp.ok
        except Exception:
            return False
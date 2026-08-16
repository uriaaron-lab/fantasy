import os
import requests

def send_discord_message(message):
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("Webhook URL is missing!")
        return

    data = {
        "content": "עדכון פאנטזי פוטבול חדש!",
        "embeds": [
            {
                "title": "בוט פאנטזי 2026-27",
                "description": message,
                "color": 3447003
            }
        ]
    }
    
    response = requests.post(webhook_url, json=data)
    if response.status_code == 204:
        print("Message sent successfully")
    else:
        print(f"Failed to send message: {response.status_code}")

def get_sleeper_data():
    # כאן תמוקם הלוגיקה שתמשוך נתונים מ-Sleeper בקשות הבאות
    
    # לצורך הבדיקה הראשונית נשלח הודעת טסט פשוטה:
    fantasy_insight = "הבוט הוגדר בהצלחה! התשתית עובדת. כעת ניתן להוסיף את מזהה הליגה שלך."
    send_discord_message(fantasy_insight)

if __name__ == "__main__":
    get_sleeper_data()

import os
import requests

# הכנס את שם המשתמש שלך ב-Sleeper ממש כאן (בתוך המרכאות במקום המילה your_username):
SLEEPER_USERNAME = "uria87"

def send_discord_message(message):
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("Webhook URL is missing!")
        return

    data = {
        "content": "עדכון מערכת פאנטזי - Sleeper",
        "embeds": [
            {
                "title": f"נתונים עבור: {SLEEPER_USERNAME}",
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
    # 1. משיכת מזהה המשתמש לפי שם המשתמש
    user_url = f"https://api.sleeper.app/v1/user/{SLEEPER_USERNAME}"
    user_response = requests.get(user_url)
    
    if user_response.status_code != 200:
        send_discord_message("שגיאה: לא הצלחתי למצוא את המשתמש ב-Sleeper. ודא ששם המשתמש מדויק.")
        return
        
    user_data = user_response.json()
    user_id = user_data.get("user_id")
    
    # 2. משיכת הליגות של המשתמש לעונת 2026
    leagues_url = f"https://api.sleeper.app/v1/user/{user_id}/leagues/nfl/2026"
    leagues_response = requests.get(leagues_url)
    
    if leagues_response.status_code == 200:
        leagues = leagues_response.json()
        if not leagues:
            send_discord_message("לא נמצאו ליגות פעילות לעונת 2026 ב-Sleeper.")
            return
            
        # יצירת הודעה עם שמות הליגות
        leagues_text = "הבוט התחבר בהצלחה לנתונים! הנה הליגות שלך לעונת 2026:\n\n"
        for league in leagues:
            league_name = league.get("name")
            league_id = league.get("league_id")
            leagues_text += f"🏆 **{league_name}** (מזהה ליגה: {league_id})\n"
            
        send_discord_message(leagues_text)
    else:
        send_discord_message("שגיאה במשיכת נתוני הליגות.")

if __name__ == "__main__":
    get_sleeper_data()

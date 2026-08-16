import os
import json
import requests
import google.generativeai as genai

SLEEPER_USERNAME = "uria87" # הכנס את שם המשתמש שלך כאן
MEMORY_FILE = "bot_memory.json"

def send_discord_message(message):
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        return

    # חיתוך ההודעה במקרה שהיא ארוכה מדי לדיסקורד (מגבלת 4096 תווים ל-Embed)
    description = message[:4090] + "..." if len(message) > 4096 else message

    data = {
        "content": "🧠 **עדכון מסוכן ה-AI שלך:**",
        "embeds": [
            {
                "title": f"ניתוח פאנטזי אסטרטגי - עונת 2026",
                "description": description,
                "color": 3447003
            }
        ]
    }
    requests.post(webhook_url, json=data)

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"past_lessons": "זהו השבוע הראשון, אין עדיין תובנות עבר.", "previous_recommendations": []}

def save_memory(new_memory_data):
    with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(new_memory_data, f, ensure_ascii=False, indent=4)

def analyze_with_ai(league_data, memory_data):
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    
    # שימוש במודל המתקדם והעדכני של ג'מיני 
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""
    אתה מומחה פאנטזי פוטבול (NFL) ברמה עולמית, ואתה מנהל עבורי את הקבוצה לעונת 2026.
    
    נתוני הליגה והסגלים מהפלטפורמה (Sleeper):
    {json.dumps(league_data, ensure_ascii=False)}
    
    זיכרון ותובנות משבועות קודמים שכתבת לעצמך (כדי שתלמד מטעויות והצלחות):
    {json.dumps(memory_data, ensure_ascii=False)}
    
    המשימה שלך:
    נתח את הנתונים לעומק. אני רוצה שתיצור דוח שמכיל את החלקים הבאים:
    1. תמונת מצב של הקבוצה שלי: מאצ'-אפים קרובים ונקודות חולשה.
    2. המלצות שוק פנויים (Waiver Wire): מי חם עכשיו ושווה להרים.
    3. אסטרטגיית טריידים: זהה קבוצות אחרות בליגה שיש להן חולשות ספציפיות, והצע לי טרייד ספציפי (תן שחקן X, קבל שחקן Y) שיהיה הוגן ויאושר על ידם, אבל ייתן לי יתרון.
    4. עדכון זיכרון: בסוף התשובה שלך, כתוב פסקה אחת תחת הכותרת "UPDATE_MEMORY" ובה תסכם מה לזכור לשבוע הבא (למשל: איזה טרייד הצענו, על איזה שחקן אנחנו עוקבים, איזה אסטרטגיה עבדה). 
    
    ענה בעברית מקצועית, פשוטה וברורה. עשה שימוש באימוג'ים כדי להקל על הקריאה.
    """
    
    response = model.generate_content(prompt)
    return response.text

def get_sleeper_data():
    # משיכת מזהה המשתמש
    user_res = requests.get(f"https://api.sleeper.app/v1/user/{SLEEPER_USERNAME}")
    if user_res.status_code != 200:
        return None
    user_id = user_res.json().get("user_id")
    
    # משיכת הליגות
    leagues_res = requests.get(f"https://api.sleeper.app/v1/user/{user_id}/leagues/nfl/2026")
    if leagues_res.status_code != 200 or not leagues_res.json():
        return None
        
    league_id = leagues_res.json()[0].get("league_id")
    
    # משיכת נתוני רוסטרים של כל הליגה (כדי למצוא הזדמנויות לטריידים)
    rosters_res = requests.get(f"https://api.sleeper.app/v1/league/{league_id}/rosters")
    
    # משיכת שחקנים טרנדיים (לחיפוש בוויבר ווייר)
    trending_res = requests.get("https://api.sleeper.app/v1/players/nfl/trending/add?lookback_hours=24&limit=5")
    
    return {
        "user_id": user_id,
        "league_id": league_id,
        "rosters": rosters_res.json() if rosters_res.status_code == 200 else {},
        "trending_adds": trending_res.json() if trending_res.status_code == 200 else {}
    }

if __name__ == "__main__":
    print("Fetching Sleeper data...")
    league_data = get_sleeper_data()
    
    if not league_data:
        print("Failed to get league data.")
        exit(1)
        
    print("Loading memory...")
    memory = load_memory()
    
    print("Analyzing with Gemini AI...")
    ai_response = analyze_with_ai(league_data, memory)
    
    # הפרדת ההמלצות מתוך הטקסט של עדכון הזיכרון
    parts = ai_response.split("UPDATE_MEMORY")
    discord_message = parts[0].strip()
    
    new_memory_text = parts[1].strip() if len(parts) > 1 else "לא נוסף זיכרון חדש."
    
    # עדכון ושמירת הזיכרון
    new_memory = {
        "past_lessons": new_memory_text
    }
    save_memory(new_memory)
    
    print("Sending to Discord...")
    send_discord_message(discord_message)
    print("Done!")

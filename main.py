import os
import json
import requests

# הגדרות כלליות
SLEEPER_USERNAME = "uria87"
LEAGUE_INDEX = 0  
MEMORY_FILE = f"bot_memory_league_{LEAGUE_INDEX}.json"

def send_discord_message(message):
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        return

    description = message[:4090] + "..." if len(message) > 4096 else message

    data = {
        "content": "🧠 **עדכון סוכן ה-AI החכם לפאנטזי:**",
        "embeds": [
            {
                "title": f"ניתוח אסטרטגי מתקדם - ליגה {LEAGUE_INDEX + 1}",
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
    return {"past_lessons": "זהו השבוע הראשון, אין עדיין תובנות עבר או הפקת לקחים קודמת.", "previous_recommendations": []}

def save_memory(new_memory_data):
    with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(new_memory_data, f, ensure_ascii=False, indent=4)

def analyze_with_ai(league_data, memory_data):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is missing!")
        
    prompt = f"""
    אתה מנהל קבוצת פאנטזי פוטבול (NFL) אסטרטגי, חכם ואנליטי ברמה העולמית. המטרה שלך היא לא רק לתת המלצות שטחיות, אלא להשתפר וללמוד לבד מפעם לפעם.
    
    נתוני הליגה, הסגלים, והטרנדים מהפלטפורמה (Sleeper):
    {json.dumps(league_data, ensure_ascii=False)}
    
    הזיכרון ההיסטורי והתובנות שהפקת בשבועות קודמים (למידה עצמית ושיפור מתמשך):
    {json.dumps(memory_data, ensure_ascii=False)}
    
    הנחיות חובה לניתוח שלך:
    1. אסטרטגיה לפי לו"ז (Schedules): אל תסתכל רק על השחקן עצמו אלא גם על הלו"ז שלו ושל הקבוצה שלי (Bye Weeks, משחקים קשים מול הגנות חזקות בשלבי ההכרעה, וכד'). תמליץ על הרמות (Waiver Wire) או טריידים תוך התחשבות בלו"ז העתידי לטווח קצר וארוך.
    2. איזון עמדות ובניית סגל: תדאג שתמיד תהיה לי קבוצה מאוזנת (גיבויים נכונים לפציעות, עומק לעונה ארוכה). בהתחשב במבנה הדראפט ובמיקומי הבחירה, תנתח מי שחקנים עשויים להישאר לבחירה הבאה ותכנן את האסטרטגיה בהתאם.
    3. סינון רלוונטיות מידע: תתייחס אך ורק לנתונים ולחדשות עדכניות שרלוונטיות למצבים קורים כעת בשטח (פציעות אמיתיות, מעמדים של שחקנים בקבוצות אמיתיות השבוע), ותתעלם מרעשי רקע לא רלוונטיים.
    4. עדכון זיכרון עצמי (UPDATE_MEMORY): בסוף התשובה שלך, כתוב פסקה מדויקת תחת הכותרת "UPDATE_MEMORY" שבה אתה מסכם מה למדת מהשבוע הנוכחי, אילו החלטות הצליחו ואילו טעויות צריך לתקן לשבוע הבא כדי שהסוכן יהיה חכם יותר בפעם הבאה.
    
    ענה בעברית מקצועית, פשוטה, ממוקדת, עם אימוג'ים מתאימים.
    """
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "אתה מומחה פאנטזי פוטבול אנליטי."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }
    
    try:
        print("Sending request to Groq API...")
        response = requests.post(url, headers=headers, json=payload)
        print(f"Groq API Response Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Groq API Error Body: {response.text}")
            raise Exception(f"Groq API failed with status {response.status_code}: {response.text}")
            
        res_data = response.json()
        text = res_data["choices"][0]["message"]["content"]
        return text
    except Exception as e:
        print(f"CRITICAL ERROR - שגיאה בתקשורת מול Groq API: {str(e)}")
        raise e

def get_sleeper_data():
    print(f"Fetching Sleeper user: {SLEEPER_USERNAME}...")
    user_res = requests.get(f"https://api.sleeper.app/v1/user/{SLEEPER_USERNAME}")
    print(f"User API status code: {user_res.status_code}")
    
    if user_res.status_code != 200:
        print(f"Failed to fetch user from Sleeper. Response: {user_res.text}")
        return None
        
    user_data = user_res.json()
    if not user_data or "user_id" not in user_data:
        print(f"User data is invalid: {user_data}")
        return None
        
    user_id = user_data.get("user_id")
    print(f"Found User ID: {user_id}")
    
    leagues = []
    for year in ["2026", "2025"]:
        print(f"Trying to fetch leagues for year {year}...")
        leagues_res = requests.get(f"https://api.sleeper.app/v1/user/{user_id}/leagues/nfl/{year}")
        print(f"Leagues {year} status code: {leagues_res.status_code}")
        if leagues_res.status_code == 200:
            data = leagues_res.json()
            if data:
                leagues = data
                print(f"Successfully found {len(leagues)} leagues for {year}.")
                break
    
    if not leagues:
        print("No leagues found for 2026 or 2025 in Sleeper API.")
        return None
        
    if len(leagues) <= LEAGUE_INDEX:
        league_id = leagues[0].get("league_id")
    else:
        league_id = leagues[LEAGUE_INDEX].get("league_id")
        
    print(f"Using League ID: {league_id}")
    
    rosters_res = requests.get(f"https://api.sleeper.app/v1/league/{league_id}/rosters")
    trending_res = requests.get("https://api.sleeper.app/v1/players/nfl/trending/add?lookback_hours=24&limit=5")
    
    return {
        "user_id": user_id,
        "league_id": league_id,
        "rosters": rosters_res.json() if rosters_res.status_code == 200 else {},
        "trending_adds": trending_res.json() if trending_res.status_code == 200 else {}
    }

if __name__ == "__main__":
    print(f"Starting bot for League Index {LEAGUE_INDEX}...")
    league_data = get_sleeper_data()
    
    if not league_data:
        print("CRITICAL: Failed to get league data from Sleeper API.")
        exit(1)
        
    print("Loading memory...")
    memory = load_memory()
    
    print("Analyzing with Groq AI...")
    ai_response = analyze_with_ai(league_data, memory)
    
    parts = ai_response.split("UPDATE_MEMORY")
    discord_message = parts[0].strip()
    new_memory_text = parts[1].strip() if len(parts) > 1 else "לא נוסף זיכרון חדש."
    
    new_memory = {
        "past_lessons": new_memory_text
    }
    save_memory(new_memory)
    
    print("Sending to Discord...")
    send_discord_message(discord_message)
    print("Done!")

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
    אתה מנהל קבוצת פאנטזי פוטבול (NFL) אסטרטגי, חכם ואנליטי ברמה העולמית.
    
    נתוני הליגה והסגלים מ-Sleeper:
    {json.dumps(league_data, ensure_ascii=False)}
    
    זיכרון ותובנות משבועות קודמים:
    {json.dumps(memory_data, ensure_ascii=False)}
    
    המשימה שלך: נתח את הנתונים, תן המלצות Waiver Wire, אסטרטגיית טריידים ולו"ז, וכתוב בסוף פסקה תחת הכותרת "UPDATE_MEMORY" עם מה שצריך לזכור לשבוע הבא. ענה בעברית עם אימוג'ים.
    """
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }
    
    print("Sending request to Groq API...")
    response = requests.post(url, headers=headers, json=payload)
    print(f"Groq API Response Status: {response.status_code}")
    
    # אם יש שגיאה, נדפיס אותה במדויק כדי שנוכל לראות מה הבעיה בלי לנחש
    if response.status_code != 200:
        print(f"GROQ ERROR DETAILS: {response.text}")
        raise Exception(f"Groq API failed with status {response.status_code}")
        
    res_data = response.json()
    return res_data["choices"][0]["message"]["content"]

def get_sleeper_data():
    print(f"Fetching Sleeper user: {SLEEPER_USERNAME}...")
    user_res = requests.get(f"https://api.sleeper.app/v1/user/{SLEEPER_USERNAME}")
    if user_res.status_code != 200:
        print(f"Failed to fetch user: {user_res.text}")
        return None
        
    user_data = user_res.json()
    user_id = user_data.get("user_id")
    
    leagues_res = requests.get(f"https://api.sleeper.app/v1/user/{user_id}/leagues/nfl/2026")
    leagues = leagues_res.json() if leagues_res.status_code == 200 else []
    
    if not leagues:
        leagues_res = requests.get(f"https://api.sleeper.app/v1/user/{user_id}/leagues/nfl/2025")
        leagues = leagues_res.json() if leagues_res.status_code == 200 else []

    if not leagues:
        print("No leagues found.")
        return None
        
    league_id = leagues[LEAGUE_INDEX].get("league_id") if len(leagues) > LEAGUE_INDEX else leagues[0].get("league_id")
    
    rosters_res = requests.get(f"https://api.sleeper.app/v1/league/{league_id}/rosters")
    trending_res = requests.get("https://api.sleeper.app/v1/players/nfl/trending/add?lookback_hours=24&limit=5")
    
    return {
        "user_id": user_id,
        "league_id": league_id,
        "rosters": rosters_res.json() if rosters_res.status_code == 200 else {},
        "trending_adds": trending_res.json() if trending_res.status_code == 200 else {}
    }

if __name__ == "__main__":
    print("Starting bot...")
    league_data = get_sleeper_data()
    
    if not league_data:
        print("CRITICAL: Failed to get league data.")
        exit(1)
        
    memory = load_memory()
    ai_response = analyze_with_ai(league_data, memory)
    
    parts = ai_response.split("UPDATE_MEMORY")
    discord_message = parts[0].strip()
    new_memory_text = parts[1].strip() if len(parts) > 1 else "לא נוסף זיכרון חדש."
    
    save_memory({"past_lessons": new_memory_text})
    send_discord_message(discord_message)
    print("Done!")

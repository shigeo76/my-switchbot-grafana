import time, hashlib, hmac, base64, requests, os

# 1. 認証情報の読み込み
sb_token = os.environ['SB_TOKEN']
sb_secret = os.environ['SB_SECRET']
supabase_url = os.environ['SUPABASE_URL']
supabase_key = os.environ['SUPABASE_KEY']

# 2. 確定した正しいIDをセット
target_devices = [
    ("C6A83697434C", "kaidanshitsu"), # 会談室
    ("DE2A338AE1E6", "kitchen"),      # キッチン
    ("E876C6462F2B", "Outside")       # 屋外
]

def get_sb_headers():
    t = str(int(time.time() * 1000))
    nonce = "anything"
    sign = base64.b64encode(hmac.new(sb_secret.encode('utf-8'), f"{sb_token}{t}{nonce}".encode('utf-8'), hashlib.sha256).digest()).upper()
    return {"Authorization": sb_token, "sign": sign, "nonce": nonce, "t": t}

# --- メイン処理 ---
try:
    records = []
    sb_headers = get_sb_headers()

    for d_id, d_name in target_devices:
        print(f"Fetching: {d_name} ({d_id})...")
        res = requests.get(f"https://api.switch-bot.com/v1.1/devices/{d_id}/status", headers=sb_headers).json()
        
        body = res.get('body', {})
        if body:
            temp = body.get('temperature')
            hum = body.get('humidity')
            if temp is not None:
                records.append({
                    "device": d_name,
                    "temperature": temp,
                    "humidity": hum
                })

    # 3. Supabase REST APIへ一括送信
    if records:
        sp_headers = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }
        post_url = f"{supabase_url}/rest/v1/switchbot_metrics"
        r = requests.post(post_url, headers=sp_headers, json=records)
        print(f"Supabase Status: {r.status_code} (Success if 201)")
        if r.status_code != 201:
            print(f"Response: {r.text}")

except Exception as e:
    print(f"Error: {e}")

import time, hashlib, hmac, base64, requests, os

# 1. 認証情報の読み込み
sb_token = os.environ['SB_TOKEN']
sb_secret = os.environ['SB_SECRET']
g_user = os.environ['GRAFANA_USER']
g_token = os.environ['GRAFANA_TOKEN']
g_url = "https://influx-prod-49-prod-ap-northeast-0.grafana.net/api/v1/push/influx/write"

target_devices = [
    ("C6A83697434C", "kaidanshitsu"),
    ("CA9D747E5EE7", "kitchen")
]

def get_sb_headers():
    t = str(int(time.time() * 1000))
    nonce = "anything"
    sign = base64.b64encode(hmac.new(sb_secret.encode('utf-8'), f"{sb_token}{t}{nonce}".encode('utf-8'), hashlib.sha256).digest()).upper()
    return {"Authorization": sb_token, "sign": sign, "nonce": nonce, "t": t}

# --- メイン処理 ---
try:
    all_lines = []
    sb_headers = get_sb_headers()
    
    # 認証ヘッダーを先に作っておく
    auth_b64 = base64.b64encode(f"{g_user}:{g_token}".encode('ascii')).decode('ascii')
    g_headers = {"Authorization": f"Basic {auth_b64}", "Content-Type": "text/plain"}

    for d_id, d_name in target_devices:
        print(f"Fetching: {d_name} ({d_id})...")
        res = requests.get(f"https://api.switch-bot.com/v1.1/devices/{d_id}/status", headers=sb_headers).json()
        body = res.get('body', {})
        
        if body:
            temp = body.get('temperature')
            hum = body.get('humidity')
            if temp is not None:
                # 確実に1行分を作成
                line = f"switchbot,device={d_name} temperature={temp},humidity={hum}"
                all_lines.append(line)

    # 最後にまとめて送信
    if all_lines:
        payload = "\n".join(all_lines) + "\n"
        print("--- Payload ---")
        print(payload)
        
        g_res = requests.post(g_url, data=payload.encode('utf-8'), headers=g_headers)
        print(f"Grafana Push Status: {g_res.status_code}")

except Exception as e:
    print(f"Error: {e}")

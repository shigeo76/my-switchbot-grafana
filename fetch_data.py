import time, hashlib, hmac, base64, requests, os

# 1. 認証情報の読み込み
sb_token = os.environ['SB_TOKEN']
sb_secret = os.environ['SB_SECRET']
g_user = os.environ['GRAFANA_USER']
g_token = os.environ['GRAFANA_TOKEN']

# 正解のURL
g_url = "https://influx-prod-49-prod-ap-northeast-0.grafana.net/api/v1/push/influx/write"

# 2. SwitchBotからデータ取得
def get_metrics():
    t = str(int(time.time() * 1000))
    nonce = "anything"
    string_to_sign = f"{sb_token}{t}{nonce}"
    sign = base64.b64encode(hmac.new(sb_secret.encode('utf-8'), string_to_sign.encode('utf-8'), hashlib.sha256).digest()).upper()
    headers = {"Authorization": sb_token, "sign": sign, "nonce": nonce, "t": t}
    
    res = requests.get("https://api.switch-bot.com/v1.1/devices/C6A83697434C/status", headers=headers).json()
    return res['body']['temperature'], res['body']['humidity']

# 3. 実行
try:
    temp, hum = get_metrics()
    payload = f"switchbot,device=kaidanshitsu temperature={temp},humidity={hum}"
    
    # 認証ヘッダー作成
    auth_b64 = base64.b64encode(f"{g_user}:{g_token}".encode('ascii')).decode('ascii')
    g_headers = {
        "Authorization": f"Basic {auth_b64}",
        "Content-Type": "text/plain"
    }
    
    # 送信
    res = requests.post(g_url, data=payload, headers=g_headers)
    print(f"Status: {res.status_code} - Data: Temp={temp}, Hum={hum}")

except Exception as e:
    print(f"Error: {e}")

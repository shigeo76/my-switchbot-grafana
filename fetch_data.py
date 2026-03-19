import time, hashlib, hmac, base64, requests, os

# 認証情報の読み込み
sb_token = os.environ['SB_TOKEN']
sb_secret = os.environ['SB_SECRET']
g_user = os.environ['GRAFANA_USER']
g_token = os.environ['GRAFANA_TOKEN']

# SwitchBotからデータ取得
def get_data():
    t = str(int(time.time() * 1000))
    nonce = "anything"
    sign = base64.b64encode(hmac.new(sb_secret.encode('utf-8'), f"{sb_token}{t}{nonce}".encode('utf-8'), hashlib.sha256).digest()).upper()
    headers = {"Authorization": sb_token, "sign": sign, "nonce": nonce, "t": t}
    res = requests.get(f"https://api.switch-bot.com/v1.1/devices/C6A83697434C/status", headers=headers).json()
    return res['body']['temperature'], res['body']['humidity']

def get_auth_header():
    auth_b64 = base64.b64encode(f"{g_user}:{g_token}".encode('ascii')).decode('ascii')
    return f"Basic {auth_b64}"

# --- 総当たり送信リスト ---
# 1枚目の画像から推測されるベースURL
base_url = "https://influx-prod-49-prod-ap-northeast-0.grafana.net"

targets = [
    {"name": "パターン1: /api/v1/push (Text)",      "url": f"{base_url}/api/v1/push",        "ct": "text/plain"},
    {"name": "パターン2: /api/v1/push/influx (Text)", "url": f"{base_url}/api/v1/push/influx", "ct": "text/plain"},
    {"name": "パターン3: /api/v1/push (Protobuf)",   "url": f"{base_url}/api/v1/push",        "ct": "application/x-protobuf"},
    {"name": "パターン4: /influx/v1/push (Text)",     "url": f"{base_url}/influx/v1/push",     "ct": "text/plain"},
]

temp, hum = get_data()
payload = f"switchbot,device=kaidanshitsu temperature={temp},humidity={hum}"
auth = get_auth_header()

print(f"取得データ -> 温度: {temp}, 湿度: {hum}\n")

for target in targets:
    print(f"--- {target['name']} ---")
    headers = {
        "Authorization": auth,
        "Content-Type": target['ct'],
        "X-Prometheus-Remote-Write-Version": "0.1.0"
    }
    try:
        res = requests.post(target['url'], data=payload, headers=headers, timeout=10)
        print(f"URL: {target['url']}")
        print(f"Result: {res.status_code}")
        if res.status_code == 204:
            print("【★大当たり！★】この設定が正解です！")
        else:
            print(f"Body: {res.text}")
    except Exception as e:
        print(f"エラー: {e}")
    print("-" * 30)

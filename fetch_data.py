import time, hashlib, hmac, base64, requests, os

# 1. 認証情報読み込み (トークンなどはSecretsのままでOK)
sb_token = os.environ['SB_TOKEN']
sb_secret = os.environ['SB_SECRET']
g_user = os.environ['GRAFANA_USER']
g_token = os.environ['GRAFANA_TOKEN']

# 【ここが最重要】Secretsを使わず、正しいURLを直接書き込みます
g_url = "https://influx-prod-49-prod-ap-northeast-0.grafana.net/api/v1/push"

def get_headers():
    t = str(int(time.time() * 1000))
    nonce = "anything"
    data = sb_token + t + nonce
    sign = base64.b64encode(hmac.new(sb_secret.encode('utf-8'), data.encode('utf-8'), hashlib.sha256).digest()).upper()
    return {"Authorization": sb_token, "sign": sign, "nonce": nonce, "t": t, "Content-Type": "application/json; charset=utf8"}

# 2. 会談室の温度計から取得
device_id = "C6A83697434C"
try:
    res = requests.get(f"https://api.switch-bot.com/v1.1/devices/{device_id}/status", headers=get_headers()).json()
    temp = res['body']['temperature']
    hum = res['body']['humidity']

    # 3. Grafana送信 (Influx Line Protocol)
    payload = f"switchbot,device=kaidanshitsu temperature={temp},humidity={hum}"
    
    # 【念押し】Content-Type: text/plain を明示して、Grafanaの「Snappy誤解」を解きます
    response = requests.post(
        g_url, 
        auth=(g_user, g_token), 
        data=payload, 
        headers={'Content-Type': 'text/plain'}
    )

    if response.status_code in [200, 204]:
        print(f"【成功】 Temp:{temp} Hum:{hum} (Status: {response.status_code})")
    else:
        print(f"失敗:{response.status_code} {response.text}")
except Exception as e:
    print(f"エラー発生: {e}")

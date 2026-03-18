import time, hashlib, hmac, base64, requests, os

# 1. 認証情報読み込み
sb_token = os.environ['SB_TOKEN']
sb_secret = os.environ['SB_SECRET']
g_url = os.environ['GRAFANA_URL']
g_user = os.environ['GRAFANA_USER']
g_token = os.environ['GRAFANA_TOKEN']

# 2. SwitchBot API 署名作成
def get_headers():
    t = str(int(time.time() * 1000))
    sign = base64.b64encode(hmac.new(sb_secret.encode('utf-8'), (sb_token + t).encode('utf-8'), hashlib.sha256).digest()).upper()
    return {"Authorization": sb_token, "sign": sign, "nonce": "", "t": t, "Content-Type": "application/json"}

# 3. 会談室の温度計から取得
device_id = "C6A83697434C"
res = requests.get(f"https://api.switch-bot.com/v1.1/devices/{device_id}/status", headers=get_headers()).json()
temp = res['body']['temperature']
hum = res['body']['humidity']

# 4. Grafana Cloud へ送信 (Influx Line Protocol 形式)
payload = f"switchbot,device=kaidanshitsu temperature={temp},humidity={hum}"
response = requests.post(g_url, auth=(g_user, g_token), data=payload)

if response.status_code in [200, 204]:
    print(f"成功！ Temp:{temp} Hum:{hum}")
else:
    print(f"失敗:{response.status_code} {response.text}")

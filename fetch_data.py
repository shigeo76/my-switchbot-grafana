import time
import hashlib
import hmac
import base64
import requests
import os

# GitHub Secrets から読み込み
token = os.environ['SB_TOKEN']
secret = os.environ['SB_SECRET']
remote_write_url = os.environ['GRAFANA_URL']
user_id = os.environ['GRAFANA_USER']
api_token = os.environ['GRAFANA_TOKEN']

# SwitchBot API 認証ヘッダー作成
def get_headers():
    t = str(int(time.time() * 1000))
    nonce = ""
    data = token + t + nonce
    sign = base64.b64encode(hmac.new(secret.encode('utf-8'), data.encode('utf-8'), hashlib.sha256).digest()).upper()
    return {"Authorization": token, "sign": sign, "nonce": nonce, "t": t, "Content-Type": "application/json; charset=utf8"}

# 1. 会談室の温度計 (C6A83697434C) の状態を直接取得
# ※さっきのログで判明したIDを直叩きするのが一番確実で速いです
device_id = "C6A83697434C" 
url = f"https://api.switch-bot.com/v1.1/devices/{device_id}/status"

res = requests.get(url, headers=get_headers()).json()
temp = res['body']['temperature']
hum = res['body']['humidity']

# 2. Grafana Cloud へ送信 (InfluxDB Line Protocol形式)
# この1行が「Snappy圧縮不要」の魔法の形式です
payload = f"switchbot,device={device_id} temperature={temp},humidity={hum}"

response = requests.post(
    remote_write_url,
    auth=(user_id, api_token),
    data=payload
)

if response.status_code in [200, 204]:
    print(f"成功！ 会談室 Temp:{temp} Hum:{hum} (Status:{response.status_code})")
else:
    print(f"失敗: {response.status_code} {response.text}")

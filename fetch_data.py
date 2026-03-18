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

def get_sb_headers():
    nonce = ""
    t = str(int(time.time() * 1000))
    data = token + t + nonce
    sign = base64.b64encode(hmac.new(secret.encode('utf-8'), data.encode('utf-8'), hashlib.sha256).digest()).upper()
    return {"Authorization": token, "sign": sign, "nonce": nonce, "t": t, "Content-Type": "application/json; charset=utf8"}

# 1. デバイス一覧を取得して、温湿度計を探す
devices_res = requests.get("https://api.switch-bot.com/v1.1/devices", headers=get_sb_headers()).json()
target_device_id = None

print("--- Device List ---")
for device in devices_res.get('body', {}).get('deviceList', []):
    print(f"ID: {device['deviceId']}, Name: {device['deviceName']}, Type: {device['deviceType']}")
    if "Meter" in device['deviceType'] or "Hub 2" in device['deviceType']:
        target_device_id = device['deviceId']

if not target_device_id:
    print("温湿度計が見つかりませんでした。")
    exit(1)

# 2. 状態を取得
status_res = requests.get(f"https://api.switch-bot.com/v1.1/devices/{target_device_id}/status", headers=get_sb_headers()).json()
temp = status_res['body']['temperature']
hum = status_res['body']['humidity']

# 3. Grafana Cloud (Prometheus) へ送信 (Simple Remote Write)
timestamp = int(time.time())
payload = f"switchbot_temperature{{device_id=\"{target_device_id}\"}} {temp} {timestamp}\nswitchbot_humidity{{device_id=\"{target_device_id}\"}} {hum} {timestamp}\n"

response = requests.post(
    remote_write_url,
    auth=(user_id, api_token),
    data=payload,
    headers={'Content-Type': 'text/plain'}
)

if response.status_code in [200, 204]:
    print(f"成功: Temp={temp}, Hum={hum}")
else:
    print(f"失敗: {response.status_code} {response.text}")

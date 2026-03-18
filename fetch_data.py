import time, hashlib, hmac, base64, requests

# --- 直接入力セクション ---
# しげおさんのトークンをここに直接貼ってください
sb_token = ecd977b644a98242361d49390faeefd0bc58b16331e47c27b4b266f2ebf5fda1eb7c8e3c33ccb5911193b6559fe6a0be
sb_secret = 28f96baf61a970b7fcab38e3b184e7d0

# Grafanaのトークン（glc_...）をここに直接貼ってください
g_token = glc_eyJvIjoiMTcwMjg2MCIsIm4iOiJzdGFjay0xNTYyODk1LWluZmx1eC13cml0ZS1zd2l0Y2hib3QtdG9rZW4iLCJrIjoiMVAyNVEzRjdiYlNjUzM2ZnM1SjEwUFZwIiwibSI6eyJyIjoicHJvZC1hcC1ub3J0aGVhc3QtMCJ9fQ==

# 以下の2つは固定です
g_url = "https://influx-prod-49-prod-ap-northeast-0.grafana.net/api/v1/push"
g_user = "3050018"
# ------------------------

def get_headers():
    t = str(int(time.time() * 1000))
    sign = base64.b64encode(hmac.new(sb_secret.encode('utf-8'), (sb_token + t).encode('utf-8'), hashlib.sha256).digest()).upper()
    return {"Authorization": sb_token, "sign": sign, "nonce": "", "t": t, "Content-Type": "application/json"}

# 会談室の温度計
device_id = "C6A83697434C"
print(f"Checking device: {device_id}")

try:
    res = requests.get(f"https://api.switch-bot.com/v1.1/devices/{device_id}/status", headers=get_headers()).json()
    temp = res['body']['temperature']
    hum = res['body']['humidity']
    print(f"Fetched Data -> Temp: {temp}, Hum: {hum}")

    # Grafanaへ送信（Content-Typeを明示的に指定）
    payload = f"switchbot,device=kaidanshitsu temperature={temp},humidity={hum}"
    response = requests.post(g_url, auth=(g_user, g_token), data=payload, headers={'Content-Type': 'text/plain'})

    if response.status_code in [200, 204]:
        print(f"成功！ Grafanaに送信しました (Status: {response.status_code})")
    else:
        print(f"失敗: {response.status_code}")
        print(f"Response Body: {response.text}")
except Exception as e:
    print(f"エラー発生: {e}")

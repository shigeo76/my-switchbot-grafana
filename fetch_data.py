import time, hashlib, hmac, base64, requests, os

sb_token = os.environ['SB_TOKEN']
sb_secret = os.environ['SB_SECRET']

def get_sb_headers():
    t = str(int(time.time() * 1000))
    nonce = "anything"
    sign = base64.b64encode(hmac.new(sb_secret.encode('utf-8'), f"{sb_token}{t}{nonce}".encode('utf-8'), hashlib.sha256).digest()).upper()
    return {"Authorization": sb_token, "sign": sign, "nonce": nonce, "t": t}

try:
    print("--- 🔍 SwitchBot デバイス一覧取得開始 ---")
    res = requests.get("https://api.switch-bot.com/v1.1/devices", headers=get_sb_headers()).json()
    
    device_list = res.get('body', {}).get('deviceList', [])
    for d in device_list:
        print(f"名前: {d['deviceName']} | ID: {d['deviceId']} | タイプ: {d['deviceType']}")
    
    print("--- 調査完了 ---")

except Exception as e:
    print(f"Error: {e}")

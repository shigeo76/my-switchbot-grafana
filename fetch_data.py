import time, hashlib, hmac, base64, requests, os

# 1. 認証情報の読み込み
sb_token = os.environ['SB_TOKEN']
sb_secret = os.environ['SB_SECRET']
g_user = os.environ['GRAFANA_USER']
g_token = os.environ['GRAFANA_TOKEN']
g_url = "https://influx-prod-49-prod-ap-northeast-0.grafana.net/api/v1/push/influx/write"

def get_sb_headers():
    t = str(int(time.time() * 1000))
    nonce = "anything"
    sign = base64.b64encode(hmac.new(sb_secret.encode('utf-8'), f"{sb_token}{t}{nonce}".encode('utf-8'), hashlib.sha256).digest()).upper()
    return {"Authorization": sb_token, "sign": sign, "nonce": nonce, "t": t, "Content-Type": "application/json; charset=utf8"}

def push_to_grafana(payload):
    auth_b64 = base64.b64encode(f"{g_user}:{g_token}".encode('ascii')).decode('ascii')
    headers = {"Authorization": f"Basic {auth_b64}", "Content-Type": "text/plain"}
    res = requests.post(g_url, data=payload, headers=headers)
    return res.status_code

# --- メイン処理 ---
try:
    headers = get_sb_headers()
    
    # 1. デバイス一覧を取得
    devices_res = requests.get("https://api.switch-bot.com/v1.1/devices", headers=headers).json()
    device_list = devices_res.get('body', {}).get('deviceList', [])
    
    all_payloads = []
    
    for device in device_list:
        d_id = device['deviceId']
        d_name = device['deviceName'].replace(" ", "_") # スペース対策
        d_type = device['deviceType']
        
        # 2. 各デバイスの詳細ステータスを取得
        status_res = requests.get(f"https://api.switch-bot.com/v1.1/devices/{d_id}/status", headers=headers).json()
        body = status_res.get('body', {})
        
        if not body: continue

        # 3. 取得できる値を抽出（デバイスによって中身が違うので安全に取る）
        metrics = []
        if 'temperature' in body: metrics.append(f"temperature={body['temperature']}")
        if 'humidity' in body: metrics.append(f"humidity={body['humidity']}")
        if 'battery' in body: metrics.append(f"battery={body['battery']}")
        
        # 値がある場合だけペイロード作成
        if metrics:
            line = f"switchbot,device={d_name},type={d_type} {','.join(metrics)}"
            all_payloads.append(line)
            print(f"Collected: {d_name} ({d_type})")

    # 4. まとめてGrafanaへ送信
    if all_payloads:
        final_payload = "\n".join(all_payloads)
        status = push_to_grafana(final_payload)
        print(f"Grafana Push Status: {status}")

except Exception as e:
    print(f"Error: {e}")

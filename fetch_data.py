import time, hashlib, hmac, base64, requests, os

sb_token = os.environ['SB_TOKEN']
sb_secret = os.environ['SB_SECRET']
g_user = os.environ['GRAFANA_USER']
g_token = os.environ['GRAFANA_TOKEN']
g_url = "https://influx-prod-49-prod-ap-northeast-0.grafana.net/api/v1/push/influx/write"

# ターゲット
target_devices = [
    ("C6A83697434C", "kaidanshitsu"),
    ("CA9D747E5EE7", "kitchen")
]

def get_sb_headers():
    t = str(int(time.time() * 1000))
    nonce = "anything"
    sign = base64.b64encode(hmac.new(sb_secret.encode('utf-8'), f"{sb_token}{t}{nonce}".encode('utf-8'), hashlib.sha256).digest()).upper()
    return {"Authorization": sb_token, "sign": sign, "nonce": nonce, "t": t}

try:
    all_lines = []
    sb_headers = get_sb_headers()
    
    auth_b64 = base64.b64encode(f"{g_user}:{g_token}".encode('ascii')).decode('ascii')
    g_headers = {"Authorization": f"Basic {auth_b64}", "Content-Type": "text/plain"}

    for d_id, d_name in target_devices:
        print(f"\n--- Debug: Processing {d_name} ({d_id}) ---")
        res = requests.get(f"https://api.switch-bot.com/v1.1/devices/{d_id}/status", headers=sb_headers).json()
        print(f"Full API Response: {res}") # 生の返り値を全部出す
        
        body = res.get('body', {})
        if body:
            temp = body.get('temperature')
            hum = body.get('humidity')
            print(f"Extracted -> Temp: {temp}, Hum: {hum}")
            
            if temp is not None:
                line = f"switchbot,device={d_name} temperature={temp},humidity={hum}"
                all_lines.append(line)
            else:
                print(f"!!! Error: Temperature is None for {d_name} !!!")

    if all_lines:
        payload = "\n".join(all_lines) + "\n"
        print("\n--- Final Payload to Send ---")
        print(payload)
        
        g_res = requests.post(g_url, data=payload.encode('utf-8'), headers=g_headers)
        print(f"Grafana Status: {g_res.status_code}")
    else:
        print("\n!!! No data collected to send !!!")

except Exception as e:
    print(f"Critical Error: {e}")

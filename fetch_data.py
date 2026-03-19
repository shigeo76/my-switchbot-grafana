import time, hashlib, hmac, base64, requests, os

# 1. 環境変数から認証情報を読み込み
sb_token = os.environ['SB_TOKEN']
sb_secret = os.environ['SB_SECRET']
g_url = "https://influx-prod-49-prod-ap-northeast-0.grafana.net/api/v1/push/influx"
g_user = os.environ['GRAFANA_USER']
g_token = os.environ['GRAFANA_TOKEN']

def get_sb_headers():
    """SwitchBot API用の認証ヘッダー作成"""
    t = str(int(time.time() * 1000))
    nonce = "anything"
    string_to_sign = f"{sb_token}{t}{nonce}"
    sign = base64.b64encode(hmac.new(sb_secret.encode('utf-8'), string_to_sign.encode('utf-8'), hashlib.sha256).digest()).upper()
    return {
        "Authorization": sb_token, "sign": sign, "nonce": nonce, "t": t,
        "Content-Type": "application/json; charset=utf8"
    }

def get_grafana_headers():
    """PowerShellで成功したBasic認証と特殊ヘッダーを完全再現"""
    auth_raw = f"{g_user}:{g_token}"
    auth_b64 = base64.b64encode(auth_raw.encode('ascii')).decode('ascii')
    return {
        "Authorization": f"Basic {auth_b64}",
        "Content-Type": "text/plain",
        "X-Prometheus-Remote-Write-Version": "0.1.0"     # プロトコルを明示
    }

# 2. SwitchBotからデータ取得
device_id = "C6A83697434C"
print(f"--- Step 1: SwitchBot API アクセス開始 ---")
try:
    response = requests.get(f"https://api.switch-bot.com/v1.1/devices/{device_id}/status", headers=get_sb_headers())
    res_data = response.json()
    print(f"SwitchBot API Response: {res_data}")

    if res_data.get('statusCode') == 100:
        temp = res_data['body']['temperature']
        hum = res_data['body']['humidity']
        print(f"データ取得成功 -> 温度: {temp}, 湿度: {hum}")

        # 3. Grafana Cloudへ送信
        print(f"--- Step 2: Grafana Cloud 送信開始 ---")
        # 改行なしの1行データ
        payload = f"switchbot,device=kaidanshitsu temperature={temp},humidity={hum}"
        
        # PowerShellと同じヘッダーでPOST
        g_res = requests.post(g_url, data=payload, headers=get_grafana_headers())

        print(f"Grafana Status Code: {g_res.status_code}")
        if g_res.status_code == 204:
            print(f"【完全成功】Grafanaへの書き込みが完了しました。")
        else:
            print(f"Grafana Response Body: {g_res.text}")
            print(f"【失敗】Status Code: {g_res.status_code}")
    else:
        print(f"【失敗】SwitchBotエラー: {res_data.get('message')}")

except Exception as e:
    print(f"【エラー】実行中に例外が発生しました: {e}")

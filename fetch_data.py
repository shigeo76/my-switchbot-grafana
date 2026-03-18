import time, hashlib, hmac, base64, requests, os

# 1. 認証情報読み込み
sb_token = os.environ['SB_TOKEN']
sb_secret = os.environ['SB_SECRET']
g_url = os.environ['GRAFANA_URL']
g_user = os.environ['GRAFANA_USER']
g_token = os.environ['GRAFANA_TOKEN']

def get_headers():
    t = str(int(time.time() * 1000))
    nonce = "anything"
    string_to_sign = f"{sb_token}{t}{nonce}"
    sign = base64.b64encode(hmac.new(sb_secret.encode('utf-8'), string_to_sign.encode('utf-8'), hashlib.sha256).digest()).upper()
    return {
        "Authorization": sb_token, "sign": sign, "nonce": nonce, "t": t,
        "Content-Type": "application/json; charset=utf8"
    }

# 2. 会談室の温度計から取得
device_id = "C6A83697434C"
print(f"--- Step 1: SwitchBot API アクセス開始 ---")
try:
    response = requests.get(f"https://api.switch-bot.com/v1.1/devices/{device_id}/status", headers=get_headers())
    res_data = response.json()
    
    # 【ログ追加】SwitchBotからの生の返答を表示
    print(f"SwitchBot API Response: {res_data}")

    if res_data.get('statusCode') == 100:
        temp = res_data['body']['temperature']
        hum = res_data['body']['humidity']
        print(f"データ取得成功 -> 温度: {temp}, 湿度: {hum}")

        # 3. Grafana送信
        print(f"--- Step 2: Grafana Cloud 送信開始 ---")
        payload = f"switchbot,device=kaidanshitsu temperature={temp},humidity={hum}"
        print(f"送信データ(Line Protocol): {payload}")
        
        g_res = requests.post(g_url, auth=(g_user, g_token), data=payload, headers={'Content-Type': 'text/plain'})

        # 【ログ追加】Grafanaからの返答を表示
        print(f"Grafana Status Code: {g_res.status_code}")
        print(f"Grafana Response Body: {g_res.text}")

        if g_res.status_code in [200, 204]:
            print(f"【完全成功】Grafanaへの書き込みが完了しました。")
        else:
            print(f"【失敗】Grafanaがデータを受け取りませんでした。")
    else:
        print(f"【失敗】SwitchBotの認証エラーまたはデバイス未発見: {res_data.get('message')}")

except Exception as e:
    print(f"【エラー】実行中に例外が発生しました: {e}")

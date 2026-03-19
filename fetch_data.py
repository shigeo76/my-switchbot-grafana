import time
import hashlib
import hmac
import base64
import requests
import os

# 1. 環境変数からの認証情報読み込み
sb_token = os.environ['SB_TOKEN']
sb_secret = os.environ['SB_SECRET']
g_url = os.environ['GRAFANA_URL']
g_user = os.environ['GRAFANA_USER']
g_token = os.environ['GRAFANA_TOKEN']

def get_sb_headers():
    """SwitchBot API用の認証ヘッダー作成"""
    t = str(int(time.time() * 1000))
    nonce = "anything"
    string_to_sign = f"{sb_token}{t}{nonce}"
    sign = base64.b64encode(
        hmac.new(
            sb_secret.encode('utf-8'), 
            string_to_sign.encode('utf-8'), 
            hashlib.sha256
        ).digest()
    ).upper()
    return {
        "Authorization": sb_token,
        "sign": sign,
        "nonce": nonce,
        "t": t,
        "Content-Type": "application/json; charset=utf8"
    }

def get_grafana_auth():
    """Grafana Basic認証用のBase64文字列作成"""
    auth_str = f"{g_user}:{g_token}"
    return base64.b64encode(auth_str.encode('ascii')).decode('ascii')

# 2. 会談室の温度計(Meter)からデータ取得
device_id = "C6A83697434C"
print(f"--- Step 1: SwitchBot API アクセス開始 ---")

try:
    sb_response = requests.get(
        f"https://api.switch-bot.com/v1.1/devices/{device_id}/status", 
        headers=get_sb_headers()
    )
    res_data = sb_response.json()
    print(f"SwitchBot API Response: {res_data}")

    if res_data.get('statusCode') == 100:
        temp = res_data['body']['temperature']
        hum = res_data['body']['humidity']
        print(f"データ取得成功 -> 温度: {temp}, 湿度: {hum}")

        # 3. Grafana Cloud 送信 (PowerShellで成功した形式)
        print(f"--- Step 2: Grafana Cloud 送信開始 ---")
        
        # Line Protocol形式のデータ (前後の空白を排除)
        payload = f"switchbot,device=kaidanshitsu temperature={temp},humidity={hum}".strip()
        print(f"送信データ(Line Protocol): {payload}")

        # PowerShellで204を叩き出した「黄金のヘッダー」
        g_headers = {
            "Authorization": f"Basic {get_grafana_auth()}",
            "Content-Type": "application/x-protobuf",
            "X-Prometheus-Remote-Write-Version": "0.1.0"
        }

        g_res = requests.post(g_url, headers=g_headers, data=payload)

        print(f"Grafana Status Code: {g_res.status_code}")
        
        # 204 は成功（Bodyが空なので text は出力しない）
        if g_res.status_code == 204:
            print("【完全成功】Grafanaへの書き込みが完了しました！")
        else:
            print(f"Grafana Response Body: {g_res.text}")
            print(f"【失敗】Status Code: {g_res.status_code}")

    else:
        print(f"【失敗】SwitchBotエラー: {res_data.get('message')}")

except Exception as e:
    print(f"【例外発生】: {e}")

import time, hashlib, hmac, base64, requests, os
import snappy
from prometheus_pb import remote_pb2

# Secrets読み込み
sb_token = os.environ['SB_TOKEN']
sb_secret = os.environ['SB_SECRET']
g_url = os.environ['GRAFANA_URL'].replace('influx-', 'prometheus-').replace('/api/v1/push', '/api/prom/push')
g_user = os.environ['GRAFANA_USER']
g_token = os.environ['GRAFANA_TOKEN']

def get_headers():
    t = str(int(time.time() * 1000))
    sign = base64.b64encode(hmac.new(sb_secret.encode('utf-8'), (sb_token + t).encode('utf-8'), hashlib.sha256).digest()).upper()
    return {"Authorization": sb_token, "sign": sign, "nonce": "", "t": t}

# 会談室の温度計から取得
device_id = "C6A83697434C"
res = requests.get(f"https://api.switch-bot.com/v1.1/devices/{device_id}/status", headers=get_headers()).json()
temp = float(res['body']['temperature'])

# --- Prometheus Remote Write 形式の構築 (Snappy圧縮) ---
write_request = remote_pb2.WriteRequest()
timeseries = write_request.timeseries.add()
timeseries.labels.add(name="__name__", value="switchbot_temperature")
timeseries.labels.add(name="device", value="kaidanshitsu")

sample = timeseries.samples.add()
sample.value = temp
sample.timestamp = int(time.time() * 1000)

compressed_data = snappy.compress(write_request.SerializeToString())
# -----------------------------------------------------

response = requests.post(
    g_url,
    auth=(g_user, g_token),
    data=compressed_data,
    headers={'Content-Type': 'application/x-protobuf', 'Content-Encoding': 'snappy', 'X-Prometheus-Remote-Write-Version': '0.1.0'}
)

if response.status_code in [200, 204]:
    print(f"成功！送った温度: {temp}")
else:
    print(f"失敗:{response.status_code} {response.text}")

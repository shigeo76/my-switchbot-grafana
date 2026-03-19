name: SwitchBot-Push
on:
  schedule:
    - cron: '*/15 * * * *'
  workflow_dispatch:

jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: pip install requests

      - name: Run Script and Push to Grafana
        env:
          SB_TOKEN: ${{ secrets.SB_TOKEN }}
          SB_SECRET: ${{ secrets.SB_SECRET }}
          GRAFANA_URL: ${{ secrets.GRAFANA_URL }}
          GRAFANA_USER: ${{ secrets.GRAFANA_USER }}
          GRAFANA_TOKEN: ${{ secrets.GRAFANA_TOKEN }}
        run: |
          # 1. PythonでSwitchBotからデータを取得し、Line Protocol形式で一時ファイルに保存
          python -c "
          import time, hashlib, hmac, base64, requests, os
          def get_sb_headers():
              t = str(int(time.time() * 1000))
              nonce = 'anything'
              string_to_sign = f'{os.environ[\"SB_TOKEN\"]}{t}{nonce}'
              sign = base64.b64encode(hmac.new(os.environ[\"SB_SECRET\"].encode('utf-8'), string_to_sign.encode('utf-8'), hashlib.sha256).digest()).upper()
              return {'Authorization': os.environ[\"SB_TOKEN\"], 'sign': sign, 'nonce': nonce, 't': t}
          
          res = requests.get('https://api.switch-bot.com/v1.1/devices/C6A83697434C/status', headers=get_sb_headers()).json()
          if res.get('statusCode') == 100:
              temp, hum = res['body']['temperature'], res['body']['humidity']
              print(f'switchbot,device=kaidanshitsu temperature={temp},humidity={hum}', end='')
          " > payload.txt

          # 2. curl で Grafana に直接叩き込む (PowerShellでの成功をUbuntuで再現)
          echo "Sending to Grafana..."
          curl -v -X POST "${{ secrets.GRAFANA_URL }}" \
            -u "${{ secrets.GRAFANA_USER }}:${{ secrets.GRAFANA_TOKEN }}" \
            -H "Content-Type: application/x-protobuf" \
            -H "X-Prometheus-Remote-Write-Version: 0.1.0" \
            --data-binary @payload.txt

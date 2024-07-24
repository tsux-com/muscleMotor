import serial
import time
import threading

# シリアルポートの設定
ser = serial.Serial(
    port='COM3',       # 使用するポート（例: COM3）
    baudrate=38400,    # ボーレート（例: 38400）
    timeout=3          # タイムアウト（秒）
)

commands1 = [
    {'commands': ['speed=1', 'power=1', 'InchingjogSpeed=80',
                  'InchingFeedAmount=200'], 'wait': 1},
    {'commands': ['motionstart'], 'wait': 3},
    {'commands': ['stop'], 'wait': 2},
    {'commands': ['speed=10', 'power=5', 'InchingjogSpeed=100'], 'wait': 1},
    {'commands': ['motionstart'], 'wait': 4},
    {'commands': ['stop'], 'wait': 2},
]

# 変換のルールを定義します
conversion_rules = {
    'motionstart': '^',
    'start': '[',
    'stop': ']',
    'speed': 'K2',
    'InchingjogSpeed': 'K50',
    'InchingFeedAmount': "K51",
    'coordinateDirection': 'k4',
    'power': 'K12'
}

# データを変換する関数を定義します


def convert_commands(data, rules):
    converted_data = []
    for item in data:
        new_commands = []
        for command in item['commands']:
            if '=' in command:
                key, value = command.split('=')
                new_key = rules.get(key, key)
                new_commands.append(f"{new_key}={value}")
            else:
                new_commands.append(rules.get(command, command))
        converted_data.append({'commands': new_commands, 'wait': item['wait']})
    return converted_data


send_data = convert_commands(commands1, conversion_rules)

print(send_data)

# 受信データを処理するスレッド関数


def receive_data():
    while True:
        if ser.in_waiting > 0:
            received_data = ser.readline().decode('utf-8').strip()
            print(f"受信データ: {received_data}")
        time.sleep(1)

# 送信データを処理するスレッド関数


def send_data_thread(send_data):
    try:
        for data in send_data:
            for command in data['commands']:
                # 送信する文字列にCR+LFを追加
                send_str = command + '\r\n'
                # 文字列をUTF-8でエンコード
                send_bytes = send_str.encode('utf-8')
                ser.write(send_bytes)
                print(f"送信データ: {send_bytes}")

            # 指定時間待機
            time.sleep(data['wait'])

    except serial.SerialException as e:
        print(f"シリアル通信エラー: {e}")
    finally:
        ser.close()


# 受信スレッドの開始
receive_thread = threading.Thread(target=receive_data)
receive_thread.daemon = True
receive_thread.start()

# 送信スレッドの開始
send_thread = threading.Thread(target=send_data_thread, args=(send_data,))
send_thread.start()

# 送信スレッドが終了するのを待機
send_thread.join()

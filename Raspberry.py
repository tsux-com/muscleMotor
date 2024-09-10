import serial
import time
import threading
import os
from typing import Any, Dict, List
import json
from openai import AzureOpenAI
import re

# Azure OpenAI サービスのエンドポイント
endpoint = "https://musclemotor.openai.azure.com/"

# OpenAI APIキー
api_key = ""  # ここに取得したAPIキーを設定

# OpenAIクライアントの初期化
client = AzureOpenAI(
    azure_endpoint=endpoint,
    api_key=api_key,  # APIキーを設定
    api_version="2024-05-01-preview",
)

completion = client.chat.completions.create(
    model="gpt-35-turbo",
    messages=[
        {
            "role": "user",
            "content": "yamaguti.txtというファイルの内容を調べてください。"
        }
    ],
    max_tokens=800,
    temperature=0.7,
    top_p=0.95,
    frequency_penalty=0,
    presence_penalty=0,
    stop=None,
    stream=False,
    extra_body={
        "data_sources": [{
            "type": "azure_search",
            "parameters": {
                "endpoint": "https://musclemotor.search.windows.net",
                "index_name": "vector-1723096776192",
                "semantic_configuration": "vector-1723096776192-semantic-configuration",
                "query_type": "semantic",
                "fields_mapping": {},
                "in_scope": True,
                "role_information": "You are an AI assistant that helps people find information.",
                "filter": None,
                "strictness": 3,
                "top_n_documents": 5,
                "authentication": {
                    "type": "api_key",
                    "key": ""
                }
            }
        }]
    }
)

# JSONレスポンスを取得
response_json = completion.to_json()

# レスポンスから "content" の部分を取り出す
response_data = json.loads(response_json)
content = response_data["choices"][0]["message"]["content"]

# 文字列として表現されている辞書を正規表現で抽出
matches = re.findall(r"{'commands': \['[^\]]+'], 'wait': \d+}", content)

# 抽出された内容を辞書形式に変換
commands1 = []
for match in matches:
    # 辞書形式の文字列を Python 辞書に変換
    command_dict = eval(match)
    commands1.append(command_dict)

# シリアルポートの設定
ser = serial.Serial(
    port='/dev/ttyUSB0',       # 使用するポート（例: COM3）
    baudrate=38400,    # ボーレート（例: 38400）
    timeout=3          # タイムアウト（秒）
)

# 変換のルールを定義します
conversion_rules = {
    'motionstart': '^',
    'start': '[',
    'stop': ']',
    'speed': 'S',
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
        converted_data.append(
            {'commands': new_commands, 'wait': item['wait'], 'repetition': item.get('repetition', 1)})
    return converted_data


# 受信データを処理するスレッド関数
ser_lock = threading.Lock()  # シリアルポート操作用のロック


def receive_data():
    try:
        while True:
            with ser_lock:  # シリアルポート操作をロック
                if ser.in_waiting > 0:
                    received_data = ser.readline().decode('utf-8').strip()
                    print(f"受信データ: {received_data}")
            time.sleep(1)
    except serial.SerialException as e:
        print(f"シリアル通信エラー（受信側）: {e}")
    except Exception as e:
        print(f"受信中に予期しないエラーが発生しました: {e}")
    finally:
        with ser_lock:  # シリアルポート操作をロックして閉じる
            ser.close()  # シリアルポートを閉じる処理を追加


# repetitionをPython内で管理し、コマンドの繰り返し処理を行う関数
stop_flag = False  # 無限ループの停止フラグ


def send_data_thread(send_data):
    global stop_flag
    try:
        while not stop_flag:  # 無限ループを全体に適用
            for data in send_data:
                repeat_count = data['repetition']

                # 無限ループの場合
                if repeat_count == 0:
                    while not stop_flag:  # 無限ループを停止するまで繰り返し
                        for command in data['commands']:
                            send_str = command + '\r\n'
                            send_bytes = send_str.encode('utf-8')
                            with ser_lock:  # シリアルポート操作をロック
                                ser.write(send_bytes)
                            print(f"送信データ: {send_bytes}")
                        time.sleep(data['wait'])

                # 繰り返しがある場合
                else:
                    for _ in range(repeat_count):
                        for command in data['commands']:
                            if not command.startswith("repetition="):
                                send_str = command + '\r\n'
                                send_bytes = send_str.encode('utf-8')
                                with ser_lock:  # シリアルポート操作をロック
                                    ser.write(send_bytes)
                                print(f"送信データ: {send_bytes}")
                        time.sleep(data['wait'])

    except serial.SerialException as e:
        print(f"シリアル通信エラー: {e}")
    finally:
        with ser_lock:  # シリアルポート操作をロックして閉じる
            ser.close()


def stop_loop():
    global stop_flag
    stop_flag = True

# エンターキー入力を監視するスレッド


def input_thread():
    input("エンターキーを押すと無限ループを停止します...\n")
    stop_loop()


# テスト用データ（例: yamaguti.txt の内容）
commands = commands1
print(commands1)  # commands1 の内容を確認してみる

# コマンドを変換して送信データを作成
send_data = convert_commands(commands, conversion_rules)

# 受信スレッドの開始
receive_thread = threading.Thread(target=receive_data)
receive_thread.daemon = True
receive_thread.start()

# 送信スレッドの開始
send_thread = threading.Thread(target=send_data_thread, args=(send_data,))
send_thread.start()

# エンターキー入力スレッドの開始
input_thread = threading.Thread(target=input_thread)
input_thread.start()

# 送信スレッドが終了するのを待機
send_thread.join()

import serial
import time
import threading
import os
from typing import Any, Dict, List
import re
from datetime import datetime  # 日付と時刻を取得するために追加

from dotenv import load_dotenv

# .envファイルの内容を読み込見込む
load_dotenv()

# 抽出された内容を辞書形式に変換
commands1 = [
    {'commands': ['speed=250'], 'wait': 0},
    {'commands': ['motionstart'], 'wait': 4},
    {'commands': ['stop'], 'wait': 0},
    {'commands': ['speed=-250'], 'wait': 0},
    {'commands': ['motionstart'], 'wait': 4},
    {'commands': ['speed=150'], 'wait': 4},
    {'commands': ['speed=-150'], 'wait': 4},
    {'commands': ['stop'], 'wait': 0},
    {'commands': ['repetition=0'], 'wait': 0},
]

# シリアルポートの設定
ser = serial.Serial(
    port=os.environ['PORT'],       # 使用するポート（例: COM3）
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

# ここでser_lockを定義します（スレッド間のシリアルポート操作をロック）
ser_lock = threading.Lock()

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


# 停止と一時停止のフラグ
stop_flag = False  # 無限ループの停止フラグ
pause_flag = False  # コマンド送信の一時停止フラグ

last_sent_data = None  # 最後に送信されたデータを保持する変数

# 日付と時刻を取得してフォーマットする関数


def get_current_timestamp():
    return datetime.now().strftime('%Y/%m/%d %H:%M:%S')

# 日付ごとのログファイルパスを取得する関数


def get_log_file_path():
    current_date = datetime.now().strftime('%Y-%m-%d')  # 現在の日付を取得してフォーマット
    log_dir = 'log'

    # ディレクトリが存在しない場合は作成
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file_name = f"serial_communication_log_{current_date}.txt"
    return os.path.join(log_dir, log_file_name)

# データを送信する関数


def send_data_thread(send_data):
    global stop_flag, pause_flag, last_sent_data
    try:
        loop_count = 1  # ループカウントの初期化
        while not stop_flag:  # stop_flag をチェック
            if pause_flag:
                time.sleep(1)  # 一時停止中はループをスキップ
                continue

            # ループ実行のログ出力
            log_message = f"{get_current_timestamp()} [{loop_count}セット目のループ実行]"
            print(log_message)
            with open(get_log_file_path(), 'a') as log_file:
                log_file.write(log_message + "\n")
                log_file.flush()

            for data in send_data:
                if stop_flag:  # stop_flag をチェック
                    break
                repeat_count = data['repetition']

                # 無限ループの場合
                if repeat_count == 0:
                    while not stop_flag:  # stop_flag をチェック
                        for command in data['commands']:
                            send_str = command + '\r\n'
                            send_bytes = send_str.encode('utf-8')
                            last_sent_data = send_bytes  # 最後に送信されたデータを記録
                            with ser_lock:  # シリアルポート操作をロック
                                ser.write(send_bytes)
                            print(f"送信データ: {send_bytes}")
                            # 送信データをログに記録
                            with open(get_log_file_path(), 'a') as log_file:
                                log_file.write(
                                    f"{get_current_timestamp()} 送信データ : {send_bytes.decode('utf-8')}\n")
                                log_file.flush()  # バッファをフラッシュしてデータを書き込む
                        time.sleep(data['wait'])
                        if stop_flag:  # stop_flag をチェック
                            break
                    loop_count += 1  # ループカウントを増加

                # 繰り返しがある場合
                else:
                    for _ in range(repeat_count):
                        if stop_flag:  # stop_flag をチェック
                            break
                        for command in data['commands']:
                            if not command.startswith("repetition="):
                                send_str = command + '\r\n'
                                send_bytes = send_str.encode('utf-8')
                                last_sent_data = send_bytes  # 最後に送信されたデータを記録
                                with ser_lock:  # シリアルポート操作をロック
                                    ser.write(send_bytes)
                                print(f"送信データ: {send_bytes}")
                                # 送信データをログに記録
                                with open(get_log_file_path(), 'a') as log_file:
                                    log_file.write(
                                        f"{get_current_timestamp()} 送信データ : {send_bytes.decode('utf-8')}\n")
                                    log_file.flush()  # バッファをフラッシュしてデータを書き込む
                        time.sleep(data['wait'])
            loop_count += 1  # ループカウントを増加
    except serial.SerialException as e:
        error_message = f"{get_current_timestamp()} シリアル通信エラー: {e}"
        print(error_message)
        # エラーメッセージをログに記録
        with open(get_log_file_path(), 'a') as log_file:
            log_file.write(error_message + "\n")
    finally:
        with ser_lock:  # シリアルポート操作をロックして閉じる
            ser.close()

# データを受信する関数


def receive_data():
    global pause_flag, last_sent_data
    try:
        while not stop_flag:  # stop_flag をチェック
            with ser_lock:  # シリアルポート操作をロック
                if ser.in_waiting > 0:
                    received_data = ser.readline().decode('utf-8').strip()
                    print(f"受信データ: {received_data}")
                    # 受信データをログに記録
                    with open(get_log_file_path(), 'a') as log_file:
                        log_file.write(
                            f"{get_current_timestamp()} 受信データ: {received_data}\n")
                        log_file.flush()  # バッファをフラッシュしてデータを書き込む

                    # Ux.1=2のエラーが検出された場合
                    if "Ux.1=2" in received_data:
                        log_message = f"{get_current_timestamp()} 過電圧アラームー検出: コマンド送信を一時停止"
                        print(log_message)
                        with open(get_log_file_path(), 'a') as log_file:
                            log_file.write(log_message + "\n")
                            log_file.flush()
                        pause_flag = True  # コマンド送信を一時停止

                    # 過負荷エラーメッセージが含まれているか確認
                    if re.search(r'\bUx\.1=4\b', received_data):
                        log_message = f"{get_current_timestamp()} 過負荷アラーム検出: コマンド送信を一時停止"
                        print(log_message)
                        with open(get_log_file_path(), 'a') as log_file:
                            log_file.write(log_message + "\n")
                            log_file.flush()
                        pause_flag = True  # コマンド送信を一時停止

                    if re.search(r'\bUx\.1=512\b', received_data):
                        log_message = f"{get_current_timestamp()} 電源断: コマンド送信を一時停止"
                        print(log_message)
                        with open(get_log_file_path(), 'a') as log_file:
                            log_file.write(log_message + "\n")
                            log_file.flush()
                        pause_flag = True  # コマンド送信を一時停止

            time.sleep(1)
    except serial.SerialException as e:
        error_message = f"{get_current_timestamp()} シリアル通信エラー（受信側）: {e}"
        print(error_message)
        # エラーメッセージをログに記録
        with open(get_log_file_path(), 'a') as log_file:
            log_file.write(error_message + "\n")
    except Exception as e:
        error_message = f"{get_current_timestamp()} 受信中に予期しないエラーが発生しました: {e}"
        print(error_message)
        # エラーメッセージをログに記録
        with open(get_log_file_path(), 'a') as log_file:
            log_file.write(error_message + "\n")
    finally:
        with ser_lock:  # シリアルポート操作をロックして閉じる
            ser.close()

# 無限ループの停止を監視する関数


def input_thread():
    input("エンターキーを押すと無限ループを停止します...\n")
    stop_loop()


def stop_loop():
    global stop_flag
    stop_flag = True


# コマンドを変換して送信データを作成
send_data = convert_commands(commands1, conversion_rules)

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

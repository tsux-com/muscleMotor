# muscleMotor

musclemota 動かすサンプルプログラム

# インストール

openai のインストールがまだの場合(update が必要な場合は必要に応じて行ってください）

    pip install openai
    pip install --upgrade openai

Windows の場合は threading をインストールする必要の可能性あり

以下のコマンドを実行して仮想環境を作成します。

    python -m venv myenv

仮想環境をアクティベートします。

    myenv\Scripts\activate

macOS および Linux の場合

    python3 -m venv myenv

仮想環境をアクティベートします。

    source myenv/bin/activate

作業が終了したら、仮想環境を非アクティベートすることができます。

    deactivate

# Raspberry Pi で実行

対象ディレクトリにて serial_communication.py を実行してください。

    python3 serial_communication.py

# Windows で実行

    win.py

を実行してください。

# 接続情報について

下記の情報が必要になります。Azure で取得してください。

- Azure OpenAI サービスのエンドポイント(endpoint)
- OpenAI API キー (api_key) Azure
- Search リソース キー(extra_body 内にある parameters の key)

# シリアルポートについて

シリアルポートの設定は環境に合わせて変更してください。

Windows デフォルト

      port='COM3',

Raspberry Pi (USB 接続)

    port='/dev/ttyUSB0

# muscleMotor

musclemota 動かすサンプルプログラム

# インストール

requirement.txtのコマンドを入力したらOKです。

例:openai のインストールがまだの場合(update が必要な場合は必要に応じて行ってください）

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

# ChatGPTに繋げて実行

対象ディレクトリにて main.py を実行してください。

    python3 main.py



# モータ単体で実行

対象ディレクトリにて motor.py 実行してください。パラメータは自由に設定可能です。

    motor.py


# 接続情報について

下記の情報が必要になります。Azure で取得してください。

- Azure OpenAI サービスのエンドポイント(endpoint)
- OpenAI API キー (api_key) Azure
- Search リソース キー(extra_body 内にある parameters の key)

# シリアルポートについて

シリアルポートの設定は環境に合わせて変更してください。(.envで変更可能)

Windows デフォルト

      port='COM3',

Raspberry Pi (USB 接続)

    port='/dev/ttyUSB0

# 無限ループについて

エンターキーで停止します。

# .env 情報

    OPEN_API_KEY=""
    AUTHENTICATION_API_KEY=""


    # シリアルポート設定

    #win
    PORT="COM3"

    #Linux
    # PORT='/dev/ttyUSB0'

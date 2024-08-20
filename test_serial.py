import os
import json
from openai import AzureOpenAI
import re

# Azure OpenAI サービスのエンドポイント
endpoint = "https://musclemotor.openai.azure.com/"

# OpenAI APIキー
# api_key = ""  # ここに取得したAPIキーを設定

# OpenAIクライアントの初期化
client = AzureOpenAI(
    azure_endpoint=endpoint,
    # api_key=api_key,  # APIキーを設定
    api_version="2024-05-01-preview",
)

completion = client.chat.completions.create(
    model="gpt-35-turbo",
    messages=[
        {
            "role": "user",
            "content": "yamaguti.txtの内容は？"
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
                    "key": ""  # キーを入れる
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

# 抽出された内容を表示
for match in matches:
    print(match)

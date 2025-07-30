# Python 3.12の公式イメージをベースにする
FROM python:3.12-slim

# 作業ディレクトリを設定
WORKDIR /app

# 必要なライブラリをインストール
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションのソースコードをコピー
COPY . .

# サーバーを起動
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]

import os
import json
from flask import Request, Response
from google.cloud import pubsub_v1

# 環境変数から設定を読み込み
TLDV_SIGNING_SECRET = os.environ.get("TLDV_SIGNING_SECRET")
PROJECT_ID = os.environ.get("GCP_PROJECT", "proj-tldv-knowledge") # ★ デフォルト値を設定
TOPIC_ID = "tldv.meeting-events"

publisher = pubsub_v1.PublisherClient()
# ★ プロジェクトIDを明示的に指定
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)

def main(request: Request) -> Response:
    """
    tl;dv Webhookを受け取り、署名を検証し、Pub/Subにイベントを発行する。
    """
    # 1. 署名検証
    signature = request.headers.get("tldv-signature")
    if not signature:
        return Response("Missing tldv-signature header", status=401)
    
    # ★ .strip() を使って前後の空白を除去
    if signature.strip() != TLDV_SIGNING_SECRET:
        print(f"Invalid signature.") # シンプルなログに変更
        return Response("Invalid signature", status=401)

    # 2. イベントをPub/Subに発行
    try:
        event_data = request.get_json()
        meeting_id = event_data.get("data", {}).get("id")
        event_type = event_data.get("event")

        if not meeting_id or not event_type:
             return Response("Invalid payload", status=400)

        future = publisher.publish(
            topic_path, 
            data=json.dumps(event_data).encode("utf-8"),
            meeting_id=str(meeting_id),
            event_type=event_type
        )
        future.result()
        
        print(f"Published event {event_type} for meeting {meeting_id} to {TOPIC_ID}")
        return Response("Event processed", status=200)

    except Exception as e:
        print(f"Error processing event: {e}")
        return Response("Internal Server Error", status=500) 
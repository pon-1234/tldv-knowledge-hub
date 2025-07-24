import os
import hmac
import hashlib
import json
from flask import Request, Response
from google.cloud import pubsub_v1

# 環境変数から設定を読み込み
TLDV_SIGNING_SECRET = os.environ.get("TLDV_SIGNING_SECRET", "your-local-secret")
PROJECT_ID = os.environ.get("GCP_PROJECT")
TOPIC_ID = "tldv.meeting-events"

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)

def main(request: Request) -> Response:
    """
    tl;dv Webhookを受け取り、署名を検証し、Pub/Subにイベントを発行する。
    """
    # 1. 署名検証 (セキュリティの要)
    signature = request.headers.get("tldv-signature")
    if not signature:
        return Response("Missing signature", status=401)
    
    body = request.get_data()
    expected_signature = hmac.new(
        key=TLDV_SIGNING_SECRET.encode(),
        msg=body,
        digestmod=hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, signature):
        print(f"Invalid signature. Expected: {expected_signature}, Got: {signature}")
        return Response("Invalid signature", status=401)

    # 2. イベントをPub/Subに発行
    try:
        event_data = request.get_json()
        meeting_id = event_data.get("data", {}).get("id")
        event_type = event_data.get("event")

        if not meeting_id or not event_type:
             return Response("Invalid payload", status=400)

        # 冪等性のため、meeting_idを属性として追加
        future = publisher.publish(
            topic_path, 
            data=json.dumps(event_data).encode("utf-8"),
            meeting_id=str(meeting_id),
            event_type=event_type
        )
        future.result()  # 送信完了を待つ
        
        print(f"Published event {event_type} for meeting {meeting_id} to {TOPIC_ID}")
        return Response("Event processed", status=200)

    except Exception as e:
        print(f"Error processing event: {e}")
        return Response("Internal Server Error", status=500) 
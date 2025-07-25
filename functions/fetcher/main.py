import os
import json
import base64
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from google.cloud import bigquery
from cloudevents.http import from_http

TLDV_API_KEY = os.environ.get("TLDV_API_KEY") # Secret Managerからマウントされる
BASE_URL = "https://pasta.tldv.io/v1alpha1"

bq_client = bigquery.Client()
DATASET_ID = "knowledge_ds"

# リトライ戦略を設定したセッションを作成
def create_retry_session():
    session = requests.Session()
    retry = Retry(
        total=3,                # 合計3回リトライ
        read=3,
        connect=3,
        backoff_factor=0.3,     # 指数バックオフ
        status_forcelist=(500, 502, 503, 504), # サーバーエラー時にリトライ
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def main(event, context):
    """
    Pub/Subトリガーで起動し、tl;dvからデータを取得してBigQueryに格納する。
    """
    try:
        pubsub_message = base64.b64decode(event['data']).decode('utf-8')
        data = json.loads(pubsub_message)
        
        event_payload = data.get("data", {})
        event_type = data.get("event")

        # ★★★ 最終修正 ★★★
        # 正しい階層から "meetingId" を取得する
        meeting_id = event_payload.get("meetingId")
        
        # meetingId がない場合のフォールバック
        if not meeting_id:
            meeting_id = event_payload.get("id")

        print(f"Processing event {event_type} for meeting {meeting_id}...")

        if event_type != "TranscriptReady":
            print(f"Skipping event type: {event_type}")
            return "OK", 200

        headers = {"x-api-key": TLDV_API_KEY}
        url = f"{BASE_URL}/meetings/{meeting_id}/transcript"
        
        session = create_retry_session()
        transcript_res = session.get(url, headers=headers)
        
        transcript_res.raise_for_status()
        transcripts = transcript_res.json().get("data", [])
        
        # 2. BigQueryに格納するデータを作成
        rows_to_insert = [
            {
                "meeting_id": meeting_id,
                "text": item.get("text"),
                "start_time": item.get("startTime"),
                "end_time": item.get("endTime"),
                "speaker_name": item.get("speaker", {}).get("name"),
                "turn_index": item.get("turnIndex"),
            }
            for item in transcripts
        ]

        if not rows_to_insert:
            print("No transcripts to insert.")
            return "OK", 200

        # 3. BigQueryにストリーミングインサート
        table_id = f"{DATASET_ID}.transcripts"
        errors = bq_client.insert_rows_json(table_id, rows_to_insert)
        
        if errors == []:
            print(f"Successfully inserted {len(rows_to_insert)} rows for meeting {meeting_id}.")
        else:
            print(f"Encountered errors while inserting rows: {errors}")
            raise Exception(f"BigQuery insert error: {errors}")

        return "OK", 200

    except Exception as e:
        print(f"Error in fetcher: {e}")
        # エラーをraiseするとPub/Subが再試行し、最終的にDLQに送られる
        raise e 
import os
import json
import requests
from google.cloud import bigquery
from cloudevents.http import from_http

TLDV_API_KEY = os.environ.get("TLDV_API_KEY") # Secret Managerからマウントされる
BASE_URL = "https://pasta.tldv.io/v1alpha1"

bq_client = bigquery.Client()
DATASET_ID = "knowledge_ds"

def main(cloudevent):
    """
    Pub/Subトリガーで起動し、tl;dvからデータを取得してBigQueryに格納する。
    """
    try:
        data = json.loads(cloudevent.data.decode("utf-8"))
        meeting_id = data.get("meeting", {}).get("id")
        event_type = data.get("event")

        print(f"Processing event {event_type} for meeting {meeting_id}...")

        # TranscriptReadyイベントの時のみ処理
        if event_type != "TranscriptReady":
            print(f"Skipping event type: {event_type}")
            return "OK", 200

        headers = {"x-api-key": TLDV_API_KEY}
        
        # 1. Transcript取得
        transcript_res = requests.get(f"{BASE_URL}/meetings/{meeting_id}/transcript", headers=headers)
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
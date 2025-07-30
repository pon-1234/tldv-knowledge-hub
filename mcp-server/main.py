import os
from fastapi import FastAPI, HTTPException, Query
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

app = FastAPI()

# 環境変数からAPIキーを取得
TLDV_API_KEY = os.environ.get("TLDV_API_KEY")
BASE_URL = "https://pasta.tldv.io/v1alpha1"

# リトライ戦略を設定したセッションを作成
def create_retry_session():
    session = requests.Session()
    retry = Retry(
        total=3,
        read=3,
        connect=3,
        backoff_factor=0.3,
        status_forcelist=(500, 502, 503, 504),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    return session

@app.get("/")
def read_root():
    """
    ヘルスチェック用のエンドポイント
    """
    return {"status": "ok"}

@app.get("/list_meetings")
def list_meetings(
    participants: list[str] = Query(None, description="参加者のメールアドレスリスト"),
    startDate: str = Query(None, description="検索開始日 (YYYY-MM-DD)")
):
    """
    指定された条件でtl;dvの会議リストを取得する。
    """
    if not TLDV_API_KEY:
        raise HTTPException(status_code=500, detail="TLDV_API_KEY is not configured.")

    headers = {"x-api-key": TLDV_API_KEY}
    params = {
        "participants": participants,
        "startDate": startDate,
    }
    
    session = create_retry_session()
    
    try:
        response = session.get(f"{BASE_URL}/meetings", headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# tldv Knowledge Hub

## 概要
オンライン会議プラットフォーム **tl;dv** から送信される Webhook を受け取り、GCP 上で処理するパイプラインのソースコードです。本リポジトリでは、Cloud Functions Gen2 (`functions/ingest`) が Webhook エントリポイントとして動作し、Pub/Sub 経由で後続の処理へイベントを配信します。

## Webhook 設定手順

### 1. 公開 URL
Cloud Functions デプロイ後に自動生成される **公開 URL** を tl;dv の Webhook 設定に登録します。

```
https://asia-northeast1-proj-tldv-knowledge.cloudfunctions.net/ingest
```

> ※ Cloud Run の内部 URL (`*.a.run.app`) では認証トークンが必須のため **401** になります。

### 2. 署名シークレット (tldv-signature)
セキュリティ確保のため、tl;dv は `tldv-signature` ヘッダーに固定値を載せてリクエストを送信します。本関数ではヘッダー値と Secret Manager 上の `tldv_signing_secret` が完全一致する場合のみ処理します。

#### シークレットの登録/更新
```bash
# 新しいシークレット値を登録（バージョン追加）
echo -n '5Ci7Fyon@qsuq0KiRNAcPz' | \
  gcloud secrets versions add tldv_signing_secret --data-file=-
```

#### シークレットを Cloud Functions へ注入してデプロイ
```bash
gcloud functions deploy ingest \
  --region=asia-northeast1 \
  --runtime=python312 \
  --source=functions/ingest \
  --entry-point=main \
  --trigger-http \
  --allow-unauthenticated \
  --set-secrets="TLDV_SIGNING_SECRET=tldv_signing_secret:latest" \
  --set-env-vars="GCP_PROJECT=proj-tldv-knowledge"
```

### 3. 動作確認
署名ヘッダーと最小限のペイロードを付与して 200 が返ることを確認します。

```bash
SECRET=$(gcloud secrets versions access latest --secret=tldv_signing_secret)

curl -v -X POST \
  -H "Content-Type: application/json" \
  -H "tldv-signature: $SECRET" \
  -d '{
        "event": "meeting.created",
        "data": { "id": "abc123" }
      }' \
  https://asia-northeast1-proj-tldv-knowledge.cloudfunctions.net/ingest
# -> HTTP/2 200  Event processed
```

### 4. Cloud Logging での確認
```
resource.type="cloud_function" "Published event"
```
が出力されていれば、Pub/Sub パブリッシュまで成功しています。

---
## トラブルシューティング 早見表
| 症状 | 原因 | 対処 |
|------|------|------|
| 401 Missing signature | `tldv-signature` ヘッダー欠如 | tl;dv または curl でヘッダーを付与 |
| 401 Invalid signature | シークレット不一致 | Secret Manager の値と tl;dv 側設定を揃える |
| 400 Invalid payload | `event` / `data.id` が欠如 | 正しい JSON を送信 |
| 500 Internal Server Error | `GCP_PROJECT` 未設定など Pub/Sub publish 失敗 | `--set-env-vars GCP_PROJECT=<your-project>` を設定 |

---
## ディレクトリ構成 (抜粋)
```
functions/ingest/  # Cloud Functions (Python 3.12)
├─ main.py         # Webhook ハンドラ
terraform/         # インフラコード (予定)
...
```

---
今後の更新方針や詳細仕様は `DEVELOPMENT_GUIDE.md` を参照してください。

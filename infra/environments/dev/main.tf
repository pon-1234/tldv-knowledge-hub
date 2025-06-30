provider "google" {
  project = "proj-tldv-knowledge"
  region  = "asia-northeast1"
}

# Secret Managerに必要なAPIキーを格納
resource "google_secret_manager_secret" "tldv_api_key" {
  secret_id = "tldv_api_key"
  replication {
    auto {}
  }
}
# 他のキー（OPENAI_API_KEY, NOTION_API_TOKENなど）も同様に作成

# Pub/SubトピックとDLQ
resource "google_pubsub_topic" "dlq" {
  name = "tldv.dlq"
}

resource "google_pubsub_topic" "main_topic" {
  name = "tldv.meeting-events"
}

# Cloud Functionsが使用するサービスアカウント
resource "google_service_account" "functions_sa" {
  account_id   = "sa-tldv-functions"
  display_name = "Service Account for Cloud Functions"
}

# BigQueryデータセット
resource "google_bigquery_dataset" "knowledge_ds" {
  dataset_id = "knowledge_ds"
  location   = "asia-northeast1"
}

# BigQueryテーブル（スキーマは後から定義も可能）
resource "google_bigquery_table" "meetings" {
  dataset_id = google_bigquery_dataset.knowledge_ds.dataset_id
  table_id   = "meetings"
  # ... schema定義 ...
}
# transcripts, highlightsテーブルも同様に作成 
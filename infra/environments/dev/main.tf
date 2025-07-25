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

resource "google_bigquery_table" "transcripts" {
  dataset_id = google_bigquery_dataset.knowledge_ds.dataset_id
  table_id   = "transcripts"
  time_partitioning {
    type  = "DAY"
    field = "inserted_at"
  }
  schema = file("../../../docs/schemas/transcripts.json")
}

resource "google_bigquery_table" "highlights" {
  dataset_id = google_bigquery_dataset.knowledge_ds.dataset_id
  table_id   = "highlights"
}

# fetcher Function (Terraform管理)
resource "google_cloudfunctions2_function" "fetcher" {
  name     = "fetcher"
  location = "asia-northeast1"

  build_config {
    runtime     = "python312"
    entry_point = "main"
    source {
      storage_source {
        bucket = google_storage_bucket.source_bucket.name
        object = google_storage_bucket_object.source_archive.name
      }
    }
  }

  service_config {
    max_instance_count = 1
    min_instance_count = 0
    available_memory   = "256Mi"
    timeout_seconds    = 60
    environment_variables = {
      TLDV_API_KEY = "bd00582b-76d9-457d-9624-f55e798e0afd" # ★ 直接値を設定
    }
    service_account_email = google_service_account.functions_sa.email
  }

  event_trigger {
    trigger_region = "asia-northeast1"
    event_type     = "google.cloud.pubsub.topic.v1.messagePublished"
    pubsub_topic   = google_pubsub_topic.main_topic.id
    retry_policy   = "RETRY_POLICY_RETRY"
  }
}

# ソースコードをアップロードするためのGCSバケット
resource "google_storage_bucket" "source_bucket" {
  name     = "source-bucket-for-fetcher"
  location = "asia-northeast1"
}

data "archive_file" "source_archive" {
  type        = "zip"
  source_dir  = "../../../functions/fetcher"
  output_path = "/tmp/fetcher.zip"
}

resource "google_storage_bucket_object" "source_archive" {
  name   = "fetcher.zip"
  bucket = google_storage_bucket.source_bucket.name
  source = data.archive_file.source_archive.output_path
}

# Pub/SubからFunctionを起動するためのIAM設定
data "google_project" "project" {}

resource "google_project_iam_member" "pubsub_token_creator" {
  project = data.google_project.project.project_id
  role    = "roles/iam.serviceAccountTokenCreator"
  member  = "serviceAccount:service-${data.google_project.project.number}@gcp-sa-pubsub.iam.gserviceaccount.com"
}

resource "google_cloud_run_service_iam_member" "fetcher_invoker" {
  location = google_cloudfunctions2_function.fetcher.location
  project  = google_cloudfunctions2_function.fetcher.project
  service  = google_cloudfunctions2_function.fetcher.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.functions_sa.email}"
} 
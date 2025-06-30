# プロジェクト実装計画 Issueリスト

このファイルは、プロジェクトの実装計画を元に作成されたGitHub Issueのテンプレートです。
各セクションをコピーして、新しいIssueを作成してください。

---

## フェーズ1: データパイプラインの基盤構築 (Epic 01-03)

---

### **[EPIC-01] 基盤構築 (Foundation & IaC)**

#### Issue: `[EPIC-01] GCPプロジェクトと基本APIの有効化`
**タスク:**
- `proj-tldv-knowledge` プロジェクトを作成する。
- 課金を有効化する。
- gcloud CLIで必要なAPI（Cloud Functions, Pub/Sub, BigQuery, Secret Manager, etc.）を有効化するスクリプトを作成する。

---
#### Issue: `[EPIC-01] GitHubリポジトリとWorkload Identity Federation設定`
**タスク:**
- `scribe` リポジトリを初期化し、仕様書通りのディレクトリ構成を作成する。
- GitHub ActionsからGCPへ安全に認証するためのWorkload Identity Federation (WIF) を設定する。
- CI/CDの基本となる `ci-cd.yaml` の骨子を作成する。

---
#### Issue: `[EPIC-01] Terraformによるコアインフラの定義`
**タスク:**
- TerraformでGCPプロバイダとバックエンド（GCS）を設定する。
- Service Account (`sa-tldv-functions`) を作成する。
- Secret Managerで各種APIキーを格納するSecretリソースを定義する（値は手動で投入）。
- Pub/Subトピック (`tldv.meeting-events`) とデッドレターキュー (`tldv.dlq`) を作成する。
- BigQueryデータセット (`knowledge_ds`) を作成する。

---
### **[EPIC-02] データインジェストパイプライン (Ingestion Pipeline)**

#### Issue: `[TDD] [EPIC-02] ingest Function: HMAC署名検証ロジック`
**タスク:**
- **1. テスト作成 (Red):**
    - `tests/test_ingest.py` を作成する。
    - **テストケース:** (a) 正常な署名、(b) 不正な署名、(c) 署名なし、の3パターンでリクエストを模倣し、それぞれ期待するHTTPステータスコード（200 or 401）が返ることをアサートするテストを書く。
- **2. 最小限の実装 (Green):**
    - `functions/ingest/main.py` に、上記テストをパスするための最小限の署名検証ロジックを実装する。
- **3. リファクタリング (Refactor):**
    - テストが通る状態を維持しながら、検証ロジックを独立したヘルパー関数に切り出すなど、可読性を向上させる。

---
#### Issue: `[TDD] [EPIC-02] ingest Function: Pub/Subへのイベント発行`
**タスク:**
- **1. テスト作成 (Red):**
    - `google-cloud-pubsub` の `PublisherClient` をモック（`unittest.mock.patch`）する。
    - **テストケース:** 正常なリクエストを受け取った際に、`publisher.publish` が期待される引数（トピックパス、データ、属性）で呼び出されることを確認するテストを書く。
- **2. 最小限の実装 (Green):**
    - `main.py` に、テストをパスするためのPub/Sub発行ロジックを実装する。
- **3. リファクタリング (Refactor):**
    - エラーハンドリングを追加・改善し、コードの堅牢性を高める。

---
#### Issue: `[EPIC-02] CI/CDによるingest Functionの自動デプロイ`
**タスク:**
- `ci-cd.yaml` に `ingest` Functionをデプロイするジョブを追加する。
- Secret Managerから `TLDV_SIGNING_SECRET` を環境変数としてマウントする設定を行う。
- `main` ブランチへのpushで自動デプロイが成功することを確認する。

---
### **[EPIC-03] データ永続化パイプライン (Persistence Pipeline)**

#### Issue: `[EPIC-03] BigQueryテーブルスキーマの定義と作成`
**タスク:**
- `meetings`, `transcripts`, `highlights` の3つのテーブルのDDLをSQLファイルとして作成する。
- DDLにはパーティショニングとクラスタリングの設定を含める。
- Terraformまたは `bq` CLIでテーブルを作成する。

---
#### Issue: `[TDD] [EPIC-03] fetcher Function: APIレスポンスのデータ変換`
**タスク:**
- **1. テスト作成 (Red):**
    - tl;dv APIのサンプルレスポンス（JSONファイル）を用意する。
    - **テストケース:** サンプルJSONを読み込み、BigQueryのテーブルスキーマに合致した辞書のリストに正しく変換されることをアサートするテストを書く。
- **2. 最小限の実装 (Green):**
    - `functions/fetcher/main.py` に、テストをパスするためのデータ変換ロジックを実装する。
- **3. リファクタリング (Refactor):**
    - データ変換ロジックを独立した関数に切り出し、型ヒントを付けて可読性を向上させる。

---
#### Issue: `[TDD] [EPIC-03] fetcher Function: 外部APIとBQクライアントの連携`
**タスク:**
- **1. テスト作成 (Red):**
    - `requests.get` と `bigquery.Client` をモックする。
    - **テストケース:** Pub/Subイベントをトリガーに、(a) `requests.get` が正しいURLとヘッダーで呼び出され、(b) `bq_client.insert_rows_json` が変換後のデータと共に呼び出されることを確認するテストを書く。
- **2. 最小限の実装 (Green):**
    - `main.py` のメイン処理として、APIクライアントとBQクライアントを呼び出すロジックを実装し、テストをパスさせる。
- **3. リファクタリング (Refactor):**
    - API呼び出しやBQ挿入部分のエラーハンドリング（リトライ処理など）を強化する。

---
#### Issue: `[EPIC-03] CI/CDによるfetcher Functionの自動デプロイ`
**タスク:**
- `ci-cd.yaml` に `fetcher` Functionをデプロイするジョブを追加する。
- トリガーを `tldv.meeting-events` トピックに設定する。
- 必要なIAMロール（BigQueryデータ編集者など）がSAに付与されていることを確認する。

---
## フェーズ2: ナレッジ活用機能の実装 (Epic 04-07)

---
### **[EPIC-04] LLMによるナレッジ生成と外部ツール連携 (Knowledge Generation)**

#### Issue: `[TDD] [EPIC-04] summarizer Function: LLMプロンプト生成`
**タスク:**
- **1. テスト作成 (Red):**
    - **テストケース:** サンプルの文字起こしテキストと固有名詞リストを入力として与え、期待する構造（システムプロンプト、ユーザープロンプト）のプロンプト文字列が生成されることを確認するテストを書く。
- **2. 最小限の実装 (Green):** プロンプトを組み立てるロジックを実装する。
- **3. リファクタリング (Refactor):** プロンプトテンプレートを外部ファイルに分離し、管理しやすくする。

---
#### Issue: `[TDD] [EPIC-04] summarizer Function: 外部API連携（Notion/Asana/Slack）`
**タスク:**
- **1. テスト作成 (Red):**
    - 各APIクライアント（Notion, Asana, Slack）をモックする。
    - **テストケース:** LLMのサンプルレスポンス（JSON）を入力とし、各APIクライアントのメソッドが期待するペイロードで呼び出されることを確認するテストをそれぞれ書く。
- **2. 最小限の実装 (Green):** 各APIを呼び出すロジックを実装し、テストをパスさせる。
- **3. リファクタリング (Refactor):** 各APIクライアントを責務ごとにクラスとして分離し、コードの見通しを良くする。

---
### **[EPIC-05] 検索バックエンド API (Search Backend)**

#### Issue: `[EPIC-05] Embedding生成パイプラインの構築`
**タスク:**
- BigQueryの `transcripts` テーブルに `embedding` カラム（VECTOR型）を追加する。
- 新規データ挿入をトリガーに、Vertex AI Embedding APIを呼び出してテキストのベクトルデータを生成し、`embedding` カラムを更新するバッチ処理（Cloud Function or Workflow）を実装する。

---
#### Issue: `[TDD] [EPIC-05] search-api: 検索クエリ構築ロジック`
**タスク:**
- **1. テスト作成 (Red):**
    - **テストケース:** ユーザーからの検索クエリ（例: "来週のタスク"）を入力とし、BigQueryの `VECTOR_SEARCH` や `SEARCH` 関数を含んだ、期待通りのSQLクエリ文字列が生成されることを確認するテストを書く。
- **2. 最小限の実装 (Green):** SQLを組み立てるロジックを実装する。
- **3. リファクタリング (Refactor):** SQLインジェクション対策を施し、クエリ構築の安全性を高める。

---
#### Issue: `[TDD] [EPIC-05] search-api: APIエンドポイントの振る舞い`
**タスク:**
- **1. テスト作成 (Red):**
    - FastAPIの `TestClient` やFlaskのテスト機能を使用する。
    - **テストケース:** `/search/vector` エンドポイントにリクエストを送り、BigQueryクライアントをモックしてサンプルデータを返却させ、期待するJSONレスポンスとステータスコードが返ることを確認するテストを書く。
- **2. 最小限の実装 (Green):** エンドポイントのロジックを実装する。
- **3. リファクタリング (Refactor):** リクエストのバリデーションやエラーレスポンスの形式を共通化する。

---
#### Issue: `[EPIC-05] Cloud Run (search-api) のセットアップとデプロイ`
**タスク:**
- FastAPIまたはFlaskでAPIサーバーのひな形を作成する。
- Dockerfileを作成し、Cloud RunにデプロイするCI/CDパイプラインを構築する。

---
### **[EPIC-06] 検索フロントエンド UI (Search Frontend)**

#### Issue: `[EPIC-06] Next.jsとTailwind CSSによるUIプロジェクトのセットアップ`
**タスク:**
- `frontend` ディレクトリにNext.jsプロジェクトを作成する。
- Tailwind CSSを導入し、基本的なレイアウトコンポーネントを作成する。

---
#### Issue: `[EPIC-06] 検索UIコンポーネントの実装`
**タスク:**
- 検索キーワードを入力するフォームと、検索種別（意味/キーワード）を選択するUIを実装する。
- 検索ボタンが押されたらバックエンドAPIを呼び出すイベントハンドラを実装する。

---
#### Issue: `[EPIC-06] 検索結果表示コンポーネントの実装`
**タスク:**
- APIからのレスポンスを整形し、会議名、発言者、発言内容、元のtl;dvへのリンクなどを一覧表示する。
- 検索キーワードをハイライト表示する機能を実装する。

---
#### Issue: `[EPIC-06] Vercelへのフロントエンド自動デプロイ設定`
**タスク:**
- GitHubリポジトリとVercelを連携させる。
- `main` ブランチへのpushで自動的に本番環境へデプロイされるように設定する。

---
### **[EPIC-07] 運用・監視体制の構築 (Operations & Monitoring)**

#### Issue: `[EPIC-07] Cloud Monitoringダッシュボードの構築`
**タスク:**
- 各Cloud Functionの実行時間、エラー率、実行回数を表示するウィジェットを追加する。
- Pub/Subの未配信メッセージ数（DLQ含む）を監視する。
- BigQueryのスロット使用率とクエリコストを可視化する。

---
#### Issue: `[EPIC-07] コスト管理のためのBudget Alert設定`
**タスク:**
- GCPプロジェクト全体で月額予算（例: 50 USD）を設定する。
- 予算の50%, 90%, 100%に達した時点で、開発チームのSlackチャンネルに通知が飛ぶように設定する。

---
#### Issue: `[EPIC-07] 単体テストとカバレッジレポートの導入`
**タスク:**
- `pytest` と `pytest-cov` を導入する。
- 各Functionのコアロジックに対する単体テストを実装する。
- CI実行時にテストカバレッジを計測し、一定の閾値を下回らないようにする。 
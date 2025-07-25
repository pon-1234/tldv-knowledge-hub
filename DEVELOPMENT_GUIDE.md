### **tl;dv × Project Knowledge Platform ― 仕様書（v1.2 / 2025-07-25 / 方針変更版）**

**はじめに**
本ドキュメントは、プロジェクトで発生するオンライン会議の情報を一元化し、活用可能にするナレッジプラットフォームの仕様を定義するものです。tl;dvを起点としたデータパイプラインをGCP上に構築し、**まずは会議の文字起こしとメタデータをBigQueryへ確実に蓄積する**ことを最優先の目的とします。

### **1. 背景・目的**

*   **背景:** プロジェクト横断で発生するオンライン会議の内容（録画、文字起こし、議事録）が、ツール毎に散在し、情報の検索性や再利用性が低下している。
*   **目的:** tl;dv APIとGCPを中核技術として利用し、以下の実現を目指す。
    1.  **ナレッジの一元化:** 会議の文字起こしやメタデータをBigQueryに集約し、**プロジェクト横断でのデータ分析基盤を構築する。**
    2.  **拡張性と運用性:** イベント駆動アーキテクチャを採用し、将来的な機能（LLMによる要約、全文検索など）の拡張が容易で、かつ低運用コストなシステムを構築する。

### **2. 成果物（ゴール）**

| # | 成果物 | 完了条件 |
| :--- | :--- | :--- |
| 1 | GCPインフラ | TerraformによるIaCで、開発・本番環境のインフラが再現可能である。 |
| 2 | データパイプライン | 会議終了後、文字起こしと会議メタデータがBigQueryに格納される。 |
| 3 | MCP Server (Cloud Run) | 特定参加者の会議一覧取得など、バッチ処理用のAPIがデプロイされている。 |
| 4 | データ可視化 | Looker Studioなどを用いて、会議参加率や総時間などのKPIが可視化されている。 |
| 5 | 監視 & コスト管理 | Cloud Monitoringで主要メトリクスが可視化され、予算アラートが設定されている。 |

### **3. ハイレベル構成図**

```mermaid
graph TD
    subgraph "Data Source & Trigger"
        A[tl;dv Webhook] -->|MeetingReady<br>TranscriptReady| B(Cloud Functions: ingest)
    end

    subgraph "GCP Core (proj-tldv-knowledge)"
        B -- Publishes --> C(Pub/Sub: tldv.meeting-events)
        C --> D(Cloud Functions: fetcher)

        D -->|Transcript JSON| E[BigQuery: transcripts]
        D -->|Meetings JSON|  F[BigQuery: meetings]

        subgraph "Optional API Layer"
            G(MCP Server<br>(Cloud Run))
            G -- REST --> tlv(tl;dv Public API)
        end
        G -- "list_meetings?participants=..." --> E
    end
```
*<p align="center">図1: システム全体のアーキテクチャ概要</p>*

### **4. リポジトリ構成**

```
root/
├── .github/workflows/
│   └── ci-cd.yaml         # CI/CDパイプライン
├── infra/                 # Terraform (GCPリソース管理)
│   ├── modules/
│   └── environments/
│       ├── dev/
│       └── prd/
├── functions/             # Cloud Functions ソースコード
│   ├── ingest/            # Webhook受信 & Pub/Sub発行
│   └── fetcher/           # tl;dv API取得 & BigQuery格納
├── mcp-server/            # MCP Server (Cloud Run) ソースコード (予定)
└── docs/
    ├── architecture.md    # 本ドキュメント
    └── schemas/           # BigQueryのスキーマ定義
```

### **5. 主要コンポーネント設計**

#### **5.1. GCPリソース**
| リソース | ID / 名称 | 設計・設定のポイント |
| :--- | :--- | :--- |
| プロジェクト | `proj-tldv-knowledge` | リージョンは `asia-northeast1` (東京) に統一。 |
| Service Account | `sa-tldv-functions` | 各Function/Runが必要とする最小権限を付与。 |
| Secret Manager | `tldv-api-key` | tl;dvのAPIキーを管理。 |
| Pub/Sub | `tldv-meeting-events` | メッセージ保持期間7日。デッドレターキュー(DLQ)を設定。 |
| BigQuery | `knowledge_ds` | `meetings`, `transcripts`テーブル。`start_time`や`inserted_at`で時間分割パーティションを設定。 |
| Cloud Functions | `ingest`, `fetcher` | Gen2, Python 3.12。冪等性を担保。Pub/SubトリガーのIAM権限設定に注意。 |
| Cloud Run | `mcp-server` | 過去データのバッチ取得や特定条件でのAPIリクエストに使用。 |

#### **5.2. 外部API & 秘匿情報**
| サービス | 用途 | Secret名 |
| :--- | :--- | :--- |
| tl;dv API | 文字起こし・メタデータ取得 | `TLDV_API_KEY` |
| tl;dv Webhook | イベント受信 | `TLDV_SIGNING_SECRET` |

### **6. フェーズ別タスク & DoD (Definition of Done)**

#### **1️⃣ データパイプライン構築 (Day 1-3)**
| ID | Task | DoD |
| :--- | :--- | :--- |
| 1-1 | GCP & Terraform基盤構築 | Secret Manager, Pub/Sub, BigQuery (`meetings`, `transcripts`) などのコアリソースがTerraformで作成済み。 |
| 1-2 | `ingest` & `fetcher` 開発 | tl;dv Webhookをトリガーに、会議メタデータと文字起こしデータがBigQueryの各テーブルに格納される。 |
| 1-3 | CI/CD設定 | `main`ブランチへのPushで`ingest`, `fetcher`が自動デプロイされる。 |

#### **2️⃣ データ活用基盤の構築 (Day 4-7)**
| ID | Task | DoD |
| :--- | :--- | :--- |
| 2-1 | `MCP Server` 開発・デプロイ | 参加者や期間を指定してtl;dv APIから会議リストを取得するAPIをCloud Runで実装・デプロイする。 |
| 2-2 | 過去データ取込 | `MCP Server`を使い、過去の全会議データをBigQueryに一括でロードする。 |
| 2-3 | データ可視化 | Looker StudioでBigQueryに接続し、参加者ごとの会議時間や発言量などのKPIを可視化するダッシュボードを作成する。 |
| 2-4 | バッチ処理設定 | Cloud Schedulerを使い、定期的に`MCP Server`を呼び出して差分データをBigQueryに連携する仕組みを構築する。 |

### **7. 将来的な拡張**
本システムの基盤の上に、将来的に以下の機能を追加開発することが可能です。
*   **LLMによる要約・タスク生成:** `summarizer` Functionを復活させ、BigQueryの新規データをトリガーに議事録要約やTODOリストを生成し、NotionやAsanaに連携する。
*   **全文・ベクトル検索:** BigQueryのデータからEmbeddingを生成するパイプラインを構築し、意味検索が可能な`search-api` (Cloud Run) とフロントエンドUIを開発する。

### **8. CI/CD**
GitHub Actionsを利用し、`main`ブランチへのPushをトリガーにテストとデプロイを自動化します。

```yaml
# .github/workflows/ci-cd.yaml (抜粋)
# ...
    strategy:
      matrix:
        function: [ingest, fetcher] # 対象を絞る
# ...
```

### **9. テスト方針**
*   **単体テスト:** `pytest`を使用。各Functionのビジネスロジックを網羅。
*   **結合テスト:** ローカルエミュレータとサンドボックスGCPプロジェクトを使用し、`ingest`から`fetcher`までの流れを検証。
*   **E2Eテスト:** tl;dvでテスト会議を実施後、BigQueryにデータが正しく格納されるかを確認する。

### **10. リスクと対策**
| リスク分類 | 具体的なリスク内容 | 対策 |
| :--- | :--- | :--- |
| **外部API** | ・API仕様変更による機能停止<br>（例: Webhookペイロードの構造変更）<br>・レートリミット超過 | ・APIクライアントを疎結合に実装し、変更時の影響範囲を限定。<br>・指数バックオフ付きのリトライ処理を実装。 |
| **データ品質** | ・文字起こしの誤認識<br>・参加者名のtypoや表記揺れ | ・パイプラインの後段（BigQuery Viewやdbt）でデータクレンジングや正規化を行う処理を追加検討。 |
| **GCP/インフラ** | ・IAM権限設定の不足によるサービス間連携の失敗 | ・TerraformでIAMポリシーをコード管理する。<br>・Pub/Subトリガーには`run.invoker`と`iam.serviceAccountTokenCreator`ロールが必要。 |

---
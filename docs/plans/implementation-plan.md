# PoC Renovater AGY - 総合実装計画書 (Master Implementation Plan)

本書は、PoC Renovater AGY アプリケーション全体の必要機能を洗い出し、フロントエンド・バックエンド・AIエージェント・インフラのすべての観点を網羅した総合的な実装計画書である。
（※直近のアーキテクチャ見直しによる「Job Tracker」および「Human in the loop」機能も包含する）

---

## 1. アプリケーション全体機能要件 (Features Breakdown)

### 1.1 フロントエンド (Frontend / Web UI)
**ユーザー体験(UX)の提供と、AIプロセスの可視化・介入を行う層。**
- **認証・テナント管理**:
  - ログイン/ログアウト画面 (Firebase Auth / Auth0 等の連携)
  - テナント切り替え機能 (B2B SaaS要件)
- **ダッシュボード**:
  - 全PoCプロジェクトの一覧表示（ステータス、進行状況、プレビューURLのカード表示）
- **PoC作成・入力 (Input)**:
  - 既存ソースコード（ZIP形式）のアップロード機能
  - または既存 GitHub リポジトリURLの連携入力
- **AIとの対話画面 (Chartering Chat)**:
  - アップロードされたソースを元にしたAIとの対話型インターフェース
  - チャットストリーミング表示と、要件定義書（Charter）のプレビュー
- **ジョブトラッカー＆オブザーバビリティ (Job Tracker & HITL)**: 🌟新規追加
  - 15ステップのAI実行パイプラインのリアルタイム・ツリー表示
  - `FAILED` ジョブ発生時のトラブルシューティング・モーダル（エラー詳細と再試行/キャンセルボタン）
  - 環境変数入力や、AIコード承認のためのヒューマン介入（BLOCKED）フォーム
- **デプロイメント・結果確認**:
  - 生成されたコードの PR リンク一覧
  - 発行されたプレビュー環境 (Webアプリケーション) のインライン表示(iframe)またはリンク

### 1.2 バックエンド API (Backend / Core API)
**フロントエンドからのリクエストを処理し、DBと状態を同期させるAPI層。**
- **テナント・プロジェクト管理 API**:
  - `GET /tenants/{tenant_id}/agents` (PoC一覧)
  - `POST /tenants/{tenant_id}/agents` (PoC新規作成・アップロード受付)
- **チャット・ストリーミング API**:
  - `POST /tenants/{tenant_id}/agents/{agent_id}/chat` (要件定義のための対話)
- **ジョブ管理 API (Job Management)**: 🌟新規追加
  - `GET /jobs` (非同期ジョブの進行状況取得)
  - `POST /jobs/{job_id}/retry` (エラーになったジョブの再実行)
  - `POST /jobs/{job_id}/cancel` (ジョブのキャンセルとロールバック)
- **Webhook リスナー**:
  - GitHub Webhook 受信（PRマージ、CI/CD完了の検知）

### 1.3 非同期ワーカー・AIエージェント (Event-Driven Workers)
**Pub/Sub 等を介してバックグラウンドで自律的に動く「頭脳」と「腕」の層。**
- **RAG / プレ解析ワーカー**:
  - アップロードされたソースコードの解凍、不要ファイル除外
  - ベクトルDB (Embedding) へのインデックス化 (`CODE_EMBEDDING_INGESTION`)
  - LLM（Vertex AI）による初期構造解析と要約
- **GitHub 連携ワーカー**:
  - リポジトリの作成・初期化
  - 抽出されたタスク群に基づく Issue の一括起票
- **実装エージェント (Coding Agent / Sandbox)**:
  - Issue に基づき、Sandbox環境 (Cloud Run Jobs / Firecracker) をプロビジョニング
  - LLMを活用してコード差分（Diff）の生成とテスト実行
  - GitHubへのPushと、Pull Requestの自動作成
- **CI/CD・デプロイ連携ワーカー**:
  - PRマージ後のビルド状況追跡
  - プレビュー環境のデプロイとヘルスチェック (`HEALTH_CHECK_VERIFICATION`)

### 1.4 インフラ・データ基盤 (Infrastructure / Data)
- **DB (Cloud SQL / PostgreSQL)**: Agent, Job, Message 等の永続化
- **Storage (Cloud Storage)**: アップロードされたZIPファイル、中間生成物の保存
- **メッセージング (Pub/Sub)**: 各種ワーカーを駆動する非同期イベントキュー
- **実行環境**: Cloud Run (API / Worker)、Sandbox 用の隔離コンテナ環境

---

## 2. 実装フェーズとロードマップ (Implementation Phases)

### Phase 1: MVP基盤の再構築 (Core Infrastructure & DB)
*目標: バックエンドとDB設計をエンタープライズ仕様（マルチテナント＋ジョブ管理）に刷新する。*
- [x] Hexagonal + Agent-centric アーキテクチャの定義
- [x] Cloud SQL (PostgreSQL) への対応とリポジトリ実装
- [x] Job管理モデル（15のステップ）とエラーリカバリのDB設計
- [ ] バックエンド API（FastAPI）の Job管理エンドポイント (`/retry`, `/cancel`) の実装

### Phase 2: 非同期ワーカーとパイプラインの細分化 (Event-Driven Pipeline)
*目標: 既存の大きな「実装」ブロックを、15個の Job Handler に分割し、エラー発生時に適切に止まるようにする。*
- [ ] Pub/Sub イベント購読ハンドラを JobType ごとに細分化。
- [ ] LLM (Vertex AI) や GitHub API の呼び出しエラーをキャッチし、`error_details` (JSON) 化して Job を `FAILED` に遷移させるロジック実装。
- [ ] 各ステートにおける冪等性 (Idempotency) の担保実装。

### Phase 3: フロントエンドと Job Tracker の実装 (Frontend Dashboard)
*目標: ユーザーがアプリケーション全体の進行状況を把握できる画面を提供する。*
- [ ] PoC 一覧ダッシュボード画面の構築 (React / Next.js)。
- [ ] ZIPアップロードから開始される新規PoC作成UIの実装。
- [ ] **Job Tracker UI**: 15ステップの進行状況をリアルタイム (SSE/Polling) で表示するコンポーネント。
- [ ] **Troubleshooting Modal**: エラー時に再試行(Retry)やキャンセルが行えるポップアップの実装。

### Phase 4: 人間とAIの対話・協調機能 (Chartering & HITL)
*目標: 単なる自動生成ではなく、ユーザーの意図を反映させるインタラクティブな機能を入れる。*
- [ ] Charter Agent とのチャットインターフェース（ストリーミングUI）の実装。
- [ ] デプロイ前の環境変数入力や、PR作成前の AIコード承認（Approve）といった `BLOCKED` ジョブのブロック解除UIの実装。

### Phase 5: 高度なインフラ統合と Sandbox 連携 (Advanced Operations)
*目標: 完全に独立した安全なコード実行環境と、本番運用に向けた連携を完成させる。*
- [ ] ソースコードの Vector DB インデックス化バッチ (`CODE_EMBEDDING_INGESTION`) 実装。
- [ ] Coding Agent 用の Sandbox 環境（Cloud Run Jobs）プロビジョニングと自動破棄 (`RESOURCE_CLEANUP`) の仕組み構築。
- [ ] GitHub App としてのWebhook連携 (CIの成功通知受け取り)。

---
## 3. 次のステップ（Next Action）
現在は **Phase 1** の「バックエンドAPIのJob管理エンドポイントの実装」および **Phase 2** の「非同期ワーカーのパイプライン細分化実装」が次の具体的な開発タスクとなります。

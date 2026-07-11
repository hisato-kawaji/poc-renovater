# PoC Foundry AGY - 実装計画書 (Job Tracker & HITL)

## 1. 全体コンセプト
今回のアーキテクチャ再設計に基づき、**「PoCパイプラインの可視化」**と**「エラーからの自己修復・手動再開 (Human in the loop)」**をアプリケーションのコア体験として実装します。
ブラックボックスになりがちなAI処理を15の細かいJobに分割し、ユーザーが常に手綱を握れるエンタープライズ対応のダッシュボードを構築します。

---

## 2. バックエンドで必要な機能 (Backend Features)

### 2.1 Job管理 API (REST / FastAPI)
- `GET /api/tenants/{tenant_id}/agents/{agent_id}/jobs`
  - ジョブ一覧とステータスの取得（トラッカー用）。
- `POST /api/tenants/{tenant_id}/agents/{agent_id}/jobs/{job_id}/retry`
  - `FAILED` または `CANCELED` なジョブを `PENDING` に戻し、Pub/Sub に再投入する。
- `POST /api/tenants/{tenant_id}/agents/{agent_id}/jobs/{job_id}/cancel`
  - 進行中・失敗したジョブをキャンセルし、必要に応じて `RESOURCE_CLEANUP` ジョブを発行する。

### 2.2 非同期ワーカー (Pub/Sub Event Handlers)
- 15個のジョブタイプ（`FILE_UPLOAD`, `CODE_GENERATION`, `WAIT_FOR_CI_CHECKS` 等）ごとのイベントハンドラを実装。
- **エラー処理の標準化**: 例外発生時、スタックトレースではなくユーザーが読める `error_details` (JSON) にパースしてDBに保存。
- **冪等性（Idempotency）の担保**: ジョブが再実行されても、同じIssueを二重に作ったり、リポジトリ作成で422エラーを出さないような実装。

### 2.3 外部システム連携強化 (Webhooks & Provisioning)
- **GitHub Webhook Handler**: CI (GitHub Actions) の成功/失敗を受信し、`WAIT_FOR_CI_CHECKS` ジョブを完了または失敗させるエンドポイント。
- **Sandboxプロビジョナー**: `SANDBOX_PROVISIONING` 時に Cloud Run Jobs などの使い捨てコンテナを起動・破棄するロジック。
- **シークレット管理**: ユーザー入力を受け付けて `WAIT_FOR_USER_SECRETS` のブロックを解除する機能。

---

## 3. フロントエンドで必要な機能 (Frontend Features)

### 3.1 リアルタイム・ジョブトラッカー (Pipeline Job Tracker)
- **UI要件**: 15ステップのジョブをツリー状または縦のプログレスステップとして表示。
- **ステータス表現**:
  - `PENDING` (待機中 - 灰色)
  - `RUNNING` (実行中 - 青色/スピナー)
  - `COMPLETED` (完了 - 緑色/チェック)
  - `FAILED` (失敗 - 赤色/警告アイコン)
  - `BLOCKED` (入力待ち - 黄色/ポーズアイコン)
- **通信**: SWRによるポーリング、または SSE (Server-Sent Events) によるリアルタイム更新。

### 3.2 トラブルシューティング・モーダル (Actionable Error Modal)
- `FAILED` なジョブをクリックすると右側パネル（またはモーダル）が開く。
- バックエンドから返ってきた `error_details`（例: "GitHub トークン権限不足"）と、推奨される**対処アクション**を表示。
- モーダル内に **[再試行 (Retry)]** と **[キャンセル (Cancel)]** ボタンを配置。

### 3.3 ヒューマン・イン・ザ・ループ (HITL) アプルーバル画面
- ジョブが `BLOCKED` (人間待ち) になった際にアクションを促すフォーム。
- **例1**: 環境変数（シークレット）の入力を求めるフォーム。
- **例2**: PR作成前に、AIが生成したコードのDiffをプレビューし、承認(Approve)させる画面。

### 3.4 テナント・オペレーション・ダッシュボード (Tenant Ops View)
- テナント全体のPoC稼働状況をサマリ表示。
- 「現在停止中 (FAILED/BLOCKED) のプロジェクト数」をアラート表示し、管理者が一括で状況を把握・介入できる機能。

---

## 4. 実装フェーズ計画

### Phase 1: DB基盤とAPIの整備 (現在地)
- [x] アーキテクチャのドキュメント更新 (Jobモデル、15ステップ定義)
- [x] DBリポジトリ (`AgentRepository`) への Job CRUD 実装
- [ ] バックエンド: REST API エンドポイント (`/jobs`, `/retry`, `/cancel`) の実装

### Phase 2: ワーカーの分割とステートマシン再構築
- [ ] 既存のバックエンドロジックを、15の個別 Job ハンドラに分割。
- [ ] 各種外部API (GitHub, Vertex) 呼び出し時のエラーを捕捉し、`error_details` にマッピングする処理。
- [ ] Pub/Sub イベントによる状態遷移の実装。

### Phase 3: フロントエンド - Job Tracker実装
- [ ] React (Next.js 等) にて `PipelineTracker` コンポーネントの実装。
- [ ] `TroubleshootingModal` コンポーネント（Retry / Cancel バインディング）の実装。

### Phase 4: HITL と Webhook 統合
- [ ] GitHub Webhook 受信エンドポイントと CI待ち ジョブの結合。
- [ ] シークレット入力フォームと Diff アプルーバル画面の実装。

### Phase 5: 高度なインフラ統合
- [ ] RAG用の `CODE_EMBEDDING_INGESTION` ジョブの実装（ベクトルDB連携）。
- [ ] `SANDBOX_PROVISIONING` と `RESOURCE_CLEANUP` による安全なリソースライフサイクル管理。

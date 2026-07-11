# PoC Renovater (Antigravity Agent)

**PoC Renovater** は、Google Cloud が提供する Agentic AI 開発・実行基盤（ADK / LangGraph等）を用いて、ユーザーからアップロードされたPoC（Proof of Concept）コードを自律的に解析・改善・コンテナ化・デプロイまで行うシステムのデモ環境です。

現在、このシステム自体も **Google Antigravity**（AI Coding Assistant）によって自律的に開発が進められています。

## Architecture Overview

システムは **Hexagonal Architecture**（および クリーンアーキテクチャ）の思想を取り入れており、機能ごとのモジュール化とインフラ詳細（DB、ストレージ、GitHub等）の隠蔽を行っています。

### ディレクトリ構成

- `apps/api/` : バックエンドAPI (FastAPI, Python 3.12)
  - `app/domain/` : ドメイン層（エンティティや Repository の Interface）
  - `app/application/` : ユースケース層（各エージェントの呼び出しロジック、ビジネスルール）
  - `app/adapters/` : インフラストラクチャ層（Firestore、Cloud Storage、GitHub 等の外部連携実装）
  - `app/interface/http/` : プレゼンテーション層（FastAPIのルーティング設定）
- `apps/web/` : フロントエンド (Next.js 15, TypeScript, TailwindCSS)
- `packages/` : 共有ライブラリやスキーマ定義
- `infra/` : Terraform等を用いたインフラ構成管理（計画中）

## Features (Current & Planned)

### 現状実装されている機能 (MVP)
1. **Analyze**: ZIP形式でアップロードされたPoCを解凍し、Google Gemini 2.5 を使ってソースコード構造と意図を分析。
2. **Register**: 分析結果が規定のスコア（Charter）を満たしている場合、自動で新規GitHubリポジトリを作成し初期プッシュを実行。
3. **Plan**: リポジトリ構成を元に、コンテナ化(Dockerfile作成)やCI設定などの改善点（Issue）をプランニングしてGitHubに自動起票。
4. **Implement**: 対象Issueを解決するためのソースコード修正をAIエージェントが自動で行い、Pull Requestを作成。
5. **Review**: 作成されたPull Requestに対して、AI（Review Agent）がコードレビューを実施。
6. **Approve & Merge**: 人間の承認によってPRをマージ。

### 今後の拡張予定 (Roadmap)
- Charter Agentによるインタラクティブな要件定義（チャットUI）
- タイムアウト対策としての非同期ジョブキュー（Pub/Sub or Cloud Tasks）の導入
- GitHub Pull Request の Diff 表示やダッシュボード機能
- Terraform を用いた Cloud Run およびリソースの自動展開
- GitHub Webhook連携によるCI/CD自動実行

## Local Development

### 1. Backend (API) の起動

```bash
cd apps/api
# パッケージのインストール
uv pip install -r requirements.txt
# 開発サーバーの起動 (localhost:8000)
uv run uvicorn app.main:app --reload --port 8000
```

*※ 実行には `GOOGLE_GENAI_USE_VERTEXAI=1`、`GCS_UPLOAD_BUCKET` などの環境変数(`.env`)が必要です。*

### 2. Frontend (Web) の起動

```bash
cd apps/web
# パッケージのインストール
pnpm install
# 開発サーバーの起動 (localhost:3000)
pnpm dev
```

## Contributing
本リポジトリは Antigravity を用いた完全自動開発のデモ用です。IssueやPRの発行は Agent の自律ループによって行われますが、手動でのPull Requestも歓迎します。

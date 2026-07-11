# セットアップ手順（日本語）

PoC Renovater 開発環境を Claude Code 主導でセットアップするための手順書。
スラッシュコマンドはすべて `.claude/commands/` に定義されており、内容は `CLAUDE.md`（英語）からたどれる。

## 前提

- macOS（Darwin）
- Homebrew が入っていること
- GitHub の `poc-recycle` org の owner 権限を持つアカウントでログイン済み（`gh auth status` で確認）
- gcloud で `your.email@example.com`（または該当オーナーアカウント）でログイン済み（`gcloud auth list`）

## 全体像

```
[1] ローカルツール導入        →  /bootstrap-tools
[2] GCP プロジェクト初期化    →  /bootstrap-gcp
[3] Terraform で資源作成       →  /bootstrap-terraform plan → apply
[4] GitHub App 連携            →  /bootstrap-github
[5] MCP 確認                   →  /bootstrap-mcp
[6] 全体セルフチェック         →  /bootstrap-verify
```

各ステップとも、破壊的・課金が発生しうる操作は **明示的な確認プロンプト** が出ます。「yes」を打たない限り進みません。

---

## 1. ローカルツール導入

```
> /bootstrap-tools
```

`scripts/bootstrap-tools.sh` を呼び、不足している以下を Homebrew で入れる:

- `pnpm`（Next.js 15 用）
- `terraform`（`infra/` 用）
- `direnv`（`.envrc` で env を自動ロード）

完了後 direnv のシェルフック追加を案内するので、`~/.zshrc` に以下を追加して `direnv allow` を実行:

```sh
eval "$(direnv hook zsh)"
```

その後 `.envrc.example` を `.envrc` にコピーして `direnv allow`。

## 2. GCP プロジェクト初期化

```
> /bootstrap-gcp
```

実行内容:

1. アクティブな gcloud アカウントを確認。違っていたら停止して質問。
2. GCP プロジェクト（既定: `poc-renovater-<任意のサフィックス>`）を作成。
3. 課金アカウントをリンク（候補一覧から選択）。
4. 必要 API を有効化（`docs/planning.md` §14.1 のリスト全部）。
5. Terraform state 用 GCS バケット `gs://<project-id>-tfstate` を `asia-northeast1` に作成、バージョニング ON。
6. `.env` に `GOOGLE_CLOUD_PROJECT` と `TF_STATE_BUCKET` を書き込み。

**注意点**:
- 既に GCP プロジェクトが他用途で使われていても、このスクリプトでは **破壊しません**。
- `cursor-test-446907` のような既存プロジェクトを流用する場合は明示的にプロジェクト ID を再入力する設計になっています（誤操作防止）。

## 3. Terraform で資源作成

```
> /bootstrap-terraform plan      # まずプランだけ
> /bootstrap-terraform apply     # プラン確認後、明示確認で apply
```

`infra/` に並ぶ Terraform で以下を作る:

| ファイル | 作るもの |
|---|---|
| `apis.tf` | プロジェクト API 有効化（冪等） |
| `service_accounts.tf` | `sa-api` / `sa-deploy` / `sa-sandbox` / `sa-preview-runtime` |
| `storage.tf` | アップロード zip 用 GCS バケット（90日ライフサイクル） |
| `firestore.tf` | Firestore Native（`(default)` データベース） |
| `artifact_registry.tf` | Docker レジストリ `poc-renovater` |
| `secret_manager.tf` | `GITHUB_APP_PRIVATE_KEY` / `GITHUB_WEBHOOK_SECRET` / `ANTHROPIC_API_KEY` のシークレットコンテナ |

`terraform.tfvars` は `terraform.tfvars.example` をコピーして書き換えてください（バケット名は global unique 必須）。

apply するときはまずプラン全部を読み上げ、`yes` を打って初めて実行します。

## 4. GitHub App 連携

```
> /bootstrap-github
```

GitHub App の作成は **必ず Web UI から org owner が実施**（GitHub の監査トレイル要件）。このコマンドが代わりに作るのは:

- gh token のスコープ確認（不足なら `gh auth refresh -s admin:org,admin:org_hook,repo,workflow` を案内）
- org `poc-recycle` での admin 権限確認
- 作成済 App の **App ID / Installation ID / 秘密鍵パス / Webhook シークレット** を受け取って Secret Manager にアップロード
- `.env` に `GITHUB_APP_ID` / `GITHUB_APP_INSTALLATION_ID` を書き込み

**秘密鍵をリポジトリ内に置くと拒否されます**（`~/secrets/` のような場所に保管）。

権限・Webhook イベントの推奨値は `docs/planning.md` §10.1 を参照。

## 5. MCP 確認

```
> /bootstrap-mcp
```

`.mcp.json` に登録した Context7 と GitHub MCP の疎通確認:

- Context7: `nextjs` を resolve できるか
- GitHub: 任意の低リスク API（issue list 等）で 200 が返るか

GitHub MCP は env `GITHUB_TOKEN` を読みます。ローカル開発では PAT、本番では GitHub App Installation Token を渡してください。

## 6. 全体セルフチェック

```
> /bootstrap-verify
```

`scripts/bootstrap-verify.sh` を呼んで、CLI / 認証 / env / GCP リソース / GitHub / MCP の全項目を PASS/FAIL で表示。**完全に冪等**で何度実行しても OK。CI に組み込み可能（FAIL があれば exit 非 0）。

## 7. PR レビューを有効化（セッション内 loop）

PR レビューは **アクティブな Claude Code セッション内** で動かします（GitHub Actions ではありません）。役割を分けた **2 つの loop** を併走:

```text
/loop 12h /loop-pr-review       # 初回レビュー（半日 1 回スイープ）
/loop 5m  /loop-pr-discussion   # 議論進行 + approve 判定（5 分間隔）
```

- `loop-pr-review`: 未レビュー head の PR を見つけて `pr-reviewer` subagent (Opus) で verdict 投稿。SHA marker (`<!-- pr-reviewer: <sha> -->`) で重複排除
- `loop-pr-discussion`: 既レビュー PR について、author の返信や fix commit を見て threads を進行。小さな fix なら自動コミット、反論があれば再評価、全 thread 解決 + CI green なら `gh pr review --approve`（merge は人間）
- **緊急で即レビューしたい単発 PR は `/pr-review <PR#>`**（marker 無視で強制再評価）

cadence の調整・safety 制約は [`docs/policy/pr-review.md`](policy/pr-review.md) §3。

- cadence の調整は [`docs/policy/pr-review.md`](policy/pr-review.md) §3.2
- レビュー観点・観点追加手順: 同 §1 / §5
- Agent 定義: [`.claude/agents/pr-reviewer.md`](../.claude/agents/pr-reviewer.md)
- 単発でいますぐ再レビュー: `/pr-review <PR#>`
- スキップ: PR を draft にする or `skip-claude-review` ラベルを付ける or `.claude/scratch/STOP-PR-LOOP` ファイルを置く
- **セッションを終了するとループも止まる**（次回起動時に再度 `/loop ...` を打つ）

---

## 進めかた（Phase 開始）

セットアップが終わったら Phase 0 から実装に入ります。

```
> /phase-status         # 現在地確認
> /phase-start 0        # Phase 0 のタスクをロード
# ... 実装 ...
> /phase-verify 0       # DoD 突き合わせ
```

Phase の DoD は `docs/planning.md` §12 を読みます。各 Phase 完了で 1 PR を作る前提です。

## トラブルシュート

| 症状 | 対処 |
|---|---|
| `gcloud` で billing リンクが失敗 | `gcloud beta billing accounts list` で account id を確認、`/bootstrap-gcp --billing-account <id>` で再実行 |
| `terraform init` でバックエンドエラー | `TF_STATE_BUCKET` が `.env` に書かれていない可能性。`/bootstrap-gcp` をやり直し |
| `gh api orgs/poc-recycle/...` が 404 | `gh auth refresh -s admin:org,admin:org_hook` |
| direnv が `.env` を読まない | `direnv allow` を忘れている、もしくは zsh フックを `~/.zshrc` に入れていない |
| Gemini 呼び出しが地域エラー | `VERTEX_LOCATION=global` を `.env` で確認（Gemini 3 が preview の間は global 経由のみ。`docs/planning.md` §4.1） |

## このリポジトリの Claude 周り

- 規約は `CLAUDE.md`（英語）
- サブエージェント定義: `.claude/agents/`（`gcp-operator` / `adk-builder` / `phase-reviewer` / `charter-tuner`）
- スキル: `.claude/skills/`（`phase-status` / `region-check` / `context7-lookup`）
- スラッシュコマンド: `.claude/commands/`
- 設定: `.claude/settings.json`（読み取り系は許可、書き込み系は都度承認）

「Claude が読む文書は英語、人間が読む文書は日本語」というルールでまとめてあります。

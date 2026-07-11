# Infra ポリシー（叩き台 v0.1）

- 最終更新: 2026-06-22
- ステータス: Draft v0.1
- 親: [`docs/planning.md`](../planning.md) §4 / §10 / §14 / §15
- 関連: [`infra/`](../../infra/) / [`docs/setup-ja.md`](../setup-ja.md)
- 対象読者: 開発者本人 + Claude Code

---

## 0. このドキュメントの目的

`infra/` の Terraform 構成を **管理しやすさ中心**でベストプラクティス化する。MVP は単一 GCP プロジェクト・単一環境だが、後で env 増殖したときに **書き直さずに済む構造**を最初から取る。

---

## 1. 現状（v0.1 時点）

```
infra/
├─ versions.tf
├─ providers.tf
├─ variables.tf
├─ apis.tf
├─ service_accounts.tf
├─ storage.tf
├─ firestore.tf
├─ artifact_registry.tf
├─ secret_manager.tf
├─ outputs.tf
├─ backend.tf                  # 生成済み（gs://poc-recycle-tfstate）
├─ terraform.tfvars.example
└─ README.md
```

「全部フラット」。これは MVP として OK。次の閾値で **モジュール分割** に進む。

---

## 2. モジュール分割の方針

### 2.1 いつ分割するか

「単一 main で読みづらくなった瞬間」を待たない。**以下のいずれかが起きたら分割する**:

- リソース数が **40 を超える**
- 同じ resource 種別の重複（例: 3 つ以上の `google_storage_bucket`）が出る
- env を 2 つ以上持つ必要が出る
- 別チームに一部を渡す可能性が出る

### 2.2 目指す構造

```
infra/
├─ envs/
│  ├─ dev/                    # 開発（任意）
│  │  ├─ main.tf
│  │  ├─ variables.tf
│  │  ├─ terraform.tfvars
│  │  └─ backend.tf
│  └─ prod/                   # MVP は実質 1 env でも prod/ に置く
│     ├─ main.tf
│     ├─ variables.tf
│     ├─ terraform.tfvars
│     └─ backend.tf
└─ modules/
   ├─ apis/                   # google_project_service 群
   ├─ iam/                    # SA + IAM bindings
   ├─ storage/                # GCS buckets（uploads / sandbox / etc）
   ├─ firestore/
   ├─ artifact_registry/
   ├─ secrets/                # Secret Manager コンテナ
   ├─ network/                # VPC connector / egress 制限（spike-6 後）
   └─ cloud_run/              # 任意（apps/web, apps/api の Cloud Run 設定をコード化）
```

各 `envs/<env>/main.tf` は module を呼ぶだけの薄い orchestrator。env 間の差は **tfvars と backend prefix のみ**。

### 2.3 単一 vs マルチ workspace

選択肢:

| 案 | 長所 | 短所 |
|---|---|---|
| `terraform workspace` で env 切替 | state 軽量 | tfvars 切替を CI で間違えやすい |
| **envs/<env>/ 別ディレクトリ**（採用） | env ごとに明示的、レビューしやすい | コピー部分が多少出る |

→ **envs/<env>/** を採用。MVP では `envs/prod/` のみ存在。`dev` 追加時はディレクトリをコピーして tfvars を書き換える。

---

## 3. 命名規約

### 3.1 リソース名

| 種別 | 命名 | 例 |
|---|---|---|
| プロジェクト | `<product>` | `poc-recycle` |
| GCS バケット | `<project>-<purpose>` | `poc-recycle-uploads`, `poc-recycle-tfstate`, `poc-recycle-sandbox` |
| SA | `sa-<role>` | `sa-api`, `sa-deploy`, `sa-sandbox`, `sa-preview-runtime` |
| Artifact Registry repo | `<product>` | `poc-renovater` |
| Cloud Run service (preview) | `poc-<agentId>-pr<NN>` | `poc-abc123-pr-5`（planning §10.5）|
| Cloud Run service (platform) | `<product>-<app>` | `poc-renovater-api`, `poc-renovater-web` |
| Secret | `<UPPER_SNAKE>` | `GITHUB_APP_PRIVATE_KEY` |

**禁則**:
- ❌ ハイフン以外の区切り（`_` / `.` / CamelCase）
- ❌ 日付・PR 番号などの可変要素をプラットフォーム共有リソース名に入れない（Managed PoC の preview は別、§10.5）

### 3.2 ラベル（label）

すべての label-対応リソースに付ける:

```hcl
labels = {
  product      = "poc-renovater"
  managed_by   = "terraform"
  env          = var.env             # prod / dev
  cost_center  = "platform"
}
```

検索 / 課金 / コスト配賦の基盤。**手作業作成リソースは label `managed_by = manual` にし、Terraform 管理に移行する候補をすぐ見つけられるようにする**。

---

## 4. ライフサイクル

### 4.1 `force_destroy`

- **GCS**: `prod` では `force_destroy = false` 固定。`dev` のみ `true` 可（個人検証）
- **Artifact Registry**: 削除前に latest images を退避するスクリプトを用意するまで `false`
- **Firestore**: そもそも terraform destroy で消さない（消えるとデータ全滅）。`prevent_destroy = true` 付きの lifecycle ブロックを足す

### 4.2 `prevent_destroy`

データを持つリソースは必ず:

```hcl
lifecycle {
  prevent_destroy = true
}
```

対象: `google_storage_bucket.uploads`, `google_firestore_database.default`, `google_secret_manager_secret.*`, `google_storage_bucket.tfstate`（後者は実質手動）

destroy したいときは **明示的に lifecycle ブロックを外す PR を出す**。

### 4.3 `ignore_changes`

外部から変更される可能性のあるフィールドだけ `ignore_changes` で除外:
- Cloud Run service の `template.spec.containers[0].image`（CI が更新する）

「全部 ignore」は禁止。

---

## 5. tfstate 管理

| 項目 | 採用 |
|---|---|
| バックエンド | GCS（`gs://poc-recycle-tfstate`） |
| Prefix | `poc-renovater/state`（env 増えたら `poc-renovater/<env>/state`） |
| バージョニング | **ON**（既設） |
| Lock | GCS の built-in (Terraform 1.5+ で `use_lockfile = true`) |
| 暗号化 | デフォルト GCP-managed key（CMEK 不要） |
| アクセス | 開発者 + sa-deploy（CI）のみ |
| バックアップ | バージョニング履歴で十分（追加バックアップ不要） |

state を **手で編集しない**。`terraform state mv` 等が必要なときは PR で記録。

---

## 6. シークレット取扱

### 6.1 Terraform で扱うもの

- **Secret Manager の "コンテナ"**（`google_secret_manager_secret`）— 中身は持たない
- **IAM bindings**（`google_secret_manager_secret_iam_member`）

### 6.2 Terraform で扱わないもの

- **シークレット値そのもの**（PEM / webhook secret / API key）— `scripts/bootstrap-github.sh` 等のシェルから `gcloud secrets versions add` で投入
- **値を tfvars / .env / 平文ファイルに置かない**

### 6.3 tfvars にも秘密を入れない

`infra/terraform.tfvars` は **設定値専用**。値が secret なら Secret Manager 経由で実行時に解決。

---

## 7. CI / drift 検知

### 7.1 CI（GitHub Actions、Phase 0 で導入）

- PR 時: `terraform fmt -check`, `validate`, `plan` の差分をコメント
- `main` push 時: 自動 apply はしない（**手動承認**）
- weekly: `terraform plan` を回し、差分があれば issue 作成（drift 検知）

### 7.2 Drift の典型と対処

| Drift | 対処 |
|---|---|
| 手動で IAM 追加 | revert する PR を切る or Terraform に取り込む |
| API 自動有効化 | `apis.tf` に追記 |
| ラベル変更 | tfvars 更新 |
| Cloud Run image tag | `ignore_changes` で許容済の場合は無視 |

### 7.3 plan の保存

`terraform plan -out=plan.out` を CI で artifact 化。`apply` 時は **直前の plan を再利用**（人間が読んだ plan と apply する plan が同一であることを保証）。

---

## 8. 環境差の付け方（将来）

### 8.1 dev / staging を増やす場合

```
infra/envs/
├─ prod/
│  ├─ main.tf                # modules を呼ぶ
│  └─ terraform.tfvars
├─ staging/
│  └─ ...
└─ dev/
   └─ ...
```

差は **tfvars だけ**:
- `project_id`
- `region`（変えない）
- `upload_bucket_name`（globally unique 必要）
- `preview_ttl_hours`（dev は短く）
- `preview_max_concurrent`（dev は 1）

### 8.2 GCP プロジェクトを env ごとに分けるか

| 案 | 採用判断 |
|---|---|
| 1 プロジェクト + namespace 分離（現行） | MVP 採用、§10.5 |
| env ごとに別プロジェクト | 課金分離が必要になったら採用 |
| Managed PoC を別プロジェクトに | 隔離強化要件が出たら採用 |

**今は移行しない**。判断ポイント:
- 課金を user 単位に分けたくなったら → 別プロジェクト
- 個人情報が入ったら → 別プロジェクト

---

## 9. コスト管理

### 9.1 常時かかるもの（注意）

| サービス | 概算 | コメント |
|---|---|---|
| Cloud Run（platform: api/web） | 数 USD/月 | min-instances=0 で実質起動時のみ |
| Firestore Native | ほぼ無料 | 無料枠 1GB / 50K read/day |
| GCS（tfstate / uploads / sandbox） | 数 USD/月 | バージョニング ON のため累積に注意 |
| Artifact Registry | 〜数 USD/月 | image 累積要監視 |
| Secret Manager | < 1 USD/月 | コンテナ数で課金 |
| Cloud Logging | 数 USD/月 | デフォルト保持 30 日 |

### 9.2 spike / 検証時にかかるもの

| サービス | 注意 |
|---|---|
| Vertex AI Gemini 3 | per-token 課金。spike-1 で実測 |
| Cloud Build | per-build-minute 課金。spike-4 と Coding Agent で発生 |
| Cloud Run job (sandbox) | per-vCPU-second |

### 9.3 ガード

- `infra/budgets.tf`（Phase 5+）で月次 budget alert を設定
- 予算超過時は Pub/Sub → Cloud Function で **自動停止**（preview の縮退）まで設計（MVP では alert のみ）

---

## 10. アクセスと権限

### 10.1 開発者

- gcloud で個人アカウント。**Project Editor は付与しない**
- 必要な role を最小で付与（`Secret Manager Viewer` / `Storage Viewer` 等）

### 10.2 SA の責任分離

| SA | 主な role |
|---|---|
| `sa-api` | `aiplatform.user`, `datastore.user`, `logging.logWriter`, 各 secret accessor, uploads RW |
| `sa-deploy` | `run.admin`, AR writer, actAs preview-runtime |
| `sa-sandbox` | uploads viewer, **他なし** |
| `sa-preview-runtime` | AR reader, **プラットフォーム資源に触れない** |

絶対に `Owner` / `Editor` / `Project IAM Admin` を SA に付けない。

### 10.3 GitHub Actions からの認証

**Workload Identity Federation** を使う（key file を CI に置かない）。Phase 0 終盤で `infra/modules/iam/wif.tf` を追加。

---

## 11. ⚠ 未確定項目

| 項目 | 状態 | 確定タイミング |
|---|---|---|
| モジュール分割の実施タイミング | リソース 40 超 or 2 env で | Phase 5+ |
| VPC connector / egress 制限の有無 | Sandbox 設計と連動 | spike-6 / Phase 4 |
| Workload Identity Federation 設定 | Phase 0 で CI 導入時に | Phase 0 |
| Budget アラート | Phase 5 で導入 | Phase 5 |
| CMEK（顧客管理鍵） | 要件出るまで保留 | – |

---

## 12. 採用ルール（短く）

1. **モジュール分割は閾値で発動**（40 リソース / 2 env / 重複 / 受け渡し）
2. データ持ちリソースは **`prevent_destroy = true`**
3. **シークレット値を Terraform で扱わない**（コンテナだけ）
4. tfstate は GCS、バージョニング ON、ロック有効
5. `force_destroy = false` を prod の既定
6. **WIF で CI 認証**、Key file は使わない
7. **drift は weekly に検知**、手動変更は即 Terraform に取り込み

---

## 13. 更新ルール

- 構造変更（モジュール分割等）は **小さな PR** に分ける（state 移行を 1 PR ずつ）
- `prevent_destroy` を外す PR には **理由と復旧計画**を必ず本文に書く
- 新リソース追加時、label と naming を本書に照らして確認

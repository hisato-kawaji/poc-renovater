# Sandbox ポリシー（仮置き v0.1）

- 最終更新: 2026-06-22
- ステータス: Draft v0.1 / **仮置き**（Phase S spike-6 で実装を起こしてから本書を更新）
- 親: [`docs/planning.md`](../planning.md) §10.3 / §10.5 / §15
- 関連: [`docs/policy/backend-architecture.md`](backend-architecture.md) §2 / [`docs/app-architecture.md`](../app-architecture.md)
- 対象読者: 開発者本人 + Claude Code

---

## 0. このドキュメントの目的

Coding Agent が **Managed Repo のコードを clone / edit / test する場所**（= sandbox）の設計規約を仮置きする。

Managed Repo の中身は **任意の Vibe Coding 製コード**であり、**信用しない**前提で動かす。プラットフォーム本体（apps/api / GCP リソース）に侵食させない隔離が最重要。

本書は **何を作るか / 何を守るか** を確定する。**実装の詳細**は Phase S の spike を経て更新する。

---

## 1. 要件（Must）

| 要件 | 由来 |
|---|---|
| **最小権限 SA で動く**（sa-sandbox） | docs/planning.md §10.5 / §15 |
| **GCS uploads bucket の read のみ**（write 不可） | §15 |
| **Firestore / Secret Manager / 他 GCS バケットには触れない** | §15 |
| **GitHub Installation Token を agent から渡される** | 直接 Secret から読まない（権限分離） |
| **使い捨て**：ジョブごとに新しいコンテナ、終了時に痕跡を残さない | §10.3 / §15 |
| **時間上限**：1 ジョブ ≤ **30 分**（暫定） | リソース枯渇防止 |
| **ネットワーク egress 制限**：パッケージレジストリ・GitHub・Vertex のみ許可 | 漏出防止 |
| **入出力は契約済み JSON / ファイル**：自由なバイナリ吐き出しを許さない | コーディングエージェント契約 |

---

## 2. 実装案（暫定）

### 2.1 ランナー選定

| 候補 | 長所 | 短所 | 採用 |
|---|---|---|---|
| **Cloud Run job**（バッチ実行）| 起動が速い、SA 厳格設定、ライフサイクル自動 | egress 制限を別途設定（Cloud Run + Service Controls）| ◎ **第一案** |
| Cloud Build job | clone/build に最適化、artifact registry 連携 | apps/api からの起動・結果取得が REST 経由で重い | ○ |
| GKE Autopilot | 細かい制御 | クラスタ管理コスト | × |
| Local Docker（apps/api と同居）| 速い | 同居プロセス汚染リスク。隔離弱い | × |

→ **Cloud Run job**（asia-northeast1）で Coding Agent を実行。実装は Phase S spike-6 / Phase 4 で確定。

### 2.2 コンテナイメージ

```
sandbox/
├─ Dockerfile             # base: python:3.12-slim + node:20 + git
├─ entrypoint.sh          # exec the spec from /input/spec.json
└─ runner/                # Python パッケージ。spec parser + git ops + test runner
```

含めるツール（最小）:
- `git`, `gh`（GitHub CLI、token は env で渡す）
- `python3.12`, `uv`, `pytest`
- `node` 20, `pnpm`
- ファイル走査 / diff（標準）
- 必要なら `ruff` / `tsc` をプリインストール（テスト時の起動短縮）

**プリインストールしない**: 任意のシステムパッケージマネージャ操作（apt/brew/curl install）はジョブ実行時に**禁止**（egress 制限で物理的にも縛る）。Managed Repo の依存はその repo 自身の lockfile から `uv sync` / `pnpm install` で導入する。

### 2.3 IO 契約

apps/api（adapter `sandbox_cloudrunjob`）が GCS にスペックを置き、Cloud Run job を kick:

```
gs://poc-recycle-sandbox/jobs/<jobId>/input/
   spec.json          # job spec（下記スキーマ）
   github_token       # 短命 installation token（jobId に紐づく一時 secret）

gs://poc-recycle-sandbox/jobs/<jobId>/output/
   result.json        # 成功時の CodeChange
   logs.ndjson        # 進行ログ（NDJSON）
   debug/              # 任意の追加ファイル（diff スナップショット等）
```

**spec.json** スキーマ（最小）:

```jsonc
{
  "jobId": "01J...",
  "type": "coding",                         // 将来 "test" / "analyze" などを追加
  "engine": "adk_gemini",                   // adk_gemini | claude_code
  "repo": {
    "fullName": "poc-recycle/managed-poc-xxx",
    "ref": "main",
    "branchName": "agent/issue-12"
  },
  "issue": {                                 // Coding Agent への入力
    "number": 12,
    "title": "...",
    "body": "..."
  },
  "charter": { /* trimmed Charter */ },
  "constraints": {
    "maxDiffLines": 400,
    "outOfScope": ["..."],
    "timeoutSec": 1500
  },
  "callbackUrl": "https://api.../api/v1/internal/sandbox/result"   // 任意
}
```

**result.json**（CodeChange 契約）:

```jsonc
{
  "jobId": "01J...",
  "status": "ok",                            // ok | failed | aborted
  "branch": "agent/issue-12",
  "diff": "<unified diff>",
  "diffLines": 137,
  "prTitle": "...",
  "prBody": "...",
  "risk": "...",
  "rollback": "...",
  "metrics": {
    "durationSec": 412,
    "modelInputTokens": 13200,
    "modelOutputTokens": 2100
  }
}
```

apps/api 側で受け取って `pulls/{n}` を作る。

### 2.4 GitHub Token の受け渡し

- apps/api が **その job 専用の短命 installation token**（最大 60 分）を Secret Manager に書き出す
- Cloud Run job は env から path だけ受け取り、token は **ファイルから読む**（ログに出さない）
- 完了後 secret は **必ず削除**

### 2.5 ネットワーク egress

Cloud Run job + VPC connector + egress 制限で **以下のみ許可**:

- `github.com`, `api.github.com`, `objects.githubusercontent.com`
- `pypi.org`, `files.pythonhosted.org`
- `registry.npmjs.org`
- `*.googleapis.com`（Vertex AI / GCS write to job output bucket / Logging）
- `npmjs.org` / `pnpm` の registry

それ以外の宛先は **遮断**。

### 2.6 ジョブの寿命

| イベント | 動作 |
|---|---|
| 開始から `constraints.timeoutSec` 超過 | SIGTERM → 30s 後 SIGKILL → `result.json{status:"aborted"}` を書いて終了 |
| 正常完了 | `result.json{status:"ok"}` を書く、コンテナ終了 |
| 例外 | `result.json{status:"failed", error: {...}}` を書く |
| いずれの場合も | secret 削除、job リソース削除（Cloud Run job の自動 GC を期待） |

### 2.7 ログ

- 標準 logger → Cloud Logging（`logName=projects/.../logs/run.googleapis.com/stdout`）
- 構造化 NDJSON で `gs://...output/logs.ndjson` にも複製（オーバーヘッド小）
- **PEM / token / Anthropic key は logger redactor で必ず除去**

---

## 3. Coding Engine 抽象との接続

[`backend-architecture.md`](backend-architecture.md) §2 の `ports.sandbox.SandboxPort` を adapter `sandbox_cloudrunjob` が実装する。

```python
# ports/sandbox.py
class SandboxPort(Protocol):
    async def run_coding_job(self, spec: SandboxJobSpec) -> SandboxJobResult: ...
```

application/agents/coding.py から呼ぶときは:

```python
# application/agents/coding.py
class CodingAgentService:
    sandbox: SandboxPort
    scm: ScmPort

    async def implement(self, agent_id: str, issue_no: int) -> Pull:
        spec = self._build_spec(agent_id, issue_no)
        result = await self.sandbox.run_coding_job(spec)
        if result.status != "ok":
            raise SandboxFailureError(detail=result.error)
        enforce_diff_cap(result.diffLines, self.settings.max_pr_diff_lines)
        enforce_out_of_scope(result.changedPaths, ...)
        pr = await self.scm.open_pull(...)
        return pr
```

Sandbox の中身（実際のコード変更）は **engine.py の責務**であり、本書のスコープではない（[`backend-architecture.md`](backend-architecture.md) §8 / `.claude/skills/adk-agent-pattern.md` 参照）。

---

## 4. セキュリティ・ガードレール（再掲）

| ガード | 実装場所 |
|---|---|
| sa-sandbox の最小 IAM | infra/service_accounts.tf |
| 入力スペックの検証 | sandbox/runner（spec.json は Pydantic で必須項目チェック） |
| egress 制限 | infra/vpc.tf（Phase S 後に追加予定） |
| token のログ漏れ防止 | sandbox/runner のロガー設定 |
| 出力 diff 行数チェック | application/agents/coding.py + domain/guardrails.py |
| 出力パスの out_of_scope チェック | 同上 |
| 実行時間上限 | spec.constraints.timeoutSec + Cloud Run job timeout（二重） |

---

## 5. ⚠ 未確定項目（Phase S / Phase 4 で確定）

| 項目 | 状態 | 確定タイミング |
|---|---|---|
| Cloud Run job vs Cloud Build の最終選定 | Cloud Run job 推し | spike-4 / spike-6 |
| egress 制限の具体（Service Controls / VPC SC / firewall） | 未調査 | Phase 4 |
| `claude_code` エンジン実行時の `ANTHROPIC_API_KEY` 渡し方 | 未調査（同じく一時 secret に書き出し方式で行く想定） | Phase 4 |
| Cloud Run job の起動時間（cold start）が許容範囲か | 未測定 | spike-6 |
| `result.json` の最大サイズ・diff サイズの上限 | 未検討 | Phase 4 |
| ジョブの並列度（同時実行数） | 未決 | Phase 5 / 6 |
| ジョブ失敗時の再試行ポリシー | application 側に持つ予定 | Phase 6 |

---

## 6. 採用ルール（短く）

1. **隔離が第一義**。性能や開発効率より優先する
2. SA は **sa-sandbox**、Firestore / Secret Manager 直アクセス不可
3. **IO は GCS バケット越し**、コードと環境は使い捨てコンテナ
4. egress は **whitelist 方式**、デフォルト deny
5. spec / result は **Pydantic スキーマで検証**、シェル expansion 等の落とし穴を排除
6. ログから **secret は自動 redact**

---

## 7. 更新ルール

- 実装が固まったら本書を「仮置き → 確定」に昇格
- spike-6 完了後、`docs/tech-stack-validation.md` の決定ログにも追記
- 新しいジョブタイプ（`type: test` 等）を増やす際は **必ず本書 §2.3 のスキーマを拡張**してから adapter 側を変更

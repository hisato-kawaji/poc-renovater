# アプリケーション実装ガイド（叩き台 v0.1）

- 最終更新: 2026-06-23（spike-5 Firestore 状態機械の知見を反映）
- ステータス: Draft v0.1
- 親ドキュメント: [`docs/planning.md`](planning.md)（§3-§8 が契約レベル。本書はその下のコードレベル規約）
- 関連: [`docs/tech-stack-validation.md`](tech-stack-validation.md)（Phase S で確定する項目をマーカー付きで併記）
- 対象読者: 開発者本人 + Claude Code
- 位置づけ: 「どう実装すべきか」を **コードに落ちる粒度** で揃える。`.claude/skills/` の各レシピはこの規約の **適用例**。

> **注記（2026-06-22 更新）**: 本書のディレクトリ構成は [`docs/policy/backend-architecture.md`](policy/backend-architecture.md) §2.2 の Hexagonal（domain / ports / adapters / application / interface）に同期済み。Pydantic Settings / 例外設計 / middleware / テスト方針は §2.2 以降の章で本書独自に詳述する。

---

## 0. このドキュメントの目的

`docs/planning.md` は **何を作るか / 何と何の契約か** を確定する。だが「実装の作法」までは決めていないため、人/Claude が書いた時に揺れが出る。本書は以下を統一する:

- ディレクトリと責務の境界
- 関数/クラスの命名と分割粒度
- 例外・エラーハンドリングの統一形式
- 設定 / シークレットの流入経路
- 非同期化 / トランザクション境界の引き方
- テストのレイヤー分け

**確定 / 未確定** をマークする。未確定（"⚠ Phase S 後に確定" マーク）は Phase S（spike）で得られた結果で本書を更新する。

---

## 1. レイヤー責務（一覧）

[`docs/policy/backend-architecture.md`](policy/backend-architecture.md) §2.2 の Hexagonal 構成を採用する。

```
apps/web/                   フロント（Next.js 15 App Router）。ユーザー操作と表示のみ。ビジネスロジック禁止
└─ packages/shared/ts/      型と JSON Schema を import

apps/api/app/               純粋 → 外側 の順で並ぶ
├─ domain/                  純粋。状態機械 / ガードレール / 値オブジェクト。**他層へ import しない**
├─ ports/                   外部依存の interface（Protocol）。実装は持たない
├─ adapters/                Port の実装（旧 services/）。GCP / GitHub / Sandbox / Vertex 等
├─ application/             ユースケース層
│  ├─ orchestrator/          状態機械の駆動（domain + ports を組み立て）
│  └─ agents/                AI エージェント駆動の薄いラッパー（リトライ・コスト記録）
├─ interface/               入口
│  ├─ http/                  routers/ + middleware/
│  └─ webhooks/              github / cloudbuild コールバック
├─ models/                  Pydantic — packages/shared から re-export
├─ deps.py                  DI 配線（adapters → ports に注入）
├─ settings.py              Pydantic Settings
└─ main.py                  FastAPI app 構築

packages/
├─ agents/                  ADK エージェント定義 + プロンプト + tools（apps/api/application/agents から呼ばれる）
└─ shared/                  Pydantic スキーマ + emit された JSON Schema（apps/web から import）

sandbox/                    Coding Agent サンドボックス（隔離コンテナ）。adapters/sandbox_cloudrunjob 越しに呼ぶ
infra/                      Terraform
templates/                  Managed Repo 注入用雛形
spikes/                     Phase S の検証コード（プロダクション import 禁止）
```

**依存方向の規約** ([`backend-architecture.md`](policy/backend-architecture.md) §2.3):

```
interface  →  application  →  domain
                ↓               ↑
              ports  ←  adapters
```

**禁則**:
- `domain/` は外部依存ゼロ（標準 + Pydantic のみ）
- `application/` から `adapters/` を直接 import しない。**必ず `ports/` 越しに、deps.py で注入される**
- `interface/` は `application/` のみを呼ぶ（domain / adapters / ports に直接触らない）
- `apps/api/application/agents/`（薄いラッパー）と `packages/agents/`（実体）は **一方向**（apps → packages のみ）

---

## 2. apps/api 実装パターン

### 2.1 ディレクトリ詳細

```
apps/api/
├─ app/
│  ├─ main.py
│  ├─ settings.py            # Pydantic Settings
│  ├─ deps.py                # DI 配線（adapters を ports に注入）
│  ├─ exceptions.py          # 業務例外クラス（FoundryError 派生）
│  ├─ logging_config.py      # 構造化ログ
│  │
│  ├─ domain/                # 純粋。外部依存ゼロ
│  │  ├─ states.py            # AgentState / Action / TRANSITIONS（planning §9 と一致）
│  │  ├─ events.py            # ドメインイベント型
│  │  ├─ charter.py           # Charter 採点 + Gate ロジック
│  │  ├─ guardrails.py        # diff cap / out_of_scope / preview cap
│  │  └─ values/              # AgentId / IssueId / 値オブジェクト
│  │
│  ├─ ports/                 # 外部依存の interface（Protocol）
│  │  ├─ scm.py               # GitHub-like
│  │  ├─ storage.py           # Firestore + GCS
│  │  ├─ secrets.py           # Secret Manager
│  │  ├─ build.py             # Cloud Build
│  │  ├─ runtime.py           # Cloud Run deploy
│  │  ├─ llm.py               # Vertex / Gemini
│  │  ├─ sandbox.py           # Sandbox 実行
│  │  └─ a2a.py               # A2A client（Managed Agent 呼び出し）
│  │
│  ├─ adapters/              # Port の実装（旧 services/）
│  │  ├─ scm_github/          # auth.py / repos.py / issues.py / pulls.py
│  │  ├─ storage_firestore/   # 各サブコレクション CRUD
│  │  ├─ storage_gcs/         # uploads bucket 読み書き
│  │  ├─ secrets_gcp/         # secret-manager-ref skill の実体
│  │  ├─ build_cloudbuild/
│  │  ├─ runtime_cloudrun/    # cloud-run-source-deploy skill の実体
│  │  ├─ llm_vertex/          # Gemini 呼び出し
│  │  ├─ sandbox_cloudrunjob/ # spec → job kick + 結果取得
│  │  └─ a2a_http/            # A2A クライアント HTTP 実装
│  │
│  ├─ application/           # ユースケース層
│  │  ├─ orchestrator/
│  │  │  ├─ driver.py         # trigger(agent_id, action) -> StateTransitionResult
│  │  │  └─ transitions/      # transition_<from>_to_<to> の関数群
│  │  └─ agents/             # AI エージェント駆動（apps/api 側の薄いラッパー）
│  │     ├─ ingest.py
│  │     ├─ charter.py
│  │     ├─ repo.py
│  │     ├─ issue_planner.py
│  │     ├─ coding.py
│  │     ├─ review.py
│  │     ├─ deploy.py
│  │     └─ self_improve.py
│  │
│  ├─ interface/             # 入口（旧 routers/ + webhooks/）
│  │  ├─ http/
│  │  │  ├─ routers/
│  │  │  │  ├─ uploads.py
│  │  │  │  ├─ agents.py
│  │  │  │  ├─ charter.py
│  │  │  │  ├─ issues.py
│  │  │  │  ├─ pulls.py
│  │  │  │  └─ deployments.py
│  │  │  └─ middleware/
│  │  │     ├─ auth.py             # Firebase ID token verification
│  │  │     ├─ exception.py        # FoundryError → HTTPException
│  │  │     ├─ logging.py          # request-id / 構造化ログ
│  │  │     └─ webhook_signature.py # /webhooks/ で使う
│  │  └─ webhooks/
│  │     ├─ github.py
│  │     └─ cloudbuild.py
│  │
│  └─ models/                # Pydantic — packages/shared/python から re-export
│
├─ tests/
│  ├─ unit/
│  │  ├─ domain/              # 純粋テスト（最重要・最も書きやすい）
│  │  ├─ application/         # ports を fake で差し替えてユースケース単体
│  │  └─ adapters/            # 外部 SDK / HTTP を mock
│  ├─ integration/            # Firestore Emulator + GitHub responses mock
│  └─ e2e/                    # 起動した API へ HTTP 叩く（demo subset）
└─ pyproject.toml            # uv-managed
```

### 2.2 Pydantic Settings（`app/settings.py`）

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="forbid")

    # GCP
    google_cloud_project: str
    google_cloud_region: str = "asia-northeast1"

    # Vertex
    vertex_location: str = "global"
    gemini_model_pro: str
    gemini_model_flash: str

    # Agent runtime / Coding engine
    agent_runtime: str = "cloudrun"
    coding_engine: str = "adk_gemini"

    # Firestore
    firestore_database: str = "(default)"

    # GitHub
    github_org: str = "poc-recycle"
    github_app_id: int
    github_app_installation_id: int

    # Guardrails
    charter_score_threshold: int = 80
    max_pr_diff_lines: int = 400
    preview_ttl_hours: int = 48
    preview_max_concurrent: int = 2
```

**規約**:
- 全 env は **ここに集約**。services / agents は `Depends(get_settings)` 経由で受け取る
- `extra="forbid"` で typo を検出
- 秘密値（PEM / webhook secret / Anthropic key）は **Settings に入れない** → `services/secrets/` で都度解決

### 2.3 例外設計（`app/exceptions.py` + `middleware/exception.py`）

```python
# exceptions.py
class FoundryError(Exception):
    """Base business error."""
    http_status: int = 500
    code: str = "foundry/internal"

class CharterGateNotPassedError(FoundryError):
    http_status = 409
    code = "foundry/charter-gate-not-passed"

class DiffTooLargeError(FoundryError):
    http_status = 422
    code = "foundry/diff-too-large"

class OutOfScopeChangeError(FoundryError):
    http_status = 422
    code = "foundry/out-of-scope"

class SandboxFailureError(FoundryError):
    http_status = 502
    code = "foundry/sandbox-failure"
```

**規約**:
- services / orchestrator / agents から投げる **業務例外は必ず `FoundryError` 派生**
- middleware で統一 JSON 形式に変換:
  ```json
  {"code": "foundry/charter-gate-not-passed", "message": "...", "details": {...}}
  ```
- `HTTPException` を services 内で raise しない（**routers / middleware の専有**）
- 不明な例外は 500 + `code=foundry/internal`、details は出さない（情報漏洩防止）

### 2.4 認証ミドルウェア（`middleware/auth.py`）

- ヘッダ: `Authorization: Bearer <Firebase ID token>`
- 検証: `firebase_admin.auth.verify_id_token(token)` — `firebase-admin` SDK
- 検証成功時、`request.state.user = User(uid=..., email=...)` をセット
- 失敗時、401 + `code=foundry/unauthenticated`

**Webhook ルート（`/api/webhooks/...`）はこのミドルウェアをバイパス** → `webhook_signature.py` で代替検証。

### 2.5 Firestore クライアントの非同期化と状態機械

`google-cloud-firestore` の Python SDK は **sync** が標準。orchestrator のトランザクションは sync API がやりやすい。`async def` の router 内では:

- 短い読み取り: `await asyncio.to_thread(client.collection(...).document(...).get)` で安全
- トランザクション: orchestrator/transitions.py 内で **sync コードブロックにまとめる** → 外側で `await asyncio.to_thread(...)`

**状態遷移の正規パターン**（spike-5 検証, 2026-06-23）: state-machine port は **常に `@firestore.transactional` でラップした関数に `client.transaction()` を渡す** 形を取る。CAS チェック（期待 `expected_status` と実 `current_status` の照合）に失敗した場合は **業務例外（`IllegalStateTransition` 等の `ValueError` 派生）** を投げる。`google.api_core.exceptions.Aborted` は SDK 側のデコレータが最大 5 回まで自動リトライで吸収するため、**アプリ層で `Aborted` を catch する必要はない**。MAX_ATTEMPTS 枯渇のレアケースのみ `Aborted` がアプリ層に到達するので、その時だけ guardrail ログに「inflight retry」を吐く。詳細は [`spikes/spike-5-firestore-state/decision.md`](../spikes/spike-5-firestore-state/decision.md) を参照。

**イベント順序保証**（spike-5 検証, 2026-06-23）: `agents/{id}/events` サブコレクションへの append は `seq` フィールドで一次ソート、`created_at` (server timestamp) で二次ソートする。`seq` は **state-machine port 側で `agents/{id}.next_event_seq` を同一トランザクション内でインクリメント** することで原子的に採番する（Phase 1+ の DoD 要件。spike では呼び出し側カウンタで代用）。auto-generated doc ID の lexical order だけに依存してはならない（Firestore は spec 上 monotonic を保証しない）。

**Firestore async API 採用可否**（spike-5 検証, 2026-06-23）: sync API + `asyncio.to_thread` で十分なパフォーマンス（state 遷移の競合は適切に処理、event append は ~16 writes/sec）を確認。**MVP は sync + to_thread 方針を維持**。async API への全面切替は不要。

### 2.6 Webhook 署名検証（`middleware/webhook_signature.py`）

`.claude/skills/github-app-token.md` 記載の HMAC-SHA256 検証ロジックを middleware として実装。`/api/webhooks/github` 専用 mount。

```python
# 抜粋
expected = "sha256=" + hmac.new(secret, raw_body, hashlib.sha256).hexdigest()
if not hmac.compare_digest(expected, request.headers["X-Hub-Signature-256"]):
    raise WebhookSignatureMismatchError()  # → 401
```

`raw_body` の取得は FastAPI で少し細工が必要（`request.body()` を読み切る `BackgroundTasks` 経由ではなく、`Depends` で先取り）。

---

## 3. orchestrator パターン

### 3.1 State machine の駆動

```python
# orchestrator/driver.py（概念）
class OrchestratorDriver:
    def __init__(self, deps: Deps): ...

    def trigger(self, agent_id: str, action: Action) -> StateTransitionResult:
        """1 transition = 1 Firestore transaction. action は外部入力 or 内部イベント。"""
        state = self._read_state(agent_id)
        transition = TRANSITION_TABLE[(state, action)]   # KeyError → InvalidTransition
        return transition(self.deps, agent_id)
```

**規約**:
- TRANSITION_TABLE は `dict[(State, Action), Callable]` で **明示的に網羅**
- 不正遷移は黙って無視せず `InvalidTransitionError` を raise
- 各 transition 関数は **(deps, agent_id) -> StateTransitionResult** に統一
- Firestore txn の中で `agents/{id}` の更新と `events/{eventId}` の append を **同時に**書く

### 3.2 Transition 関数の例

```python
# orchestrator/transitions.py
def transition_uploaded_to_analyzing(deps: Deps, agent_id: str) -> StateTransitionResult:
    @firestore.transactional
    def _txn(tx):
        doc = deps.fs.agents.doc(agent_id)
        snap = doc.get(transaction=tx)
        if snap.get("status") != "UPLOADED":
            raise InvalidStateError(snap.get("status"))
        tx.update(doc, {"status": "ANALYZING", "updatedAt": SERVER_TIMESTAMP})
        emit_event(tx, agent_id, type="analyzed_start", actor="orchestrator")
        return StateTransitionResult(from_="UPLOADED", to="ANALYZING")
    return _txn(deps.fs.transaction())
```

**規約**:
- 関数名は `transition_<from>_to_<to>` 固定
- transaction 外で副作用（GitHub 呼び出し / Cloud Build kick）はしない → 副作用は **transaction commit 後** に services 経由で
- 副作用が失敗した場合の **補償遷移**を必ず定義（例: `transition_analyzing_to_failed`）
- CAS チェック失敗（`snap.get("status") != expected`）は `IllegalStateTransition`（`FoundryError` 派生）を投げる。**`Aborted` は `@firestore.transactional` が SDK 内部で自動リトライ（最大 5 回）するため、アプリ層では catch しない**（spike-5 検証, 2026-06-23 — 詳細は [`spikes/spike-5-firestore-state/decision.md`](../spikes/spike-5-firestore-state/decision.md)）
- event append は同一 transaction 内で `agents/{id}.next_event_seq` をインクリメントして `seq` を原子的に確保（spike-5 検証, 2026-06-23）

### 3.3 非同期処理（長時間 Job）

Ingest / Coding / Deploy などは秒〜分単位かかる。実行モデルの選択肢:

| 案 | 長所 | 短所 | 採用 |
|---|---|---|---|
| **同期 (router 内で await)** | 単純、トレースしやすい | router タイムアウト、ワーカープール圧迫 | MVP 採用 |
| Cloud Tasks → Cloud Run job | スケール / 再試行 / 耐障害 | 導入コスト | Phase 6 で導入検討 |
| Cloud Run の background task | コードは簡単 | コンテナが死ぬとロスト | 採用しない |

⚠ **Phase S 後に確定**: spike-2 (ADK 呼び出し時間) を見て、router 内同期で耐えるかを判定。耐えられないなら Phase 0 終盤で Cloud Tasks 導入。

---

## 4. agents の呼び出し境界

`apps/api/agents/<name>.py` は `packages/agents/<name>` の **薄い薄いラッパー**。

```python
# apps/api/agents/charter.py
class CharterAgentClient:
    def __init__(self, deps: Deps):
        self.engine = build_charter_agent()   # packages/agents/charter 側

    async def turn(self, user_message: str, charter: Charter, analysis: Analysis) -> CharterTurnResult:
        for attempt in range(3):
            try:
                result = await asyncio.to_thread(
                    self.engine.run,
                    CharterAgentInput(message=user_message, charter=charter, analysis=analysis),
                )
                return CharterTurnResult.model_validate(result)
            except ValidationError as e:
                if attempt == 2:
                    raise AgentParseError(self.__class__.__name__) from e
                # リトライ時はエラー文をエージェントに伝えて再生成（packages/agents 側で吸収）
                continue
            finally:
                _record_usage(deps, agent=self.__class__.__name__, attempt=attempt)
```

**規約**:
- リトライは **最大 3 回**、ValidationError のみ対象
- 他の例外（タイムアウト・通信障害）は即 raise
- **コスト記録は必ず finally で**（`record_usage` は token / latency / model を `agents/{id}/usage/{eventId}` に append）

---

## 5. apps/web 実装パターン

### 5.1 App Router 構成

```
apps/web/
├─ app/
│  ├─ layout.tsx
│  ├─ page.tsx
│  ├─ agents/
│  │  ├─ page.tsx                # 一覧
│  │  └─ [agentId]/
│  │     ├─ page.tsx             # 詳細
│  │     ├─ charter/page.tsx     # 壁打ち UI
│  │     ├─ issues/page.tsx
│  │     └─ pulls/[n]/page.tsx
│  └─ api/                       # 基本使わない（バックエンドは apps/api）
├─ components/
├─ lib/
│  ├─ firebase.ts                # Firebase Auth + Firestore client init
│  ├─ api.ts                     # apps/api への fetch ラッパー
│  └─ schemas.ts                 # packages/shared/ts から re-export
└─ tests/
```

### 5.2 Server / Client 分割の原則

| ケース | 採用 |
|---|---|
| 初期描画（リスト・詳細） | **Server Component**（apps/api 経由でデータ取得） |
| Firestore リアルタイム更新 | **Client Component**（`onSnapshot` リスナー） |
| フォーム / 壁打ち送信 | **Server Action** が第一候補。apps/api への REST 呼び出しに変換 |
| 認証状態 | **Client Component**（Firebase Auth SDK は client only） |

**確定**（spike-5 検証, 2026-06-23）: Firestore Web SDK の Server Component 内利用は基本サポート外。**初期データは apps/api 経由**、ライブ更新は Client Component の `onSnapshot` リスナーで購読する。Python SDK 側で計測した listener latency は **p50 0.048s / max 0.057s**（3 件の status 変更で測定）で、UX 上 polling 不要のレベル。コールバック signature は `(doc_snapshots, changes, read_time) -> None`、購読解除は `watch.unsubscribe()`。詳細は [`spikes/spike-5-firestore-state/decision.md`](../spikes/spike-5-firestore-state/decision.md)。

### 5.3 型共有

```typescript
// apps/web/lib/schemas.ts
export * from "@poc-renovater/shared";

import { AgentSchema, type Agent } from "@poc-renovater/shared";
// AgentSchema は zod 互換 / JSON Schema 由来。
// API レスポンスは AgentSchema.parse(json) で必ず検証してから state に入れる
```

**規約**:
- `any` 禁止、`unknown` から `zod.parse` で narrow
- フェッチ結果は必ず schema validate → ランタイムで型が壊れない保証
- API への送信前に同じ schema で validate（送信側も入力検証）

### 5.4 Firebase Auth

- ログイン: Google プロバイダ（MVP は社内なら何でも）
- ID Token を fetch ごとに添付:
  ```typescript
  const token = await auth.currentUser?.getIdToken();
  fetch("/api/...", { headers: { Authorization: `Bearer ${token}` } });
  ```
- middleware で Cookie 化はしない（複雑化回避）

---

## 6. 横断的関心

### 6.1 構造化ログ

- 形式: JSON 1 行 1 イベント
- 必須フィールド: `time` (ISO8601 UTC), `severity`, `message`, `request_id`, `agent_id` (任意)
- 実装: Python は `structlog` を採用、 GCP Cloud Logging には JSON のまま流れる → severity がそのままマップ
- TS 側は console.log を JSON 化（Server Component / Server Action のみ）

### 6.2 リクエスト ID

- middleware で `X-Request-Id` ヘッダを生成（未指定なら uuid7）
- すべてのログに付与
- 外部呼び出し（GitHub / Vertex）にも `X-Request-Id` を伝播

### 6.3 トレース

⚠ **Phase S 後に確定**: OpenTelemetry → Cloud Trace は MVP 採用。spike 中はトレース無しでも可。

### 6.4 設定の流入経路（再掲）

```
.env (local)  ┐
              ├→  pydantic_settings.Settings  →  Depends(get_settings)  →  services / agents
GCP env vars  ┘

Secret Manager  →  services/secrets/get_secret(name)  →  agents / services  （TTLCache 5min）
```

`.env` に Secret Manager の値を二重保持しない。

### 6.5 テスト方針

| レイヤー | テストの種類 | 主な依存 |
|---|---|---|
| `routers/` | 単体（TestClient） | services を mock |
| `services/` | 単体（実装ごと） | GCP クライアントを fake / GitHub HTTP を responses |
| `orchestrator/` | 単体（Firestore Emulator） | transition 1 つずつ |
| `agents/` (apps 側) | 単体 | packages/agents の Runner を mock、ValidationError リトライをテスト |
| `packages/agents/` | 単体 | LLM 呼び出しは stub、output_schema を含むスキーマ検証 |
| `apps/web` | コンポーネント単体 + e2e（Playwright） | apps/api への fetch を msw で mock |
| 統合 | demo シナリオの subset | Firestore Emulator + Cloud Build をローカル mock |

---

## 7. 確定 / ⚠未確定 一覧（Phase S 後に本書を更新）

| 項目 | 状態 | 確定先 |
|---|---|---|
| ディレクトリ構成・責務 | 確定 | 本書 §1 / §2 |
| 例外設計（FoundryError 派生） | 確定 | 本書 §2.3 |
| Pydantic Settings の流入経路 | 確定 | 本書 §2.2 / §6.4 |
| 認証 / Webhook 検証ミドルウェア | 確定 | 本書 §2.4 / §2.6 |
| State machine + Firestore txn の境界 | 確定 | 本書 §3 |
| 長時間 Job の実行モデル | ⚠ 未確定 | spike-2 で時間測定後、本書 §3.3 を更新 |
| Firestore async API 採用可否 | 確定（spike-5, 2026-06-23） | 本書 §2.5 — sync + `asyncio.to_thread` を維持 |
| Server Component で Firestore SDK を扱うか | 確定（spike-5, 2026-06-23） | 本書 §5.2 — 初期は apps/api 経由、ライブは Client + `onSnapshot` |
| `next_event_seq` 原子採番 | Phase 1+ 実装要 | spike-5 残課題、本書 §2.5 / §3.2 で要件化 |
| OpenTelemetry / Cloud Trace 採用 | ⚠ 未確定 | Phase 5 までに判定、本書 §6.3 を更新 |
| Coding Engine 抽象化の最終契約 | ⚠ 未確定 | spike-6 で決定、本書 §4 を更新 |

---

## 8. このドキュメントを更新するルール

1. 規約の変更は **PR で合意**（main 直 commit でも、内容は事前に提案ベースで）
2. ⚠未確定項目を解消したら、本書の該当節と「§7 一覧」を同時に更新
3. `.claude/skills/` のレシピは本書の **適用例** として整合させる（skill 追加時に本書のどこに紐づくか明記）
4. `docs/planning.md` §4 / §8 と矛盾する変更を本書に入れる場合は、planning.md 側を別 PR で更新（先方を正本としているため）

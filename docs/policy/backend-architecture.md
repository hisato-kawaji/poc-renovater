# バックエンド アーキテクチャ ポリシー（叩き台 v0.1）

- 最終更新: 2026-06-22（spike-2 / 3 / 5 / 6 反映）
- ステータス: Draft v0.2
- 親: [`docs/planning.md`](../planning.md) §3 / [`docs/app-architecture.md`](../app-architecture.md)
- 対象読者: 開発者本人 + Claude Code

---

## 0. このドキュメントの目的

`docs/app-architecture.md` は実装パターン（ディレクトリ・命名・例外）を規定済み。本書は **その背骨となるアーキテクチャ選択** を、複数案の比較とともに明示する。

具体的には：
1. なぜ Clean / Hexagonal / Onion / Vertical Slice / Layered / Agent-centric の中から **Hexagonal + Agent-centric ハイブリッド** を採用するのか
2. その結果としてディレクトリ責務とインポート方向がどう決まるか
3. 既存の `apps/api/` 構造との対応関係

---

## 1. 選択肢の比較

### 1.1 候補

| 案 | 一行説明 |
|---|---|
| **Layered (N-tier)** | router → service → repository の縦割り |
| **Clean Architecture** | Entity 中心、依存性は内→外、Use Case 層を明示 |
| **Hexagonal / Ports & Adapters** | ドメインを中心に Port（interface）と Adapter（実装）で囲う |
| **Onion** | Clean に近い同心円。差は主に呼称 |
| **Vertical Slice** | 機能単位で 1 ディレクトリ。各 slice 内に必要な層を抱える |
| **Agent-centric**（現状） | エージェント名でディレクトリを区切る |

### 1.2 評価軸

| 軸 | 重要度 |
|---|---|
| ドメインロジックの隔離（テスト容易性） | 高 |
| 外部依存差し替えコスト（GCS / GitHub / Vertex / Sandbox の付け替え） | 高 |
| 状態機械の表現のしやすさ | 高 |
| AI エージェント（8 体）の責務分離 | 高 |
| ボイラープレート / 学習コスト | 中 |
| 機能追加時の変更局所性 | 中 |
| マイクロサービス分割への発展性 | 低（MVP では不要） |

### 1.3 スコアシート

| 軸 | Layered | Clean | Hexagonal | Onion | Vertical Slice | Agent-centric |
|---|---|---|---|---|---|---|
| ドメイン隔離 | △ | ◎ | ◎ | ◎ | ○ | × |
| 外部依存差替 | △ | ○ | ◎ | ○ | △ | × |
| 状態機械表現 | ○ | ◎ | ◎ | ◎ | △ | × |
| エージェント分離 | × | △ | △ | △ | ○ | ◎ |
| 学習コスト | ◎ | × | ○ | △ | ○ | ◎ |
| 変更局所性 | △ | ○ | ○ | ○ | ◎ | ◎ |
| 単一でカバー | できる | できる | できる | できる | 可（要規律） | 不可 |

ハッキリした弱点があるのは Agent-centric（ドメインの隔離概念がない）と Layered（依存制御が緩い）。

---

## 2. 採用する設計：Hexagonal コア + Agent-centric ハイブリッド

### 2.1 採用の要約

中心に **Hexagonal/Ports & Adapters** を置く。理由:
- 我々のドメインは **状態機械（Managed Agent の lifecycle）** で表現できる。ドメインロジックを純粋に保ち、外部（GitHub / Firestore / GCS / Cloud Build / Vertex / Sandbox）は Port 越しに繋ぐ。
- Charter Gate / 差分ライン上限 / 非スコープ検知 などの **ガードレールはドメインロジック** なので、ここを隔離してテストできる構造が最大価値。
- 一方、AI エージェント 8 体は **責務単位でディレクトリを分けたい**（Agent-centric の良さ）。これは Adapter / Application 側の **構造化**として併存できる。

つまり：
- **ドメイン層**: 状態機械 + ガードレール + 値オブジェクト（純粋、Firestore 等の知識ゼロ）
- **Ports 層**: 外部依存の interface 定義（Protocol で）
- **Adapters 層（services/）**: GCP / GitHub / Sandbox / Vertex 実装
- **Application 層（agents/）**: AI エージェント駆動の薄いユースケース
- **Interface 層（routers/）**: HTTP 境界、Pydantic in/out

「Clean を採らないのか？」については、**Clean の精神（依存逆転、ドメイン隔離）は採用する**。命名と層数だけ Hexagonal の用語に揃える方が、Port が見えやすく Web 周りの実装者に馴染みやすい。

### 2.2 ディレクトリ写像（最終形）

```
apps/api/app/
├─ domain/                     # 純粋。ここから他層へ import しない
│  ├─ states.py                # StrEnum / State machine 定義
│  ├─ events.py                # ドメインイベント（型）
│  ├─ charter.py               # Charter 採点 + Gate ロジック
│  ├─ guardrails.py            # diff cap / out_of_scope / preview cap
│  └─ values/                  # 値オブジェクト（AgentId / IssueId 等）
│
├─ ports/                      # 外部依存の interface（Protocol）
│  ├─ scm.py                   # GitHub-likeを抽象化（Issue/PR/Repo）
│  ├─ storage.py               # GCS-like
│  ├─ secrets.py
│  ├─ build.py                 # Cloud Build / 等
│  ├─ runtime.py               # Cloud Run deploy
│  ├─ llm.py                   # Vertex / Gemini
│  ├─ sandbox.py
│  └─ a2a.py                   # A2A client（Managed Agent 呼び出し）
│
├─ adapters/                   # services/ から改名（Port の実装）
│  ├─ scm_github/              # ports.scm の GitHub 実装
│  ├─ storage_gcs/
│  ├─ secrets_gcp/
│  ├─ build_cloudbuild/
│  ├─ runtime_cloudrun/
│  ├─ llm_vertex/
│  ├─ sandbox_cloudrunjob/
│  └─ a2a_http/
│
├─ application/                # ユースケース層
│  ├─ orchestrator/            # 状態機械の駆動（domain と adapters を組み合わせ）
│  │  ├─ driver.py
│  │  └─ transitions/
│  └─ agents/                  # AI エージェント駆動（per-agent ユースケース）
│     ├─ ingest.py
│     ├─ charter.py
│     ├─ repo.py
│     ├─ issue_planner.py
│     ├─ coding.py
│     ├─ review.py
│     ├─ deploy.py
│     └─ self_improve.py
│
├─ interface/                  # routers/ から改名（HTTP 境界）
│  ├─ http/
│  │  ├─ routers/
│  │  └─ middleware/
│  └─ webhooks/                # github / cloudbuild のコールバック
│
├─ models/                     # Pydantic（packages/shared の re-export）
├─ deps.py                     # DI wiring
├─ settings.py
└─ main.py
```

### 2.3 依存方向の規約（重要）

```
interface  →  application  →  domain
                ↓               ↑
              ports  ←  adapters
```

- `domain/` は **どこにも依存しない**（標準ライブラリ + Pydantic のみ）
- `application/` は `domain/` と `ports/` のみ import
- `adapters/` は `ports/` を import して **interface を実装する**（domain と adapters は直接やりとりしない）
- `interface/` は `application/` のみを呼ぶ（domain や adapters を直接触らない）
- `models/` は packages/shared の薄いラッパー、どこからも参照可

**禁則の例:**
- ❌ `application/agents/coding.py` から `adapters/scm_github` を直接 import
- ✅ `application/agents/coding.py` は `ports.scm.ScmPort` を受け取り、deps.py で `GithubScmAdapter` が注入される

### 2.4 既存 `apps/api/app/services/` との関係

[`docs/app-architecture.md`](../app-architecture.md) §2 で示した `services/` 構造は、本書の `adapters/` に該当する。**改名するだけで思想は連続**。

- `services/scm/github/` → `adapters/scm_github/`
- `services/firestore/` → `adapters/storage_firestore/`（or `repo_firestore/`）
- `services/gcs/` → `adapters/storage_gcs/`
- `services/cloudrun/` → `adapters/runtime_cloudrun/`
- `services/secrets/` → `adapters/secrets_gcp/`
- `services/vertex/` → `adapters/llm_vertex/`

`orchestrator/` と `agents/` は `application/` 配下に移動。

`app-architecture.md` 側は次の更新で本書に整合させる。

---

## 3. ドメイン層の主役：状態機械

### 3.1 状態の表現

```python
# domain/states.py
from enum import StrEnum

class AgentState(StrEnum):
    UPLOADED = "UPLOADED"
    ANALYZING = "ANALYZING"
    ANALYZED = "ANALYZED"
    CHARTERING = "CHARTERING"
    CHARTER_READY = "CHARTER_READY"
    REGISTERING = "REGISTERING"
    REGISTERED = "REGISTERED"
    PLANNING = "PLANNING"
    IMPLEMENTING = "IMPLEMENTING"
    PR_OPEN = "PR_OPEN"
    REVIEWING = "REVIEWING"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    PREVIEW_READY = "PREVIEW_READY"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    MERGED = "MERGED"
    IDLE = "IDLE"
    FAILED = "FAILED"

class Action(StrEnum):
    UPLOAD = "upload"
    START_ANALYZE = "start_analyze"
    FINISH_ANALYZE = "finish_analyze"
    OPEN_CHARTER = "open_charter"
    FINALIZE_CHARTER = "finalize_charter"
    REGISTER = "register"
    PLAN_ISSUES = "plan_issues"
    IMPLEMENT = "implement"
    REVIEW = "review"
    REQUEST_CHANGES = "request_changes"
    DEPLOY_PREVIEW = "deploy_preview"
    APPROVE = "approve"
    SELF_IMPROVE = "self_improve"
    STOP = "stop"
```

### 3.2 遷移テーブル

```python
# domain/states.py（続き）
TRANSITIONS: dict[tuple[AgentState, Action], AgentState] = {
    (AgentState.UPLOADED, Action.START_ANALYZE): AgentState.ANALYZING,
    (AgentState.ANALYZING, Action.FINISH_ANALYZE): AgentState.ANALYZED,
    (AgentState.ANALYZED, Action.OPEN_CHARTER): AgentState.CHARTERING,
    # ... 全遷移を明示。網羅性は test で確認
}

class InvalidTransitionError(Exception): ...

def next_state(current: AgentState, action: Action) -> AgentState:
    try:
        return TRANSITIONS[(current, action)]
    except KeyError as e:
        raise InvalidTransitionError(f"{current} -> {action} is not allowed") from e
```

### 3.3 ガードレールはドメイン関数

```python
# domain/guardrails.py
def enforce_charter_gate(score: int, threshold: int) -> None:
    if score < threshold:
        raise CharterGateNotPassedError(score=score, threshold=threshold)

def enforce_diff_cap(diff_lines: int, cap: int) -> None:
    if diff_lines > cap:
        raise DiffTooLargeError(diff_lines=diff_lines, cap=cap)

def enforce_out_of_scope(changed_paths: list[str], out_of_scope: list[str]) -> None:
    matched = [p for p in changed_paths if any(p.startswith(s) for s in out_of_scope)]
    if matched:
        raise OutOfScopeChangeError(paths=matched)
```

これらは外部依存ゼロでテストできる。Coding Agent も Review Agent もこの関数を呼ぶ。

---

## 4. Port の書き方（雛形）

### 4.1 ScmPort（GitHub 等）

```python
# ports/scm.py
from typing import Protocol, Self
from dataclasses import dataclass

@dataclass(frozen=True)
class RepoRef:
    full_name: str    # "poc-recycle/managed-pocXYZ"
    default_branch: str

class ScmPort(Protocol):
    def create_repo(self, name: str, *, private: bool = True) -> RepoRef: ...
    def create_branch(self, repo: RepoRef, branch: str, from_sha: str) -> None: ...
    def open_issue(self, repo: RepoRef, title: str, body: str, *, labels: list[str]) -> int: ...
    def open_pull(self, repo: RepoRef, head: str, base: str, title: str, body: str) -> int: ...
    def comment_pull(self, repo: RepoRef, n: int, body: str) -> None: ...
    def review_pull(self, repo: RepoRef, n: int, *, approved: bool, body: str) -> None: ...
    def get_pull_diff(self, repo: RepoRef, n: int) -> str: ...
```

Port には実装の知識を一切入れない（戻り型がドメイン値オブジェクト or 標準型のみ）。

### 4.2 LlmPort（ADK + Vertex Gemini） — spike-2 / spike-3 で確定

実装は ADK の `LlmAgent` + `Runner` + `SessionService` を使う。Phase 1 起点で **以下のパターンが確定** している（spike-2 採用 / spike-3 PASS, 2026-06-22）。

```python
# 確定パターン（adapters/llm_vertex/agent.py 相当）
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService  # 本番は永続版に差替
from pydantic import BaseModel

class AgentOutput(BaseModel):
    ...  # 各エージェントの出力スキーマ（packages/shared/python/ で定義）

agent = LlmAgent(
    name="...",                                 # Python identifier 制約（英数 + _）に注意
    model=os.environ["GEMINI_MODEL_PRO"],       # or FLASH per §10.2
    instruction="...",
    output_schema=AgentOutput,                  # ← JSON 強制はこの 1 行で済む
)
session_service = InMemorySessionService()
runner = Runner(agent=agent, session_service=session_service, app_name="...")

# ★ session は必ず事前生成（自動作成されない）
session = await session_service.create_session(app_name="...", user_id="...")

async for event in runner.run_async(session_id=session.id, ...):
    if event.is_final_response():
        result = AgentOutput.model_validate_json(event.content.parts[0].text)
```

**spike から得た規約**:

- **env 名マッピング**（spike-2 検証）: ADK / google-genai は `GOOGLE_GENAI_USE_VERTEXAI=true` と `GOOGLE_CLOUD_LOCATION=<region>` を要求する。本プロジェクトの正規設定値は引き続き `VERTEX_LOCATION`（`docs/planning.md` §4.1 region policy の真の値）とし、`run.sh` / 起動スクリプト側で `GOOGLE_CLOUD_LOCATION` にマップする（`.env.example` 明示済）。
- **session 必須**（spike-2 検証）: `runner.run_async()` を呼ぶ前に `session_service.create_session(...)` を必ず呼ぶ。MVP は `InMemorySessionService`、Phase 1+ で永続化を判断（Firestore-backed or `VertexAiSessionService`）。
- **構造化出力は `output_schema`**（spike-3 PASS, 25/25）: 自作の「JSON プロンプト指示 + `json.loads`」は入れない。`event.content.parts[0].text` を `Pydantic.model_validate_json()` で復元する 1 本道。
- **ValidationError リトライは guardrails 層**（spike-3 finding）: spike では 0% 失敗だったが、本番では `ValidationError` を捕捉する最大 N 回のリトライ・ラッパーを ports / application 共通ヘルパとして用意する。これは `docs/planning.md` §15 の deterministic check の一部。
- **async 統一**: `runner.run_async()` + `async for event` を使う。`apps/api` の async/await と整合。

実装側（adapters/llm_vertex/）はこのパターンを薄く LlmPort interface に被せ、application/agents/ からは Pydantic 入出力だけが見えるようにする。

### 4.3 StateRepo（Firestore Native） — spike-5 で確定

`AgentState` の遷移と event log は Firestore Native で扱う（spike-5 PASS, 2026-06-23）。**`@firestore.transactional` デコレータで read-modify-CAS を完結させる** のが canonical pattern。

```python
# 確定パターン（adapters/storage_firestore/state.py 相当）
from google.cloud import firestore

@firestore.transactional
def _transition(tx: firestore.Transaction, ref, expected: AgentState, to: AgentState):
    snap = ref.get(transaction=tx)
    if not snap.exists:
        raise AgentNotFoundError(ref.id)
    cur = snap.get("status")
    if cur != expected:
        # CAS mismatch — ドメイン例外として surface
        raise IllegalStateTransition(f"agent={ref.id} expected={expected} actual={cur}")
    tx.update(ref, {"status": to, "updated_at": firestore.SERVER_TIMESTAMP})
```

**spike から得た規約**:

- **CAS 失敗は `Aborted` ではなく業務例外**（spike-5 重要発見）: `@firestore.transactional` は内部で transport-level の `google.api_core.exceptions.Aborted` を最大 5 回まで吸収・再試行する。アプリ層に到達するのは「再試行後に prerequisites（state CAS）が崩れていた」ケースだけなので、上記の `IllegalStateTransition` のような **ドメイン例外** に変換して raise する。**`Aborted` を application 層で catch しない** — 真に枯渇した時だけ guardrail ログに残す方針。
- **event log の順序保証は `seq` フィールド**（spike-5 検証）: `agents/{id}/events` サブコレクションは append-only。`doc_id` の lexical order は Firestore spec 上 monotonic を約束していないため、ソートキーは `seq` を一次・`created_at` を二次にする。
- **`next_event_seq` の原子的採番**（spike-5 残課題、Phase 1 DoD 候補）: `seq` は `agents/{id}.next_event_seq` を state transition と **同じトランザクション内で同時インクリメント** することで原子的に確保する。spike は呼び出し側カウンタで代用したが、本番ではこの方式が必須。
- **realtime listener**（spike-5 PASS）: `doc_ref.on_snapshot(cb)` を採用。p50 48ms / max 57ms と十分小さく、UI 側の polling は不要。コールバック署名は `(doc_snapshots, changes, read_time) -> None`、解除は `watch.unsubscribe()`。Phase 1 では Web → Firestore 直 listen（Firestore JS SDK の `onSnapshot`）が主、Python 側は worker 間の状態検知に使う。

### 4.4 CodingEnginePort — spike-6 で確定（PR#16 マージ済）

Coding Agent の LLM 切替（Vertex Gemini ⇄ Claude Code CLI）を Phase 4 で安定運用するための抽象は `packages/agents/coding/engine.py` に既にマージ済（spike-6 PASS, 2026-06-23, PR#16）。

```python
# 確定パターン（packages/agents/coding/engine.py より要約）
from typing import Protocol, runtime_checkable
from pydantic import BaseModel

class Issue(BaseModel):
    id: str
    title: str
    body: str
    hint_files: list[str]

class CodeChange(BaseModel):
    branch_name: str
    diff: str            # unified diff
    pr_title: str
    pr_body: str         # ## Summary / ## Test plan セクションで正規化
    files_touched: list[str]

@runtime_checkable
class CodingEngine(Protocol):
    async def generate(self, issue: Issue) -> CodeChange: ...

def make_engine() -> CodingEngine:
    """`CODING_ENGINE` env を読んで実装を返す。default `adk_gemini`。"""
    ...
```

**spike から得た規約**:

- **`CodeChange` は 5 フィールド契約**（spike-6 検証）: `branch_name` / `diff` (unified) / `pr_title` / `pr_body` / `files_touched`。両エンジン（`AdkGeminiEngine` / `ClaudeCodeEngine`）が全フィールドを充足することを確認済。Phase 4 でフィールドを増やす場合は両エンジンを同時に追従させる。
- **engine 選択は `CODING_ENGINE` env + `make_engine()` のみ**: 下流（`_downstream.apply(CodeChange)`）は engine 名を import せず、`CodeChange` だけを受け取る。engine 由来の差異（ADK `LlmAgent.name` の identifier 制約、Claude CLI 出力の ```json``` フェンス除去、PR body 正規化）はすべて `engine.py` 内に閉じ込め済み。
- **Claude Code CLI は `--allowedTools ""`（空 allowlist）**（spike-6 検証）: 純 LLM として扱うため明示的に空 allowlist を渡す。`--disallowedTools` denylist は使わない（新規ツールが追加された場合に自動で抑止できないため）。Phase 4 で Sandbox 内 Edit/Write を許可する設計に切り替える場合は、allowlist を `"Edit,Write,Read,Bash"` 等に明示拡張する。
- **engine 共通の例外**: `EngineError` で双方の失敗を統一。

`CodingEnginePort` はこの spike 成果物（`packages/agents/coding/engine.py`）を **そのまま Phase 4 の起点** として使う。`ports/coding_engine.py` を別途切り出す場合も interface は上記のままで良い。

---

## 5. application 層

### 5.1 orchestrator の責務

- 「次の遷移を起こす」を atomic に駆動
- domain.next_state() で遷移先を決め、必要な ports を呼んで副作用を出す
- transaction 内の Firestore 書き込みは **状態と event の append** だけ
- 外部副作用（GH 呼び出し / Cloud Build kick）は **commit 後** に ports 越しで実行

### 5.2 application/agents/ の薄さ

```python
# application/agents/charter.py
@dataclass
class CharterAgentService:
    llm: LlmPort
    storage: StoragePort
    settings: Settings

    async def turn(self, agent_id: str, user_message: str) -> CharterTurnResult:
        charter, analysis = await self.storage.load_charter_and_analysis(agent_id)
        result = await self._run_with_retry(user_message, charter, analysis)
        new_score = result.score
        if new_score >= self.settings.charter_score_threshold:
            # ドメインの Gate チェックは別途 enforce_charter_gate で
            ...
        await self.storage.save_charter(agent_id, result.charter)
        return result
```

- ここに **ガードレール・スコア閾値の判定ロジック** は書かない（domain に投げる）
- LLM 呼び出しは ports.llm 越し、リトライは共通ヘルパで（3 回・ValidationError のみ）

---

## 6. アーキテクチャの進化（Event-Driven, Multi-Tenancy & Job Management）

MVP後の進化として、以下のアーキテクチャ拡張を導入している（Phase 1/2/4 の成果）。

### 6.1 非同期 Job 管理とエラーリカバリ (新規追加)
Pub/Subによる自動リトライだけでは、外部システム（GitHubやLLM）の障害時に「ユーザーにエラーを可視化し、対話的に再開・キャンセルを選ばせる」ことができない。
これを解決するため、大局的な `Agent` のステートマシンから、個別の非同期処理ステップを分離して管理する **Job モデル** を導入する。

#### Job テーブルスキーマ
| カラム名 | 型 | 説明 |
|---|---|---|
| `id` | String | JobのユニークID (ULID推奨) |
| `agent_id` | String | 紐づくAgent (PoC) ID |
| `tenant_id` | String | マルチテナント隔離キー |
| `job_type` | Enum | 実行する処理の種類 (例: `FILE_UPLOAD`, `GITHUB_REPO_CREATE`) |
| `status` | Enum | `PENDING`, `RUNNING`, `FAILED`, `COMPLETED`, `CANCELED` |
| `error_details` | JSON | 失敗理由や外部APIからのレスポンスコード等の詳細 |
| `retry_count` | Int | ユーザーが「再試行」した回数 |
| `created_at` / `updated_at` | Timestamp | |

#### 外部疎結合システムの依存・障害ポイントと再実行のライフサイクル
あらゆる工程における「API等のレスポンス次第で後続に影響を及ぼすケース」と「隠れた非同期プロセス」を洗い出し、細かい Job の単位として定義する。
ユーザーは画面上で進行中の Job をトラッキングでき、`FAILED` または `BLOCKED` になった場合、詳細なエラーメッセージを確認した上で **[再実行 (Retry)]** または **[キャンセル (Cancel)]** を選択できる。
再実行された場合、Job のステータスは `PENDING` に戻り、Pub/Sub に再投入されて処理を再開する。

##### メインパイプライン（ビジネスロジック）
1. **`FILE_UPLOAD` (ファイルアップロードと解凍)**
   - **依存**: Google Cloud Storage (GCS)
   - **影響**: ネットワークエラー等でソースコードがないとプレ解析に進めない。
2. **`PRE_ANALYSIS` (ファイルの検修・LLM解析)**
   - **依存**: LLM API (Vertex AI Gemini)
   - **影響**: レートリミット(429)や長文超過でCharter（方針）作成に進めない。
3. **`CHARTER_CHAT_RESPONSE` (LLM対話応答)**
   - **依存**: LLM API
   - **影響**: ユーザーとのチャット中にLLMがダウンすると「タイピング中」のままフリーズする。1往復の対話もJobとしてステータス管理する。
4. **`GITHUB_REPO_CREATE` (リポジトリ登録・初期化)**
   - **依存**: GitHub API
   - **影響**: 認証切れや名前重複(422)で出力先が作れず以後のフローが完全にブロックされる。
5. **`GITHUB_ISSUE_CREATE` (Issue作成)**
   - **依存**: GitHub API
   - **影響**: Issue単位でJobを発行し、スパム判定等で失敗した場合は個別に再試行可能にする。
6. **`CODE_GENERATION` (LLMによる実装)**
   - **依存**: LLM API
   - **影響**: ハルシネーションによる無限ループ発生時、タイムアウトでJobを停止し、プロンプト微修正後に再開する。
7. **`GITHUB_PR_CREATE` (PRオープン)**
   - **依存**: GitHub API
   - **影響**: Baseブランチの更新によるコンフリクト時はユーザーに通知。
8. **`GITHUB_PR_MERGE` (レビューとマージ)**
   - **依存**: GitHub API
   - **影響**: 保護ブランチ制約でマージ拒否された場合、人間がGitHub上で承認後に再試行する。

##### インフラ・システムライフサイクル（見落とされがちな処理）
9. **`CODE_EMBEDDING_INGESTION` (RAG用ベクトル化)**
   - **依存**: Embedding API / Vector DB
   - **影響**: アップロード後、大量のファイルをベクトル化する際にレートリミットに引っかかる。チャンクごとに進捗管理し、失敗部分からリトライさせる。
10. **`SANDBOX_PROVISIONING` (Sandbox環境起動)**
    - **依存**: Cloud Run Jobs / Firecracker / 外部プロバイダ
    - **影響**: コンテナ起動失敗はAIの実装エラーとは別物。インフラエラーとして切り分け、再試行させる。
11. **`WAIT_FOR_CI_CHECKS` (CI完了待ち)**
    - **依存**: GitHub Actions (Webhook/Polling)
    - **影響**: PR作成後、CI完了を待たずにマージしようとすると弾かれる。CI失敗時はユーザーに修正を促すかAIに再実装タスクを投げる。
12. **`WAIT_FOR_USER_SECRETS` (環境変数入力待ち)**
    - **依存**: ユーザー入力
    - **影響**: デプロイに必要なAPIキー等が未設定の場合、`BLOCKED` 状態で意図的にJobを止め、ユーザーに入力を促す。
13. **`DEPLOY_PREVIEW` / `DEPLOY_PRODUCTION` (デプロイ)**
    - **依存**: Cloud Build, Cloud Run, Firebase Hosting
    - **影響**: ビルドエラー時はログを提示し、設定修正後に再デプロイ。
14. **`HEALTH_CHECK_VERIFICATION` (稼働確認)**
    - **依存**: デプロイされたURLのHTTPレスポンス
    - **影響**: デプロイAPIが成功しても502エラーになるケースを防ぐため、200 OK が返るまでポーリング確認する。
15. **`RESOURCE_CLEANUP` (ロールバック処理)**
    - **依存**: 各種クラウドリソース
    - **影響**: エラーやユーザーの「キャンセル」時に、中途半端なリポジトリやSandbox環境を削除して課金を防ぐ。

### 6.2 イベント駆動アーキテクチャ (Pub/Sub)
- **非同期状態遷移**: Webhook やユーザーアクションによる状態遷移を直接処理するのではなく、Pub/Sub にイベント（例: `start_analysis`, `start_planning`）をパブリッシュする。これらは上記の `Job` モデルの状態更新と連動する。
- **Cloud Run Push Subscriptions**: FastAPI 内の `/api/events/pubsub` が Pub/Sub からの Push リクエストを受け取る。
- **実行モデル**: Cloud Run の CPU Throttling を回避するため、FastAPI の `BackgroundTasks` は使用せず、Push ハンドラ内で同期的に `await AgentUseCase.execute()` を実行する。リトライ制御やスケーリングは Pub/Sub + Cloud Run に委譲する。

### 6.3 マルチテナントと隔離
- **テナントID（tenant_id）**: 全てのリクエストは `X-Tenant-ID` ヘッダを必須とし、Deps 経由で各 Port/Adapter に注入される。
- **Firestore 隔離**: `tenants/{tenant_id}/agents/{upload_id}` をプレフィックスとして分離。
- **GCS 隔離**: `gs://bucket_name/tenants/{tenant_id}/agents/...`
- **ランタイム隔離**: Cloud Run プレビュー等のデプロイ時は `poc-{upload_id[:8]}-...` の命名規則で隔離しつつ、将来的にはテナントごとに専用の Service Account を適用できる構造を維持している。

---

## 7. テスト戦略との接続

| 層 | テスト | 偽物 |
|---|---|---|
| domain | 純関数テスト | なし（純粋） |
| ports | typing 上の確認のみ | – |
| adapters | 単体（外部 SDK / HTTP を mock） | google-cloud-* の fake、`responses` |
| application | 単体 | port の fake 実装（dataclass で十分） |
| interface | 統合（TestClient） | application を mock |

ドメイン層の純粋テスト（domain/charter.py, domain/guardrails.py）が **最重要かつ最も書きやすい**。Charter Gate の挙動はここで保証する。

---

## 8. 移行コスト

現在の `apps/api/` は中身が `.gitkeep` のみ。移行ではなく **最初からこの構造で実装する**。本書を Phase 0 終盤 / Phase 1 着手時に skill `adk-agent-pattern` や `phase-start` から参照可能にする。

`docs/app-architecture.md` §2.1 のディレクトリ詳細は本書に整合する形で更新する（次回 commit で）。

---

## 9. 採用しないことを明示

| 案 | 不採用の理由 |
|---|---|
| **マイクロサービス分割（agent 単位）** | MVP では単一サービス。境界を引きすぎると orchestrator のトランザクションが破綻 |
| **CQRS** | 状態機械の書き込み /読み出しが対称、分離の利得が低い |
| **イベントソーシング** | Firestore の `events` サブコレクションは「監査ログ」であって 再構築前提ではない。再構築が必要になったら見直す |
| **DDD の完全装備（Aggregate, Domain Service, Application Service の厳密分離）** | 1 人開発（+ Claude）には過剰。`domain/` 内の純関数で十分 |
| **ドメインを TypeScript / Go に分離** | Python 単一スタックの利点が大きい |

---

## 10. Phase S spike 結果との対応

| 項目 | 状態 | spike / source |
|---|---|---|
| LlmPort の async 化（ADK の同期/非同期） | **確定** — `runner.run_async()` + `async for event` 採用。詳細は §4.2 | [`spikes/spike-2-adk-gemini/decision.md`](../../spikes/spike-2-adk-gemini/decision.md) |
| LLM 構造化出力の方式 | **確定** — `LlmAgent(output_schema=PydanticModel)` 25/25 PASS。詳細は §4.2 | [`spikes/spike-3-adk-structured-output/decision.md`](../../spikes/spike-3-adk-structured-output/decision.md) |
| StateRepo の遷移パターン | **確定** — `@firestore.transactional` 採用。CAS-mismatch はドメイン例外で surface。詳細は §4.3 | [`spikes/spike-5-firestore-state/decision.md`](../../spikes/spike-5-firestore-state/decision.md) |
| Realtime 購読の方式 | **確定** — `doc_ref.on_snapshot(cb)` 採用、p50 48ms。詳細は §4.3 | [`spikes/spike-5-firestore-state/decision.md`](../../spikes/spike-5-firestore-state/decision.md) |
| `next_event_seq` の原子的採番 | **TBD-Phase-1** — spike では caller-side counter で代用。本番では state transition と同じ tx 内でインクリメント | [`spikes/spike-5-firestore-state/decision.md`](../../spikes/spike-5-firestore-state/decision.md) §残課題 |
| CodingEnginePort 抽象 | **確定** — `packages/agents/coding/engine.py` に PR#16 でマージ済。詳細は §4.4 | [`spikes/spike-6-coding-engine/decision.md`](../../spikes/spike-6-coding-engine/decision.md) |
| `ports.a2a` の必要メソッド集合 | **未確定** — A2A 仕様確認後 | [`spikes/spike-8-a2a-sdk/`](../../spikes/spike-8-a2a-sdk/) |
| LLM session の永続化方式 | **TBD-Phase-1** — MVP は `InMemorySessionService`、Firestore-backed か `VertexAiSessionService` を Phase 1 で判断 | [`spikes/spike-2-adk-gemini/decision.md`](../../spikes/spike-2-adk-gemini/decision.md) §NoGo にはならなかったが要注意 |

---

## 11. 参考: 各案を不採用にした余白

- **Clean Architecture**: 同じ思想だが用語（Use Case / Entity / Interface Adapters / Frameworks & Drivers）が重く、Web 開発者にとって Hexagonal の Port/Adapter のほうが直感的。本書では Clean の **依存逆転原則** だけ採用。
- **Vertical Slice**: 機能数が増えた段階で再評価する価値あり。MVP では Issue / PR / Charter / Deploy の関心が orchestrator にまたがるため slice にしづらい。
- **Layered**: 既に [`docs/app-architecture.md`](../app-architecture.md) で似た形を提示済。本書はその延長として依存制御を強化する位置づけ。

---

## 12. 更新ルール

- 本書のアーキテクチャ変更は **`docs/app-architecture.md` の対応節を同時に更新**
- `domain/` のシグネチャ変更は最も慎重に（テストでロックする）
- 新しい Port を増やすときは「**既存 Port で吸収できないか**」を 1 度問う

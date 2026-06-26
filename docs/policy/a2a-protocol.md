# A2A プロトコル統合ポリシー（v0.3）

- 最終更新: 2026-06-23
- ステータス: Draft v0.3（仕様 v1.0.0 / **SDK v1.1.0 検証済**、spike-8 反映、2026-06-23 時点）
- 親: [`docs/planning.md`](../planning.md) §8 / §10
- 関連: [`docs/policy/templates.md`](templates.md) §6 / [`docs/policy/backend-architecture.md`](backend-architecture.md) §2
- 仕様参照先（一次情報）:
  - 仕様サイト: https://a2a-protocol.org/latest/specification/
  - GitHub: https://github.com/a2aproject/A2A（Apache 2.0、Linux Foundation 配下）
  - Python SDK: `pip install a2a-sdk`
  - JS SDK: `npm install @a2a-js/sdk`（他に Go / Java / .NET / Rust も配布）
- 対象読者: 開発者本人 + Claude Code

---

## 0. このドキュメントの目的

PoC Foundry が改善する **Managed Agent を A2A プロトコル準拠の "サーバ" として常に立てる** 方針と、その実装上の規約を確定する。

- **Managed Agent 側**: AgentCard を公開し、JSON-RPC エンドポイントを実装。テンプレートが雛形を注入。
- **Foundry 側**: Managed Agent を **A2A クライアントとして呼ぶ**（改善後の動作検証、Phase 5+）。

---

## 1. なぜ A2A か

選択肢:

| 案 | 評価 |
|---|---|
| **A2A プロトコル**（採用） | 2025-04 に Google が公開、2025-06 に **Linux Foundation 配下**へ移管。2026-04 時点で **150 組織以上が支持**（Microsoft / AWS / Salesforce / SAP / ServiceNow / IBM など）。Azure AI Foundry / Amazon Bedrock AgentCore / Google Cloud が native 統合済み |
| OpenAPI + 独自 REST | 標準化が弱い。Foundry 個別仕様になる |
| MCP（Model Context Protocol） | "ツール提供" が主目的。Agent そのものの呼び出しには別物（A2A と相補的） |
| LangGraph 等独自プロトコル | エコシステム閉鎖的 |

採用理由:
1. Managed PoC が **AI Agent 系**である場合、A2A で呼べると **第三者からも利用可能**になる
2. Foundry 自身が **改善後の Agent を A2A クライアントとして検証** できる（受入条件の自動チェック）
3. AI Agent 系でなくても A2A サーバを **任意活性化** にすれば普通の web app テンプレと共存できる
4. Apache 2.0 / 中立な Foundation 配下なので、ベンダーロックなし

---

## 2. A2A プロトコルの確定事実

### 2.1 トランスポート（確定）

- **JSON-RPC 2.0 over HTTPS**（同期 request/response）
- **Server-Sent Events (SSE)** で streaming（任意）
- **Async Push Notifications** 経路もあり（任意、コールバック URL を agent に登録）
- gRPC / HTTP REST 経路も spec に存在するが MVP では **JSON-RPC のみ採用**

### 2.2 AgentCard（確定）

固定 URL で配信。**`agent-card.json`**（`agent.json` ではない）:

```
GET https://<agent-host>/.well-known/agent-card.json
```

**top-level フィールド**（spike-8 検証, 2026-06-23 — `a2a.compat.v0_3.types.AgentCard` Pydantic モデル由来。必須 8 / 任意 10）:

```jsonc
{
  // ── 必須（8 個）──
  "name": "string",                          // 必須
  "description": "string",                   // 必須
  "url": "string",                           // 必須。A2A endpoint root
  "version": "string",                       // 必須（semver 推奨）
  "capabilities": {                          // 必須（中身は任意）
    "streaming": false,                      // tasks streaming 対応
    "pushNotifications": false,              // push 対応
    "stateTransitionHistory": false          // 履歴公開
  },
  "defaultInputModes":  ["text/plain"],      // 必須
  "defaultOutputModes": ["text/plain"],      // 必須
  "skills": [                                // 必須（少なくとも 1 個）
    {
      "id":          "answer-inquiry",
      "name":        "Answer Inquiry",
      "description": "...",
      "tags":        ["support"],
      "examples":    ["..."],                // 任意
      "inputModes":  ["text/plain"],         // 任意（default を override）
      "outputModes": ["application/json"]    // 任意
    }
  ],

  // ── 任意（10 個）──
  "provider": {                              // 任意
    "organization": "string",
    "url": "string"
  },
  "documentationUrl": "string",              // 任意
  "iconUrl": "string",                       // 任意
  "protocolVersion": "0.3.0",                // 任意（spike-8 サンプルは "0.3.0"）
  "preferredTransport": "JSONRPC",           // 任意（MVP テンプレ規約: "JSONRPC" を明示）
  "additionalInterfaces": [                  // 任意（追加 transport を宣言）
    /* AgentInterface[] */
  ],
  "security": [                              // 任意（OpenAPI 形式：要求リスト）
    { "bearerAuth": [] }
  ],
  "securitySchemes": {                       // 任意（OpenAPI 形式：定義マップ）
    "bearerAuth": { /* SecurityScheme */ }
  },
  "signatures": [ /* AgentCardSignature[] */ ],   // 任意
  "supportsAuthenticatedExtendedCard": false      // 任意（true なら拡張カード取得をサポート）
}
```

> **重要な差分（spike-8 検証, 2026-06-23）**:
> - 旧 policy にあった top-level `authentication` フィールドは **v0.3 Pydantic モデルには存在しない**。代わりに OpenAPI 形式の `security` (要求リスト) + `securitySchemes` (定義マップ) の **2 フィールド構成**。**両方とも任意**。
> - 追加発見フィールド: `additionalInterfaces` / `signatures` / `iconUrl` / `protocolVersion` / `preferredTransport` / `supportsAuthenticatedExtendedCard`。
> - MVP テンプレでは `preferredTransport="JSONRPC"` を明示推奨（spike-8 サンプルでもこの値で配信）。

**Extended AgentCard**（任意）: 認証済みクライアントだけに見せる拡張版。`supportsAuthenticatedExtendedCard` が true なら `agent/getAuthenticatedExtendedCard` で取得（wire string 確定、spike-8）。

### 2.3 JSON-RPC メソッド（確定）

**確定（spike-8 検証済 a2a-sdk v1.1.0, 2026-06-23）** — すべて `a2a.compat.v0_3.types` 配下の Request クラスの `method` Literal から取得:

| 用途 | SDK Request クラス | wire `method`（確定） |
|---|---|---|
| メッセージ送信（同期） | `SendMessageRequest` | `message/send` |
| メッセージ送信（SSE streaming） | `SendStreamingMessageRequest` | `message/stream` |
| タスク取得 | `GetTaskRequest` | `tasks/get` |
| タスクキャンセル | `CancelTaskRequest` | `tasks/cancel` |
| タスク再購読（SSE 再接続） | `TaskResubscriptionRequest` | `tasks/resubscribe` |
| Push 通知設定 set | `SetTaskPushNotificationConfigRequest` | `tasks/pushNotificationConfig/set` |
| Push 通知設定 get | `GetTaskPushNotificationConfigRequest` | `tasks/pushNotificationConfig/get` |
| Push 通知設定 list | `ListTaskPushNotificationConfigRequest` | `tasks/pushNotificationConfig/list` |
| Push 通知設定 delete | `DeleteTaskPushNotificationConfigRequest` | `tasks/pushNotificationConfig/delete` |
| 拡張 AgentCard 取得 | `GetAuthenticatedExtendedCardRequest` | `agent/getAuthenticatedExtendedCard` |

> 補足（spike-8 検証, 2026-06-23）: 仕様サイト本文では `tasks/pushNotificationConfig/list` と `tasks/pushNotificationConfig/delete` は §2.3 で明示列挙されていないが、SDK には対応 Request クラスが存在し wire string も確定済。`tasks/list`（タスク一覧）は SDK 上に対応 Request クラスが存在せず、A2A v0.3 では**未提供メソッド**。

### 2.4 Task オブジェクト（確定）

`Task` の主要フィールド（spec §4.1.1 確認済）:

```jsonc
{
  "id":         "string",        // タスク ID
  "contextId":  "string",        // 会話 / セッション ID
  "status":     { "state": "...", "timestamp": "..." },  // TaskStatus
  "artifacts":  [ /* Artifact[] */ ],
  "history":    [ /* Message[] */ ],
  "metadata":   { /* free-form */ }
}
```

### 2.5 TaskState（確定 — lowercase + kebab-case）

**確定（spike-8 検証済 a2a-sdk v1.1.0, 2026-06-23）** — `a2a.compat.v0_3.types.TaskState` Enum から取得:

| 仕様 protobuf 定数 | Python enum メンバ | **JSON wire 値（確定）** |
|---|---|---|
| `TASK_STATE_SUBMITTED` | `submitted` | `"submitted"` |
| `TASK_STATE_WORKING` | `working` | `"working"` |
| `TASK_STATE_INPUT_REQUIRED` | `input_required` | `"input-required"` |
| `TASK_STATE_COMPLETED` | `completed` | `"completed"` |
| `TASK_STATE_FAILED` | `failed` | `"failed"` |
| `TASK_STATE_CANCELED` | `canceled` | `"canceled"` |
| `TASK_STATE_REJECTED` | `rejected` | `"rejected"` |
| `TASK_STATE_AUTH_REQUIRED` | `auth_required` | `"auth-required"` |
| —（SDK 追加、spec §4.1.3 protobuf 未記載） | `unknown` | `"unknown"` |

> **重要（spike-8 検証, 2026-06-23）**:
> - wire 形式は **lowercase + kebab-case（ハイフン）**。`"inputRequired"` / `"INPUT_REQUIRED"` / `"input_required"` は **誤り**。
> - Python enum メンバ名（`input_required`、`auth_required` — snake_case）と JSON wire 値（`"input-required"`、`"auth-required"` — kebab-case）の**表記揺れ**があるため、シリアライズは SDK 任せにすること（自前の文字列構築は禁則）。
> - `unknown` は SDK には存在するが、spec §4.1.3 の protobuf 定数には未記載。SDK 経由なら受信可能。

### 2.6 Message と Part（確定 — RootModel union + `kind` discriminator）

**確定（spike-8 検証済 a2a-sdk v1.1.0, 2026-06-23）** — `a2a.compat.v0_3.types.Part` は **`RootModel[TextPart | FilePart | DataPart]`** であり、各バリアントは `kind` 文字列を discriminator として持つ。

```python
# a2a.compat.v0_3.types.Part = RootModel[TextPart | FilePart | DataPart]
```

各バリアントの wire 形式（spike-8 で実測）:

```jsonc
// TextPart
{ "kind": "text", "text": "hello" }

// FilePart（URI 版） — file は FileWithUri
{
  "kind": "file",
  "file": { "uri": "https://example.com/a.pdf", "mimeType": "application/pdf" }
}

// FilePart（bytes 版・base64） — file は FileWithBytes
{
  "kind": "file",
  "file": { "bytes": "<base64>", "mimeType": "application/pdf" }
}

// DataPart
{ "kind": "data", "data": { "city": "Tokyo" } }
```

> **重要な差分（spike-8 検証, 2026-06-23）**:
> - 旧 policy の「単一 `Part` 型に OneOf フィールド `text` / `raw` / `url` / `data`」記述は **誤り**。
> - 実体は **RootModel union（TextPart / FilePart / DataPart）** + 各 variant に `kind` discriminator。
> - ファイルは `text` / `raw` ではなく **`FilePart.file: FileWithUri | FileWithBytes`** という**入れ子の union**。`file.uri` か `file.bytes` のどちらかが入る。
> - シリアライザ任せにする運用（手書きで JSON を組み立てない）。

Message 自体の wire 形（spike-8 ライブ観測）:

```jsonc
{
  "kind": "message",
  "messageId": "...uuid...",
  "role": "user",                            // または "agent"
  "parts": [ /* Part[] */ ]
}
```

### 2.7 Artifact（概要）

`artifacts` フィールドはタスクの **生成物**（添付ファイル・構造化結果など）。詳細フィールドは spec §4.1.7 で参照可能（取得時に SDK 例で確認）。

### 2.8 認証スキーム（OpenAPI 形式の `securitySchemes` / `security`）

**確定（spike-8 検証, 2026-06-23）** — v0.3 Pydantic モデルでは AgentCard 直下に `authentication` は無く、OpenAPI 同様の **2 フィールド構成**で表現する:

- `securitySchemes`: スキーム定義のマップ（`dict[str, SecurityScheme]`）。
- `security`: 要求リスト（`list[dict[str, list[str]]]`）。クライアントが満たすべき条件を OR で並べる。

サポートされる `SecurityScheme` の種類（仕様で定義済）:

- `apiKey`
- HTTP Auth（Bearer / Basic）
- OAuth2
- OpenID Connect
- Mutual TLS

MVP は **Bearer**（API キー or Firebase ID Token）で開始。AgentCard では次のように記述する:

```jsonc
{
  "securitySchemes": {
    "bearerAuth": { "type": "http", "scheme": "bearer" }
  },
  "security": [
    { "bearerAuth": [] }
  ]
}
```

---

## 3. Managed Agent 側の実装規約（テンプレ）

`templates/modules/a2a-server-python/` が注入する物（Python の例）:

### 3.1 ディレクトリ

```
src/
├─ interface/
│  └─ a2a/
│     ├─ __init__.py
│     ├─ server.py           # a2a-sdk Server を FastAPI / ASGI に mount
│     ├─ agent_card.py       # AgentCard を返す
│     ├─ handlers.py         # message/send / tasks/get を application/ に転送
│     └─ types.py            # SDK 型の再 export（薄ラッパ）
└─ application/
   └─ a2a/
      └─ task_runner.py      # ユースケースとして A2A タスクを処理
a2a/
└─ agent-card.json           # 静的 AgentCard サンプル（テスト用。本番は agent_card.py が動的生成）
```

### 3.2 SDK の利用

**確定（spike-8 検証, 2026-06-23 — a2a-sdk v1.1.0）** — `a2a.server` トップレベルに `A2AServer` クラスは**存在しない**。FastAPI mount パターン（`add_a2a_routes_to_fastapi` + `create_*_routes`）を正とする。Pydantic 型は `a2a.compat.v0_3.types` を、サーバ実装は `a2a.server.*` 配下を import する:

```python
# Python（a2a-sdk）— pip install a2a-sdk==1.1.0

# Pydantic wire 型（クライアント / 検証用、JSON wire の source of truth）
from a2a.compat.v0_3.types import (
    AgentCard, AgentCapabilities, AgentSkill,
    Part, TextPart, FilePart, DataPart,
    Message, TaskState,
)

# サーバ実装（protobuf AgentCard を渡す FastAPI mount パターン）
from a2a.types import AgentCard as ProtoAgentCard
from a2a.server.agent_execution import AgentExecutor
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.routes import (
    add_a2a_routes_to_fastapi,
    create_agent_card_routes,
    create_jsonrpc_routes,
)
```

> **重要（spike-8 検証, 2026-06-23）**:
> - **JSON wire 形式の source of truth は `a2a.compat.v0_3.types`**（Pydantic v2）。
> - サーバ側 `DefaultRequestHandler` は **protobuf 版 `AgentCard`**（`a2a.types.AgentCard`）を要求する。そのため Pydantic と protobuf の **2 つの AgentCard モデルが併存**する点に注意。テンプレ側の `agent_card.py` では「protobuf を組み立てて Pydantic にも変換するヘルパ」を提供するのが安全。
> - `enable_v0_3_compat=True` で JSON-RPC エンドポイントを v0.3 互換モードに切り替える（現状ほぼ必須）。

```typescript
// TypeScript（@a2a-js/sdk）
// npm install @a2a-js/sdk
import { A2AServer, AgentCard } from "@a2a-js/sdk";
// 注: JS SDK の対応 import / mount API は Phase 3 着手時に follow-up spike（spike-8b）で確認する。
```

公式 SDK 採用方針: **可能な限り SDK が提供する型・サーバ実装を使う**。手書きの JSON 整形は禁則（schema drift の温床）。

### 3.3 mount

**確定（spike-8 検証, 2026-06-23）** — `/.well-known/agent-card.json` と JSON-RPC エンドポイントを **既存 web/api と同じ FastAPI app に mount**。`add_a2a_routes_to_fastapi` 経由でルート工場を渡す:

```python
# src/interface/http/main.py
from fastapi import FastAPI

from a2a.types import AgentCard as ProtoAgentCard
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import (
    add_a2a_routes_to_fastapi,
    create_agent_card_routes,
    create_jsonrpc_routes,
)

app = FastAPI()

proto_card: ProtoAgentCard = build_proto_agent_card()       # テンプレが提供
handler: DefaultRequestHandler = build_request_handler()    # AgentExecutor を内包

add_a2a_routes_to_fastapi(
    app,
    agent_card_routes=create_agent_card_routes(proto_card),
    jsonrpc_routes=create_jsonrpc_routes(
        handler,
        rpc_url="/",                  # 例: A2A エンドポイントを root に置く場合
        enable_v0_3_compat=True,      # JSON-RPC を v0.3 互換で公開
    ),
)
# /.well-known/agent-card.json は create_agent_card_routes が定義する
# JSON-RPC は rpc_url に POST（spike-8 では "/" で実測）
```

> `rpc_url` をサブパス（例 `"/a2a"`）に変える場合は、AgentCard `url` フィールドにも同じパスを反映すること（spike-8 検証, 2026-06-23）。

### 3.4 handler の薄さ

```python
# src/interface/a2a/handlers.py
async def handle_message_send(req):
    # 入力 Message を application 側の input 形式に変換
    input_ = _to_application_input(req.message)
    # ユースケース呼び出し
    output = await application.a2a.task_runner.run(input_, task_id=req.task_id)
    # output を A2A 形式に変換
    return _to_a2a_result(output)
```

**ガードレール**:
- handler 内に **業務ロジックを書かない**（application/ に投げる）
- error は SDK が提供する error 型を使う（自前の JSON-RPC error 構築禁止）
- **secret を Part の data に詰めない**

### 3.5 認証

- AgentCard で `securitySchemes = {"bearerAuth": {"type": "http", "scheme": "bearer"}}` を宣言し、`security = [{"bearerAuth": []}]` を要求として並べる（spike-8 検証, 2026-06-23 — 旧 `authentication.schemes` フィールドは v0.3 Pydantic モデルから消えている）
- MVP は Bearer（API キー or Firebase ID Token）
- `preferredTransport = "JSONRPC"` を明示（spike-8 サンプル準拠）
- 401 は SDK のエラー型で返す

### 3.6 streaming（任意）

`AgentCard.capabilities.streaming = true` 時のみ `message/stream`（SSE）を実装。テンプレ展開フラグ `has_streaming` で活性化。MVP の Managed PoC では同期 `message/send` のみで十分。

---

## 4. Foundry 側の A2A クライアント

[`docs/policy/backend-architecture.md`](backend-architecture.md) §2 の `ports.a2a` を adapter `a2a_http` が実装する。

```python
# ports/a2a.py
class A2aClient(Protocol):
    async def fetch_agent_card(self, base_url: str) -> AgentCard: ...
    async def send_message(self, base_url: str, params: MessageSendParams, *, auth: str) -> TaskResult: ...
    async def get_task(self, base_url: str, task_id: str, *, auth: str) -> Task: ...
    async def cancel_task(self, base_url: str, task_id: str, *, auth: str) -> None: ...
```

実装は **`a2a-sdk` のクライアントクラスをラップ**するだけにする（手書き HTTP 禁止）。

### 4.1 何に使うか

- **Charter の受入条件検証**: `acceptanceCriteria` を A2A の `message/send` で投げて期待出力と比較（自動 e2e）
- **Self-Improvement Agent の現状観測**: 改善前後で AgentCard と振る舞いを比較
- **Demo シナリオ §11**: 改善後 Managed Agent を実際に Foundry UI から触る

### 4.2 認証情報の管理

- Managed Agent ごとに access credentials を Secret Manager に格納
- Firestore `agents/{id}.a2a` に `{base_url, auth_secret_id, agent_card_cached}` を保存
- AgentCard は **TTL 1 時間で再取得**（agent 側のリビジョン更新を反映）

---

## 5. AgentCard の動的生成

Profile / Charter / git tag から AgentCard を自動生成する規約:

| AgentCard フィールド | 由来 |
|---|---|
| `name` | `Profile.name` または `agents/{id}.name` |
| `description` | `Charter.whatItDoes` |
| `provider.organization` | `"poc-recycle"` 固定 |
| `version` | `git describe --tags` or `0.0.<commit-count>` |
| `protocolVersion` | `"0.3.0"` 固定（spike-8 検証時のバージョン） |
| `preferredTransport` | `"JSONRPC"` 固定（MVP テンプレ規約） |
| `capabilities.streaming` | テンプレ展開時の `has_streaming` フラグ |
| `securitySchemes` | 既定 `{"bearerAuth": {"type": "http", "scheme": "bearer"}}`（spike-8 検証, 2026-06-23） |
| `security` | 既定 `[{"bearerAuth": []}]` |
| `defaultInputModes` / `defaultOutputModes` | Profile.inputFormat / outputFormat から推定 |
| `skills[]` | `Profile.useCases` から 1 use case = 1 skill |

→ `agent_card.py` がランタイムで組み立てる（静的 JSON より柔軟）。生成時は **protobuf 版 `AgentCard`**（`DefaultRequestHandler` 用）と **Pydantic 版 `AgentCard`**（クライアント検証用）の双方を整合させること。

---

## 6. CI で AgentCard を検証

Managed Repo の ci.yml に追加（テンプレが注入）:

```yaml
- name: Validate AgentCard
  run: |
    python -m src.interface.a2a.agent_card --dump > /tmp/agent-card.json
    # 公式 schema validator を pip install してチェック
    a2a-sdk validate-card /tmp/agent-card.json   # ⚠ コマンド名は SDK で要確認
```

公式 validator のコマンド名は **SDK の bin を Phase 3 で確認**して確定。

---

## 7. 残りの要確認項目（spike-8 で大半解消）

spike-8（2026-06-23, `a2a-sdk==1.1.0`）の検証で**確定済**となった項目と、引き続き**保留**の項目:

| 項目 | 状態 | 補足 |
|---|---|---|
| JSON-RPC メソッドの正確な wire string | **確定（spike-8 / a2a-sdk v1.1.0）** | §2.3 の表に集約。`pushNotificationConfig/list` と `/delete` を追加発見 |
| TaskState の JSON wire 値 | **確定（lowercase + kebab）** | §2.5。`unknown` も SDK 上に存在 |
| Part の wire 形式 | **確定（RootModel + `kind` discriminator）** | §2.6。`FilePart.file: FileWithUri \| FileWithBytes` の入れ子 |
| AgentCard の必須/任意フィールド一覧 | **確定（必須 8 / 任意 10）** | §2.2。`authentication` は廃止、`security` + `securitySchemes` に置換 |
| Authentication の wire 形 | **確定（OpenAPI 形式の `securitySchemes` + `security`）** | §2.8 / §3.5 |
| Artifact の詳細フィールド | **保留** | 本スパイクの対象外。Phase 3 着手前に追加スパイクで確認 |
| AgentCard validator の CLI 名 | **保留** | SDK には `a2a-db-cli` あり。validator は別途確認 |
| Push Notifications の callback URL 登録手順 | **保留** | MVP では未採用方針のため未確認 |
| JS SDK (`@a2a-js/sdk`) の同等確認 | **保留（spike-8b として別 issue 化予定）** | Python 側で確定したため blocker ではない |

> SDK version verified: `a2a-sdk==1.1.0` (spike-8, 2026-06-23). See `spikes/spike-8-a2a-sdk/` for raw probe data.

---

## 8. 採用ルール（短く）

1. Managed Agent は **テンプレ展開時に `has_a2a_server` を ON**（AI Agent 系・混合系では既定 ON）
2. **AgentCard は動的生成**（Profile / Charter / git tag から）、`/.well-known/agent-card.json` で配信
3. **公式 SDK（`a2a-sdk` / `@a2a-js/sdk`）を使う**、手書き JSON-RPC 構築を禁止
4. **handler は薄く**、業務ロジックは `application/a2a/` に置く
5. Foundry 側は `ports.a2a` 経由でクライアント呼び出し、adapter は SDK ラッパ
6. **secret を Message Part に詰めない**
7. AgentCard の breaking change を起こす変更は **Managed Repo の段階移行ガイド付き** で行う

---

## 9. 実装ロードマップ

| Phase | やること |
|---|---|
| **Phase S** | **完了（spike-8, 2026-06-23）** — `a2a-sdk==1.1.0` で最小サーバ起動 + raw JSON-RPC 1 往復、wire string / TaskState / Part / AgentCard を確定 |
| Phase 3（Repo / Issue） | `has_a2a_server=true` のときテンプレが A2A 雛形を注入する Repo Agent 実装 |
| Phase 4（Coding） | Coding Agent が A2A 関連ファイルの diff cap / out_of_scope 規約を尊重するよう確認 |
| Phase 5（Deploy + 検証） | Foundry の A2A クライアントから deployed Managed Agent を呼ぶ受入テスト |
| Phase 6+（Self-Improvement） | 改善前後で AgentCard 差分検知、振る舞い差分テスト自動化 |

---

## 10. 更新ルール

- `⚠ 残り要確認項目` を解消したら本書を更新（推定 → 確定に格上げ）
- A2A 仕様が breaking change を出した場合、本書 + `templates/modules/a2a-server-*` + Managed Repo migration guide を **同時更新**
- 公式 SDK のメジャー更新時は依存バージョンを `templates/` の lockfile に反映

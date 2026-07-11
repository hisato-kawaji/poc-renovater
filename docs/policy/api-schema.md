# API スキーマ ポリシー（叩き台 v0.1）

- 最終更新: 2026-06-22
- ステータス: Draft v0.1
- 親: [`docs/planning.md`](../planning.md) §7 / [`docs/app-architecture.md`](../app-architecture.md)
- 対象読者: 開発者本人 + Claude Code

---

## 0. このドキュメントの目的

フロント (Next.js) ↔ API (FastAPI) の通信形式を確定する。具体的には:

1. REST / GraphQL / gRPC / tRPC / JSON-RPC / WebSocket の比較と推奨
2. スキーマの **正本**（packages/shared にどの形で置くか）
3. エラー / ページング / 冪等性 / バージョニング / リアルタイム の扱い方
4. **A2A は別レイヤ**（[`a2a-protocol.md`](a2a-protocol.md)）として切り出し、本書は Foundry 内部 API を対象

---

## 1. 選択肢比較

### 1.1 候補

| 候補 | 一行説明 |
|---|---|
| **REST + JSON**（OpenAPI） | リソース志向、HTTP 文法を素直に活かす。Python/TS とも標準 |
| **GraphQL** | クエリ言語で client が必要なフィールドを選ぶ。複雑 UI に強い |
| **gRPC** | Protocol Buffers + HTTP/2。型強制が強い、ブラウザは gRPC-Web |
| **tRPC** | TS↔TS の関数呼び出し感覚。end-to-end 型推論が売り |
| **JSON-RPC** | 1 endpoint で method 名を切る簡易プロトコル |
| **WebSocket** | 双方向リアルタイム。Auth・スケールに工夫が要る |
| **Server-Sent Events (SSE)** | 単方向 push、HTTP 上で動く |

### 1.2 我々の要件

| 要件 | 重要度 |
|---|---|
| Pydantic スキーマを **API / web 両方が共有** | 高 |
| FastAPI 既定の OpenAPI ドキュメント自動生成を活かす | 高 |
| Firestore listener で **リアルタイム更新は API を介さない** | 高（これが live の主役） |
| 学習コストが低く、Claude のテスト生成が安定する | 高 |
| ファイル（zip）アップロードを扱う | 中 |
| 将来 A2A / 第三者連携を容易にする | 中 |
| 強い型（コンパイル時検査）が欲しい | 中 |
| client-driven query | 低（uploader / charter / pulls などは UI 主導でない） |

### 1.3 スコアリング

| 軸 | REST | GraphQL | gRPC | tRPC | JSON-RPC |
|---|---|---|---|---|---|
| スキーマ共有（Pydantic→JSON Schema） | ◎ | ○ | △（proto 生成が必要） | × (TS↔TS) | ○ |
| FastAPI 親和性 | ◎ | △ | △ | × | ○ |
| ブラウザ互換 | ◎ | ◎ | △（gRPC-Web 必要） | ◎ | ◎ |
| 学習コスト | ◎ | △ | △ | ○ | ◎ |
| ファイル UP | ◎ | △ | △ | △ | △ |
| 強い型 | ○ | ◎ | ◎ | ◎ | △ |
| リアルタイム | × | △（subs） | ◎（streaming） | ○ | × |
| OpenAPI 自動生成 | ◎ | – | – | – | – |

リアルタイムは **Firestore listener に寄せる**ため、API 側で WS/SSE/streaming は不要。よってリアルタイム軸は実質スコープ外。

### 1.4 採用

**REST + JSON**。理由:

1. **API は資源操作**（agents / charter / issues / pulls / deployments / uploads）。GET/POST の HTTP 動詞でほぼ表現できる。`/api/agents/{id}:finalize` のような **副作用操作は `:verb` サフィックス**で許容（Google API Design Guide 流）。
2. **Pydantic v2 → JSON Schema → web で zod 化**の一方向経路が綺麗。これがフロント・バックの **唯一のスキーマソース**。
3. **ファイルアップロード**（zip）は multipart で素直。
4. **OpenAPI 自動生成**を FastAPI が無料で出す。`/openapi.json` を web 側の build-time 検証や CI のスキーマ差分検知に使える。
5. **学習コストが低い**。Claude のテスト生成も安定。

GraphQL や gRPC の利点は、本プロジェクトの規模では **ROI が出ない**。

### 1.5 採用しない案の余白

- **GraphQL**: client-driven query が要らないので、N+1 / 認可ロジックの複雑化を払うほどの利得がない
- **gRPC**: ブラウザ向けに gRPC-Web ゲートウェイが必要、proto 生成 CI を背負うコストが過剰
- **tRPC**: バックエンドが Python なので適用不可
- **JSON-RPC**: REST と比べた強い動機がない（HTTP 動詞・URL の意味づけを捨てるトレードオフが見合わない）
- **WebSocket / SSE**: リアルタイムは Firestore 任せ。API は副作用要求のみで完結

---

## 2. スキーマの正本

### 2.1 配置

```
packages/shared/
├─ python/poc_renovater_shared/      # Pydantic v2（API の正本）
│  ├─ agent.py
│  ├─ profile.py
│  ├─ charter.py
│  ├─ issue.py
│  ├─ pull.py
│  ├─ deployment.py
│  ├─ event.py
│  ├─ errors.py                    # エラーエンベロープ
│  └─ pagination.py
├─ ts/                              # 生成物（手で書かない）
│  └─ src/
│     ├─ schemas/                   # JSON Schema (.json)
│     ├─ types.ts                   # json-schema-to-typescript 生成
│     └─ runtime.ts                 # zod ヘルパ
└─ scripts/
   └─ emit_schemas.py               # 生成スクリプト
```

### 2.2 出力フロー

```
Pydantic v2 BaseModel.model_json_schema()  →  *.schema.json  →  json-schema-to-typescript / zod
```

- TS は **生成物のみ**。手書き型は禁止
- フロントは `import { AgentSchema, type Agent } from "@poc-renovater/shared"` で読む
- 受信した JSON は **必ず schema.parse(json) で narrow**（`any` 禁止）

### 2.3 命名規約

- **snake_case** で API/JSON 両方を統一。TS 側も snake_case。camelCase 変換はしない（変換層を作らない）
- DTO は `<Resource>` / 入力は `<Resource>CreateInput` / 部分更新は `<Resource>PatchInput`
- 列挙は `StrEnum`（Python）/ `z.enum([...])`（TS）

---

## 3. URL と動詞の規約

### 3.1 リソース URL

```
GET    /api/v1/agents
GET    /api/v1/agents/{agent_id}
POST   /api/v1/agents:analyze                   # 副作用動詞
POST   /api/v1/agents/{agent_id}:register
POST   /api/v1/agents/{agent_id}:stop
GET    /api/v1/agents/{agent_id}/charter/messages
POST   /api/v1/agents/{agent_id}/charter/messages
POST   /api/v1/agents/{agent_id}/charter:finalize
GET    /api/v1/agents/{agent_id}/issues
POST   /api/v1/agents/{agent_id}/issues:plan
POST   /api/v1/agents/{agent_id}/issues/{n}:implement
GET    /api/v1/agents/{agent_id}/pulls
POST   /api/v1/agents/{agent_id}/pulls/{n}:review
POST   /api/v1/agents/{agent_id}/pulls/{n}:deploy-preview
POST   /api/v1/agents/{agent_id}/pulls/{n}:approve
POST   /api/v1/uploads                          # multipart
POST   /api/v1/webhooks/github
POST   /api/v1/webhooks/cloudbuild
```

### 3.2 バージョニング

- URL prefix `/api/v1/`
- **breaking change は v2/ を立てて並走**、v1 は最低 1 リリース残す
- 非破壊変更（フィールド追加）は v1 で扱う

### 3.3 副作用動詞のサフィックス `:verb`

リソースとして表せない処理は `/{resource}:verb` で表現:
- 状態遷移を起こす（`:register` / `:finalize` / `:approve` / `:stop`）
- 派生操作（`:implement` / `:review` / `:deploy-preview`）

これにより `POST /resources` を「新規作成」に限定し、状態遷移と区別できる。

---

## 4. リクエスト/レスポンス契約

### 4.1 全レスポンスの共通形式

ペイロードは **裸の JSON オブジェクト**（`{ "id": ..., ... }`）。**ラッパー（`{data: ...}` など）は使わない**。理由: OpenAPI / Pydantic / zod のいずれもネスト無しが扱いやすい。

ページング付きリストだけ例外:

```json
{
  "items": [ ... ],
  "next_cursor": "string|null",
  "has_more": false
}
```

### 4.2 エラーエンベロープ

```json
{
  "code": "foundry/charter-gate-not-passed",
  "message": "Charter score 60 is below threshold 80",
  "details": {
    "score": 60,
    "threshold": 80,
    "missing": ["acceptanceCriteria", "outOfScope"]
  },
  "request_id": "01J..."
}
```

- `code`: `foundry/...` ネームスペースで階層化
- `message`: 人間可読（i18n は MVP では未実装）
- `details`: structured な追加情報（オプショナル）
- `request_id`: middleware が付ける同一 ID

HTTP ステータスは `FoundryError` の `http_status` に従う（[`app-architecture.md`](../app-architecture.md) §2.3 参照）。

### 4.3 ページング

- **cursor ベース**。offset/limit は使わない（Firestore に合わせる）
- クエリ: `?limit=20&cursor=<opaque>`
- `next_cursor` を返す。`null` なら最後

### 4.4 冪等性

POST で **副作用がある**エンドポイントは冪等キーをサポート:

```
POST /api/v1/agents:analyze
Idempotency-Key: 01J...

→ サーバは (Idempotency-Key, upload_id, principal) の組で 24h キャッシュ。重複なら同じ結果を返す
```

対象エンドポイント:
- `agents:analyze`
- `agents/{id}:register`
- `issues/{n}:implement`
- `pulls/{n}:deploy-preview`
- `pulls/{n}:approve`

実装は middleware で Firestore コレクション `idempotency/{key}` に判定キャッシュを持つ。

### 4.5 認証

- ヘッダ: `Authorization: Bearer <Firebase ID token>`
- 失敗は 401 + `code=foundry/unauthenticated`
- **Webhook ルートはバイパス** → HMAC で代替検証

### 4.6 ファイルアップロード

`POST /api/v1/uploads` は `multipart/form-data`、フィールド名 `file`。最大サイズは middleware で 100MB に制限。レスポンスは `{ upload_id, size, sha256 }`。

---

## 5. リアルタイム更新の方針（API ではなく Firestore）

### 5.1 役割分担

| 種類 | 担当 |
|---|---|
| 副作用要求 | API（REST POST） |
| 一覧/詳細の最新取得 | API（GET）+ Firestore onSnapshot |
| 進行状況のライブ表示 | **Firestore onSnapshot 直接**（onSnapshot は web の Firebase SDK） |
| 通知（バッジ更新） | Firestore onSnapshot |

→ **API には WebSocket / SSE を実装しない**。実装しても二重維持になる。

### 5.2 セキュリティ

- Firestore セキュリティルールで `ownerId == request.auth.uid` をチェック
- フロントが onSnapshot で参照できるのは「自分の agents」だけ
- write は **常に API 経由**にする（フロントから Firestore に直接 write はしない）

---

## 6. OpenAPI

### 6.1 自動生成

FastAPI が `/openapi.json` を出す。手で `openapi.yaml` を維持しない。

### 6.2 利用

- 開発時: `/docs` で Swagger UI
- CI: 1 つ前のコミットと **openapi.json の diff** を取り、breaking change を検知（フィールド削除・required 追加・enum 削減）
- 検出は単純な diff スクリプトで十分（差分が出たら人間レビュー）

### 6.3 公開

MVP 中は社内のみ。公開時は v1 を固定して別パスにマウント。

---

## 7. テストでの契約検証

- 各 router は **Schemathesis** で OpenAPI からプロパティテストを生成（推奨）
- 重要エンドポイントは **golden response テスト**（json snapshot）で固定
- フロント側は `@poc-renovater/shared` の zod スキーマで **受信時に必ず parse**（失敗 = テスト失敗）

---

## 8. ⚠ 未確定項目

| 項目 | 状態 | 確定タイミング |
|---|---|---|
| Idempotency-Key の有効期間（24h で良いか） | 仮置き | Phase 1 実装時 |
| OpenAPI 差分検知ツールの採用（自前 vs `openapi-diff`） | 未決 | Phase 0 終盤 |
| Schemathesis 採用 | 検討 | Phase 1 で導入 |
| エラーコードのレジストリ管理（一覧 doc 必要か） | 検討 | Phase 1 で `errors.md` を起こす |
| ファイルアップロードの **resumable upload**（巨大 zip） | 不要 → 必要時に検討 | – |

---

## 9. 採用ルール（短く）

1. **REST + JSON + 共有 Pydantic スキーマ** が API 通信のすべて
2. リアルタイム表示は **Firestore リスナー**、API は副作用要求のみ
3. URL は `/api/v1/<resource>[/<id>][:verb]`、snake_case 統一、レスポンスは裸 JSON
4. エラーは `{code, message, details, request_id}` の 1 形式
5. 副作用 POST は `Idempotency-Key` を許容
6. **A2A は別レイヤ**（Managed Agent 側のサーバ実装 / Foundry が A2A クライアントとして呼ぶ）→ [`a2a-protocol.md`](a2a-protocol.md)

---

## 10. 更新ルール

- スキーマ変更は packages/shared の Pydantic を起点に
- OpenAPI の breaking change は **v2/ を立てて並走**
- 本書を変更するときは [`docs/app-architecture.md`](../app-architecture.md) §2 / §6 も同時更新

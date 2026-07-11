# Managed Repo Template ポリシー（叩き台 v0.1）

- 最終更新: 2026-06-22
- ステータス: Draft v0.1
- 親: [`docs/planning.md`](../planning.md) §10.2 / §11
- 関連: [`templates/`](../../templates/) / [`docs/policy/a2a-protocol.md`](a2a-protocol.md) / [`docs/policy/backend-architecture.md`](backend-architecture.md)
- 対象読者: 開発者本人 + Claude Code

---

## 0. このドキュメントの目的

Managed Repo（PoC Renovater がアップロードを受けて作成・改善する各 PoC のリポジトリ）に **何を注入するか** を確定する。

Managed PoC は次のいずれか（または混合）を想定:

1. **Web アプリ系**: Next.js / FastAPI / Streamlit など、ブラウザで触れる UI を持つ
2. **AI Agent 系**: バックエンドが LLM 駆動のエージェント。**A2A プロトコルでの呼び出し可能** が要件
3. **混合**: UI を持ちつつ、内部に Agent モジュールを抱える

→ **どの形でも受けられる単一テンプレート** を作る。「AI Agent モジュール」と「A2A サーバ」は **任意活性化** のオプションとして用意する。

---

## 1. 設計の柱

### 1.1 アーキテクチャの基線

Managed PoC 側のコード品質は **DDD レイヤード**を基線とする。改善 Issue が「層が混ざっている」「ドメインロジックが UI に滲んでいる」を狙えるようにするため。

```
managed-poc/
├─ src/
│  ├─ domain/                # 純粋。ビジネスルール・値オブジェクト
│  ├─ application/           # ユースケース。domain と infrastructure を組み合わせ
│  ├─ infrastructure/        # 外部依存（DB / HTTP / LLM / FS）
│  └─ interface/             # 入口（HTTP handler / CLI / A2A server）
├─ tests/
├─ a2a/                      # 任意：AgentCard と A2A server エントリ
│  └─ agent-card.json
├─ Dockerfile                # 任意（無くてもよい。buildpack で出る）
├─ Procfile                  # cloudrun --source 向け（任意）
├─ .env.example
├─ .github/
│  ├─ ISSUE_TEMPLATE/
│  ├─ pull_request_template.md
│  └─ workflows/ci.yml
├─ README.md                 # Profile / Charter ベース
├─ ARCHITECTURE.md           # 本テンプレが採用する DDD 層の説明
└─ SECURITY.md
```

### 1.2 任意モジュールの「フラグ」

テンプレート展開時に Profile / Charter を見て **どのモジュールを入れるか**を決める。Repo Agent（[`docs/planning.md`](../planning.md) §8）が判定:

| フラグ | 有効化条件 | 注入されるもの |
|---|---|---|
| `has_web_ui` | Profile.inputFormat に "browser" 等 | `src/interface/http/` + `apps/web/` 雛形 |
| `has_a2a_server` | Profile.useCases に "agent invocation" / "agent2agent" を含む / 明示指定 | `src/interface/a2a/` + `a2a/agent-card.json` |
| `has_llm_module` | Profile.dependencies に "openai" / "anthropic" / "vertex" / "gemini" 等 | `src/infrastructure/llm/` + `src/application/agents/` |
| `has_db` | Analysis で DB 利用検出 | `src/infrastructure/repository/` 雛形（最初は in-memory / SQLite） |

複数同時 ON 可。**全部 OFF はあり得る**（純粋ライブラリ等）。

---

## 2. テンプレートのディレクトリ展開（フル）

```
templates/
├─ base/                     # 全テンプレ共通
│  ├─ README.md.tmpl
│  ├─ .env.example.tmpl
│  ├─ .gitignore
│  ├─ .editorconfig
│  ├─ SECURITY.md
│  ├─ ARCHITECTURE.md.tmpl   # 採用された層の説明
│  ├─ pull_request_template.md
│  └─ .github/
│     ├─ ISSUE_TEMPLATE/
│     └─ workflows/ci.yml
├─ modules/
│  ├─ python-fastapi/        # has_web_ui=true & 言語 Python
│  │  ├─ pyproject.toml
│  │  ├─ src/
│  │  │  ├─ domain/__init__.py
│  │  │  ├─ application/__init__.py
│  │  │  ├─ infrastructure/__init__.py
│  │  │  └─ interface/http/main.py    # /healthz など
│  │  ├─ tests/test_healthz.py
│  │  └─ Procfile
│  ├─ nextjs/                # has_web_ui=true & TS
│  │  ├─ package.json
│  │  ├─ app/
│  │  │  ├─ layout.tsx
│  │  │  ├─ page.tsx
│  │  │  └─ healthz/route.ts
│  │  └─ ...
│  ├─ a2a-server-python/     # has_a2a_server=true & Python
│  │  ├─ src/interface/a2a/server.py
│  │  └─ a2a/agent-card.json.tmpl
│  ├─ a2a-server-typescript/ # has_a2a_server=true & TS
│  ├─ llm-vertex-python/     # has_llm_module=true & Python & Vertex
│  ├─ llm-anthropic-python/  # has_llm_module=true & Python & Anthropic
│  ├─ db-sqlite-python/      # has_db=true & SQLite
│  └─ ...
└─ catalog.json              # 「どのフラグでどのモジュールを入れるか」のマッピング
```

`catalog.json` の例:

```jsonc
{
  "modules": [
    {
      "id": "python-fastapi",
      "requires": ["has_web_ui", "lang=python"]
    },
    {
      "id": "nextjs",
      "requires": ["has_web_ui", "lang=typescript"]
    },
    {
      "id": "a2a-server-python",
      "requires": ["has_a2a_server", "lang=python"]
    },
    {
      "id": "llm-vertex-python",
      "requires": ["has_llm_module", "lang=python", "llm_provider=vertex"]
    }
  ]
}
```

Repo Agent が Analysis / Profile / Charter から「アクティブ flags」を計算し、catalog から module 集合を選び、base にマージ展開する。

---

## 3. DDD 層の規約（Managed PoC 側）

### 3.1 src/domain/

- **外部依存ゼロ**（標準ライブラリ + dataclass / Pydantic のみ）
- ドメインオブジェクト・値オブジェクト・ドメインサービス
- 例: `Order`, `OrderId`, `OrderStatus`, `pricing_rules.py`

### 3.2 src/application/

- ユースケース層。**1 ユースケース = 1 関数 or クラス**
- `domain` と `infrastructure` を組み合わせる
- トランザクション境界
- A2A タスクの 1 呼び出し = 1 application ユースケース、が原則

### 3.3 src/infrastructure/

- 外部依存の実装
- `repository/`（DB）、`llm/`（モデル呼び出し）、`http/`（外部 API）等
- domain interface を実装する形（依存の方向は infrastructure → domain）

### 3.4 src/interface/

- 入口
- `http/`（FastAPI / Next.js route）、`cli/`（CLI コマンド）、`a2a/`（A2A サーバ）、`worker/`（バックグラウンドジョブ）

### 3.5 禁則（テンプレ展開後 PoC 側でも守る）

- ❌ `interface/` から `infrastructure/` を直接 import（必ず `application/` 経由）
- ❌ `domain/` から `infrastructure/` を import
- ❌ `domain/` で I/O（HTTP / DB / file）
- ❌ 単一巨大 `main.py`（行数上限の lint を Repo Agent が ci.yml に入れる）

---

## 4. ci.yml（Managed Repo 用）

最低限:

```yaml
name: ci
on: [push, pull_request]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: # 言語別 lint
  typecheck:
    # Python: mypy / pyright, TS: tsc --noEmit
  test:
    # pytest / vitest
  build:
    # buildpack dry-run (or docker build) — Cloud Run --source の前哨
  secret-scan:
    # gitleaks
```

これは **Repo Agent が雛形から注入**。Coding Agent は Issue 単位の変更でこの workflow を壊さないことを保証（壊れたら Self-Improvement Agent が修正 PR を起こす）。

---

## 5. ARCHITECTURE.md.tmpl（採用した層の説明）

テンプレ展開時に **何が入ったか** をリポジトリ自身に書き残す。後で AI Agent / 人間がリポを見たとき、何が前提かが即わかる。

```markdown
# Architecture

This repository was initialized from PoC Renovater template `{{template_version}}`.

## Stack
- Language: {{lang}}
- Framework: {{framework}}
- LLM provider: {{llm_provider_or_none}}

## Active modules
{{#modules}}
- `{{id}}` — {{description}}
{{/modules}}

## Layering (DDD)
- `src/domain/` — pure business rules
- `src/application/` — use cases
- `src/infrastructure/` — external integrations
- `src/interface/` — entry points (HTTP / CLI / A2A)

## A2A
{{#has_a2a_server}}
This service exposes an A2A endpoint. AgentCard at `/.well-known/agent.json`.
See `a2a/` for the static AgentCard and `src/interface/a2a/` for the server.
{{/has_a2a_server}}

## Operating notes
- Charter: see CHARTER.md
- Improvement plan: managed by PoC Renovater (issues are auto-created)
```

---

## 6. A2A サーバの注入（要点）

詳細は [`a2a-protocol.md`](a2a-protocol.md)。テンプレ側で用意するのは:

- `a2a/agent-card.json.tmpl` — Profile / Charter から AgentCard を生成
- `src/interface/a2a/server.py` (or `.ts`) — JSON-RPC over HTTP の最小実装（`tasks/send` 等）
- `src/interface/a2a/handler.py` — application ユースケースに転送する薄いハンドラ
- ci.yml に **AgentCard 自己検証**（A2A schema validator）を追加

A2A エンドポイントは **既存の web/api サーバと同居**。別ポート不要。

---

## 7. LLM モジュールの注入（要点）

`has_llm_module=true` 時に注入される物:

```
src/
├─ infrastructure/llm/
│  ├─ client.py         # provider 別の実装（Vertex / Anthropic 等）
│  └─ types.py
└─ application/agents/
   ├─ base.py           # 抽象 Agent クラス（input -> output JSON）
   └─ <domain_agent>.py # ユースケース固有
```

**規約**:
- LLM 呼び出しは `infrastructure/llm/` に閉じ込める（テスト時にモック差し替え可能に）
- プロンプトは Python の f-string / template ライブラリで管理（巨大文字列を application に置かない → `prompts/` ディレクトリ）
- 出力スキーマは Pydantic、エージェント側で validate

---

## 8. 「混合型」サンプル: Web UI + 内部 Agent

例: 「ユーザーが質問を投稿 → 内部 LLM Agent が処理 → 結果表示 + 別 Agent への A2A 呼び出しもできる」

```
src/
├─ domain/
│  ├─ inquiry.py
│  └─ answer.py
├─ application/
│  ├─ submit_inquiry.py        # web UI から
│  ├─ answer_inquiry.py        # A2A から呼ばれる用
│  └─ agents/answerer.py       # LLM
├─ infrastructure/
│  ├─ llm/client.py
│  └─ repository/inquiry_repo.py
└─ interface/
   ├─ http/api.py              # /inquiries POST/GET
   └─ a2a/server.py            # tasks/send → answer_inquiry を呼ぶ
```

この場合のフラグ: `has_web_ui=true`, `has_a2a_server=true`, `has_llm_module=true`, `has_db=true`。

---

## 9. テンプレ自身の品質ガード

`templates/` への変更は **テンプレ自体の CI** で守る:

- 各 module を「全フラグ ON で展開した repo」と「最小フラグで展開した repo」両方で `pnpm install` / `uv sync` が通ること
- 注入後 `pytest` / `vitest` の最小スイートが green
- README / ARCHITECTURE が template syntax 残りなくレンダリングされる

`templates/tests/` 配下に展開シミュレータと検証スクリプトを置く。

---

## 10. ⚠ 未確定項目

| 項目 | 状態 | 確定タイミング |
|---|---|---|
| catalog.json のフラグ仕様（network of conditions） | 仮置き、シンプル形式で開始 | Phase 3 着手時 |
| テンプレ展開エンジン（Mustache / Jinja / cookiecutter） | 未決 | Phase 3 |
| TypeScript / Go / Rust テンプレの追加 | MVP は Python / TS のみ | Phase 1-2 確定後 |
| LLM provider 切替（Vertex / Anthropic / OpenAI）の抽象化レベル | LLM module 内で吸収 | Phase 3 |
| Managed PoC 側の packages/shared 連携（PoC Renovater の型を借りるか） | 借りない方針（独立性のため） | Phase 3 |

---

## 11. 採用ルール（短く）

1. テンプレは **単一**、モジュールは **フラグで任意活性化**
2. Managed PoC は **DDD 4 層**（domain / application / infrastructure / interface）
3. `has_a2a_server=true` なら **AgentCard 注入 + tasks エンドポイント** を必ず立てる
4. `ARCHITECTURE.md` に **何のモジュールが入ったか** を必ず残す
5. テンプレ自体の変更には **展開シミュレータでの ci 検証** が必須
6. **既存ファイルの上書きは慎重に**（Coding Agent が変更を加えるため、テンプレ側の "初期値" と "現状" の差を尊重）

---

## 12. 更新ルール

- 新しいモジュールを追加するときは **catalog.json + 展開ルール + テンプレ自身の test** を 1 PR にまとめる
- DDD 層の規約変更は本書 + ARCHITECTURE.md.tmpl + lint ルールを同時に
- 既存テンプレを破壊的に変更するとき、**過去に作成済の Managed Repo は自動更新しない**（手動 migration ガイドを書く）

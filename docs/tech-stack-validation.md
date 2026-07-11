# 技術スタック検証フェーズ — 設計ドキュメント（叩き台 v0.1）

- 最終更新: 2026-06-22
- ステータス: Draft v0.1
- 親ドキュメント: [`docs/planning.md`](planning.md) §12（本フェーズは Phase 0 と Phase 1 の間に挿入）
- 関連: [`docs/policy/`](policy/)（backend-architecture / api-schema / frontend / a2a-protocol / sandbox / infra / templates）— 各 spike の結果が本書経由で policy を更新する流れ
- 対象読者: 開発者本人 + Claude Code
- 位置づけ: **Phase S（Spike Phase）**。本フェーズの DoD を満たすまで Phase 1 には進まない。

---

## 0. このドキュメントの目的

PoC Renovater が前提とする技術スタックには、**preview / 急速進化中 / リージョン未確定**な要素が含まれている。具体的には:

- Vertex AI Gemini 3（preview、global endpoint 縛り）
- Google ADK（Agent Development Kit、活発に変化中）
- Vertex AI Agent Engine Runtime（地域提供状況が変動）
- Cloud Run `--source` デプロイ（buildpack の挙動が言語スタックに依存）

これらが「実装着手後に使えないと判明」してから設計を巻き戻すコストは大きい。本フェーズは **小さなスパイクで早期に確証/反証** を取り、必要なら `docs/planning.md` §4 / §8 を更新してから本実装（Phase 1+）に入るための **ガードレール**である。

---

## 1. 検証する / しない の線引き

### 検証対象（リスク高、本フェーズで spike を回す）

| spike id | 検証対象 | リスク要因 |
|---|---|---|
| `spike-1-vertex-gemini` | Vertex AI Gemini 3 (Pro/Flash) を SDK 経由で呼び出せるか | preview / global endpoint のみ / モデル文字列が変わる可能性 |
| `spike-2-adk-gemini` | ADK の `LlmAgent` で Gemini 3 を動かせるか | ADK が活発に変化中、Gemini 3 とのバインディングが不明 |
| `spike-3-adk-structured-output` | ADK の構造化出力（`output_schema`）が安定して効くか | スキーマ強制が想定通り効かないと Coding/Charter/Review 設計に影響 |
| `spike-4-run-source-deploy` | Next.js 15 + FastAPI(uv) を `gcloud run deploy --source` で出せるか | buildpack の対応状況次第で Dockerfile 戦略への切替が必要 |
| `spike-5-firestore-state` | Firestore Native を状態機械として使えるか | トランザクション・イベント順序保証の実用性 |
| `spike-6-coding-engine` | `CodingEngine` 抽象化が両エンジンで成立するか | `adk_gemini` / `claude_code` 共通の `CodeChange` 契約が破綻しないか |
| `spike-7-agent-engine` | Agent Engine Runtime が asia-northeast1 で提供されているか | Phase 7（任意）の前提。MVP の blocker ではない |
| `spike-8-a2a-sdk` | `a2a-sdk` (Python) / `@a2a-js/sdk` (TS) の wire 仕様確認 | `message/send` 以外のメソッド wire string / TaskState JSON 値 / Part 型の整合確認（[`docs/policy/a2a-protocol.md`](policy/a2a-protocol.md) §7 を解消） |

### 非検証（成熟・既動作確認済み、本フェーズで触らない）

| 項目 | 理由 |
|---|---|
| Next.js 15 App Router | エコシステム成熟。本筋の不確実性ではない |
| FastAPI + uv | 安定 |
| Firestore SDK の基本 CRUD | 安定。**状態機械としての使い方**だけ spike-5 で別途 |
| Terraform google provider | 既に動作確認済（`infra/` で apply 完了） |
| GitHub App / installation token | 既に動作確認済（bootstrap 時に smoke test 通過） |
| Cloud Build / Artifact Registry | 標準。`spike-4` で間接的に検証される |
| Secret Manager | 標準 |
| pnpm / uv ツール本体 | 標準 |

---

## 2. 各 spike の標準構成

各 spike は `spikes/<spike-id>/` 配下に独立配置し、**再現実行可能** にする:

```
spikes/<spike-id>/
├── README.md      # 目的 / 仮説 / 検証手順 / 合格条件
├── run.sh         # or run.py — 全工程を 1 コマンドで再現
├── result.md      # 実行ログのサマリ（時間 / 出力 / エラー / 数値）
└── decision.md    # 採用 / 見送り / 設計変更点（人間が書く）
```

進行は **`run.sh` → `result.md` → `decision.md`** の 3 段階。

### スパイクの大きさの目安

- コード量: 1 spike あたり **100〜300 行**
- 実行時間: **5 分以内**（spike-4 のみビルドが入るので例外）
- 依存追加: 本番依存に影響しない（`spikes/<id>/` 単位で完結）

---

## 3. 個別 spike の合格条件

### spike-1: Vertex AI Gemini 3 ping

**仮説**: `GEMINI_MODEL_PRO` / `GEMINI_MODEL_FLASH` の文字列で global endpoint 経由で Gemini 3 を呼べる。

**手順**:
1. `google-cloud-aiplatform`（または `google-genai`）の最新 SDK を `uv` で導入
2. `VERTEX_LOCATION=global` で Pro / Flash の両方に「短い日本語プロンプト」を投げる
3. レスポンス本文 / latency / token usage を `result.md` に記録

**合格条件**:
- Pro / Flash 両方が 200 を返す
- レスポンスが意味のある自然文（言語混在 OK）
- p50 latency が 5 秒以内（参考値、要件ではない）
- 公式に推奨されているモデル文字列が `.env` の `GEMINI_MODEL_PRO/FLASH` と一致

**NoGo 時の選択肢**:
- 公開モデル文字列の調整（`gemini-3-pro-xxx` のようなリビジョン付き名）
- Gemini 2.5 系へ一時的にフォールバック（`docs/planning.md` のモデル変数を書き換え）
- アジア地域 endpoint が GA したら切替

---

### spike-2: ADK + Gemini 3 連携

**仮説**: ADK の `LlmAgent` で Gemini 3 を model として指定し、ローカルプロセスから推論できる。

**手順**:
1. `google-adk` の最新 SDK を導入
2. 1 ターンだけで応答する最小 `LlmAgent` を定義
3. `Runner` 経由で呼んで応答を得る
4. env を変えて Pro ↔ Flash を切替できるか確認

**合格条件**:
- エージェントが応答を返す
- env を変えるだけで Pro / Flash 切替が効く
- ADK のエラー設計が想定通り（タイムアウト・パースエラーが区別可能）

**NoGo 時**:
- ADK が Gemini 3 未対応 → **LiteLLM 経由**で接続
- それも不可 → ADK を諦め、Vertex AI SDK 直接 + 自作 orchestrator

---

### spike-3: ADK 構造化出力

**仮説**: ADK の `output_schema`（Pydantic）で JSON 出力が強制される。

**手順**:
1. spike-2 のエージェントに 3〜5 フィールドの Pydantic `BaseModel` を `output_schema` として渡す
2. 同じプロンプトを 20 回流す
3. Pydantic validation 通過率を集計
4. スキーマ違反時に取れるエラー型を確認

**合格条件**:
- **20/20** でスキーマ通過
- スキーマ違反時のエラーが `ValidationError` として例外で取れる（リトライ可能な形）

**NoGo 時**:
- `output_schema` が機能しない → プロンプト内で JSON 強制 + `json.loads` + 失敗時リトライを自作
- これは Coding / Charter / Review の中核なので回避策は必須

---

### spike-4: Cloud Run `--source` デプロイ

**仮説**: Next.js 15 と FastAPI(uv) を `gcloud run deploy --source .` で buildpack 経由デプロイできる。

**手順**:
1. `apps/web` に最小の `app/page.tsx` + `app/healthz/route.ts` を置く
2. `apps/api` に最小の `app/main.py` (`/healthz` 返すだけ) + `pyproject.toml` を置く
3. それぞれ `gcloud run deploy <name> --source . --region=asia-northeast1 --project=poc-recycle` で出す
4. デプロイされた URL に `/healthz` で 200 が返ることを確認

**合格条件**:
- 両方の URL が `/healthz` で 200 を返す
- ビルドログにエラー / 重大な警告なし
- ビルド時間が許容範囲（参考値: 5 分以内）

**NoGo 時**:
- buildpack が動かなければ `templates/` に Dockerfile 雛形を用意して切替
- これは **MVP のデモ DoD を直撃する**ので最重要

---

### spike-5: Firestore Native を状態機械として使う

**仮説**: `agents/{id}.status` のフィールド遷移をトランザクションで安全に進められ、`agents/{id}/events` への append が順序保証つきで効く。

**手順**:
1. ダミー `agents/test` に `status: UPLOADED` を作る
2. 2 つのプロセスから同時にトランザクションで `ANALYZING` への遷移を試みる
3. 片方だけが成功し、もう片方は `aborted`（→ 再試行）になることを確認
4. リスナー（`onSnapshot` 相当）でリアルタイム反映を確認

**合格条件**:
- 競合検知がトランザクション失敗で表面化する
- イベントが順序保証つきで `events` サブコレクションに積まれる
- リスナーで client にリアルタイム反映が見える

**NoGo 時**:
- 順序保証で力不足なら Pub/Sub を間に挟む
- 状態機械をアプリ層で持ち、Firestore は事実保存だけにする

---

### spike-6: Coding Engine 抽象化

**仮説**: `CodingEngine` Protocol に対し `AdkGeminiEngine` と `ClaudeCodeEngine` を独立に実装でき、下流（Sandbox / Review）は engine を意識せず動く。

**手順**:
1. `packages/agents/coding/engine.py` に Protocol と 2 つの実装を書く
   - `AdkGeminiEngine`: spike-2 のエージェントを呼ぶ
   - `ClaudeCodeEngine`: `claude -p --output-format json` を `subprocess` で呼ぶ（実呼び出しは mock でも可）
2. 「文字列の中の `foo` を `bar` に変える」程度の trivial issue を渡す
3. 両エンジンから返ってきた `CodeChange` を Sandbox 側で適用 → diff 行数チェック → PR 本文整形、までが共通コードで通ることを確認
4. `CODING_ENGINE` の env 切替だけで挙動が変わることを確認

**合格条件**:
- 2 エンジンの差が `engine.py` 内に閉じ込められている
- `CodeChange`（branch / diff / PR body）契約に過不足がない
- `CODING_ENGINE` の env 切替だけで Sandbox / Review 側のコードが変わらない

**NoGo 時**:
- どちらかが `CodeChange` 契約で表現できない → 契約を拡張するか、片方のエンジンを当面諦める

---

### spike-8: A2A SDK wire 仕様確認

**仮説**: `a2a-sdk` (Python) を import し、最小の AgentCard / Server / Client を組めば、wire-format の正確な値（method 名 / TaskState JSON / Part shape）が `a2a.types` から確認できる。

**手順**:
1. `uv` で `a2a-sdk` を導入（v1.x）
2. `a2a.types.MethodName`（または相当）の enum を列挙して `result.md` に貼る
3. `a2a.types.TaskState` を JSON serialize したときの値を実測
4. `a2a.types.Part` の構造（OneOf / 分離クラス）を確認
5. AgentCard を minimal で組み立てて `.well-known/agent-card.json` 形式で dump、フィールド一覧を実測
6. 最小サーバ（uvicorn）を立てて Python クライアントから `message/send` を 1 回叩き、リクエスト/レスポンスの raw JSON を `result.md` に記録

**合格条件**:
- 以下が wire-string レベルで確定:
  - `message/stream`（streaming）の正確な name
  - `tasks/cancel` / `tasks/resubscribe` の正確な name
  - `tasks/pushNotificationConfig/{set,get}` の正確な name
  - `agent/getAuthenticatedExtendedCard` の正確な name
- TaskState の JSON 値（lowercase か CamelCase か）が確定
- Part の wire 形式（OneOf シリアライズ）が確定
- AgentCard の必須 / 任意フィールドが SDK 型から正確に列挙

**NoGo 時**:
- SDK バージョンと spec のずれがあれば、`docs/policy/a2a-protocol.md` の §2.3 / §2.6 を SDK 実態に合わせる（spec ではなく SDK が動作の真）
- Python SDK で取れない情報は `@a2a-js/sdk` も併用

---

### spike-7: Agent Engine Runtime（asia-northeast1）

**仮説**: Vertex AI Agent Engine Runtime が asia-northeast1 で利用可能で、ADK エージェントをデプロイできる。

**手順**:
1. 公式 locations ドキュメントで対応状況を確認
2. spike-2 のエージェントを Agent Engine Runtime にデプロイ
3. リモート呼び出しで応答を確認

**合格条件**:
- asia-northeast1 でデプロイが成功
- リモート呼び出しレイテンシがローカル + 1〜2 秒以内

**NoGo 時 / 期日**:
- 提供されていない場合は **Phase 7 を一旦保留**
- このスパイクは MVP リリースの blocker ではない（§4 で確定済）

---

## 4. フェーズの進め方

1. 各 spike を独立にスパイク実装（main 直 commit OK 期間）
2. `spikes/<id>/README.md` に仮説・手順・合格条件
3. `run.sh` を叩いて `result.md` を生成
4. `decision.md` で **採用 / 見送り / 設計変更** を明記
5. 全 spike の `decision.md` が「採用」または「見送り（フォールバック設計済）」になったらフェーズ完了

### 実行順序の推奨

```
spike-1 (Vertex ping)
   ↓
spike-2 (ADK + Gemini) ―→ spike-3 (構造化出力) ―→ spike-6 (Coding Engine 抽象)
   ↓
spike-4 (Cloud Run --source)
   ↓
spike-5 (Firestore state)
   ↓
spike-8 (A2A SDK)        ※ Phase 3 着手前に必要、Phase S 内で先取り
   ↓
spike-7 (Agent Engine)   ※ 任意・並行可
```

spike-1 〜 4 が **MVP 必達**。spike-5 は Phase 1 着手前に必要。spike-6 は Phase 4 前に必要だが本フェーズで先取り。spike-8 は Phase 3 で A2A サーバ雛形を作る前に必要。spike-7 は MVP の blocker ではない。

---

## 5. フェーズの DoD

- [ ] spike-1〜6, spike-8 がすべて合格 or 明示的な fallback 採用済み
- [ ] spike-7 は判定済み（合格 / 保留 / Phase 7 設計見直し のいずれか）
- [ ] 各 `decision.md` の総括として、本ドキュメント末尾「§8 決定ログ」に追記
- [ ] `docs/planning.md` §4（技術スタック）/ §8（エージェント）のうち、検証結果と矛盾する記述を更新（必要があれば）
- [ ] `docs/policy/a2a-protocol.md` §7「残りの要確認項目」が spike-8 結果で解消
- [ ] `.env.example` のモデル文字列・モデル指定方針が検証結果と一致

---

## 6. NoGo シナリオと退避策（早見表）

| シナリオ | 影響 | 退避策 |
|---|---|---|
| Gemini 3 が global endpoint でも安定して使えない | Pro/Flash の使い分けが崩れる | Gemini 2.5 系で MVP、Gemini 3 GA 後に切替 |
| ADK が Gemini 3 未対応 | エージェント設計全面見直し | LiteLLM 経由 / Vertex AI SDK 直 + 自作 orchestrator |
| ADK の `output_schema` 信頼性低い | JSON 強制パターンを自作する必要 | プロンプト + `json.loads` + リトライで吸収 |
| Cloud Run buildpack が要件スタックで動かない | デモ DoD 直撃 | `templates/` に Dockerfile 雛形 |
| Firestore がイベント順序保証で力不足 | 状態機械の信頼性低下 | Pub/Sub + Firestore の組み合わせ |
| Coding Engine 抽象化が破綻 | 2 エンジン併用方針見直し | MVP は `adk_gemini` 一択にして、`claude_code` を後送り |
| Agent Engine Runtime 未提供 | Phase 7 保留 | MVP は Cloud Run 同居で継続（§4 既定済） |

---

## 7. 成果物（本フェーズ完了時に手元にあるもの）

- `spikes/spike-1〜7/` 配下の検証コードと結果レポート
- 本ドキュメント §8「決定ログ」セクション
- 必要なら `docs/planning.md` の更新 PR（§4 / §8）
- 必要なら `templates/` への Dockerfile 雛形（spike-4 NoGo 時）
- 必要なら `docs/setup-ja.md` への「spike を動かすには」追記

---

## 8. 決定ログ（spike 完了後に追記する）

| 日付 | spike id | 判定 | 採用内容 / 設計変更 | 参照 |
|---|---|---|---|---|
| 2026-06-22 | spike-1 | 採用（条件付） | `GEMINI_MODEL_PRO=gemini-3.1-pro-preview`（Pro は preview のみ）/ `GEMINI_MODEL_FLASH=gemini-3.5-flash`（GA）。p50 latency 約 4s / 2s。`.env` / `.env.example` 更新済 | [spike-1/decision.md](../spikes/spike-1-vertex-gemini/decision.md) |
| 2026-06-22 | spike-2 | 採用 | ADK `LlmAgent + Runner + InMemorySessionService` で Vertex 経由 Gemini 3 を呼び出し 4/4 OK（p50 4.51s）。env で Pro/Flash 切替成立。`.env.example` に `GOOGLE_GENAI_USE_VERTEXAI` / `GOOGLE_CLOUD_LOCATION` 追記、session 永続化方針は Phase 1 で確定 | [spike-2/decision.md](../spikes/spike-2-adk-gemini/decision.md) |
| 2026-06-22 | spike-3 | 採用 | ADK `LlmAgent(output_schema=PydanticModel)` で 25/25 (Pro 20/20 + Flash 5/5) スキーマ通過、`ValidationError` 発生ゼロ。Coding / Charter / Review の構造化出力に直接採用。`event.content.parts[0].text` から `model_validate_json()` で取得するパターンを確定。リトライラッパは guardrails で別途実装（spec §15） | [spike-3/decision.md](../spikes/spike-3-adk-structured-output/decision.md) |
| 2026-06-23 | spike-4 | 採用 | `gcloud run deploy --source` で Next.js 15 (pnpm) + FastAPI (uv) の両方を asia-northeast1 に投入、`/healthcheck` で 200 を確認。**重要発見**: Cloud Run は `/healthz` を GFE で予約遮断するため `/healthcheck` に統一。Web ビルド 271s / API 86s（5 分 SLO ぎりぎりは Web 側で要警戒）。SA 指定 / 認証ゲートは Phase 1+ で対応 | [spike-4/decision.md](../spikes/spike-4-run-source-deploy/decision.md) |
| 2026-06-23 | spike-5 | 採用 | Firestore Native `(default)` で 3 sub-claim 全合格: トランザクション競合は CAS-mismatch (`ValueError`) として 1 winner / 1 loser で表面化、events 100件は seq / server_timestamp 両方で順序保証、listener 反映 p50 48ms / max 57ms。SDK は `@firestore.transactional` + `client.transaction()`、`on_snapshot(cb)` で realtime。Phase 1+ で `seq` は `agents/{id}.next_event_seq` の atomic 更新パターン必須 | [spike-5/decision.md](../spikes/spike-5-firestore-state/decision.md) |
| 2026-06-23 | spike-6 | 採用 | `CodingEngine` Protocol + `make_engine()` factory で `AdkGeminiEngine` (Vertex Gemini 3 Pro, 16s) と `ClaudeCodeEngine` (`claude -p --output-format json`, 5.6s) が `CODING_ENGINE` env 切替のみで入れ替え可能。同一 trivial issue で両者バイト一致 diff を返し、engine 非依存の `_downstream.apply()` (diff 行数 / files_touched 整合 / PR body 正規化) が 2/2 accepted。`CodeChange` 契約 (branch / diff / pr_title / pr_body / files_touched) に過不足なし。実装は `packages/agents/coding/` に Phase 4 起点として固定 | [spike-6/decision.md](../spikes/spike-6-coding-engine/decision.md) |
| 2026-06-23 | spike-7 | 採用（条件付） | Agent Engine Runtime（`reasoningEngines` v1 GA API）は asia-northeast1 で **利用可能**を実証（REST プローブで HTTP 200、リソース作成 → 即時削除、ネット残存 0）。`gcloud ai reasoning-engines` はサブコマンドとして存在しない（CLI 521.0.0）— REST API 直接が正しいプローブ手段。Phase 7 はリージョンポリシー違反なく実施できる。残課題: ADK + Agent Engine 統合・Gemini エンドポイント確認・SA IAM は Phase 7 着手時に別途確認 | [spike-7/decision.md](../spikes/spike-7-agent-engine/decision.md) |
| 2026-06-23 | spike-8 | 採用 | `a2a-sdk==1.1.0` で wire-string レベル確定: 全 8 JSON-RPC method（`message/send` `message/stream` `tasks/{get,cancel,resubscribe}` `tasks/pushNotificationConfig/{set,get,list,delete}` `agent/getAuthenticatedExtendedCard`）、`TaskState` は **lowercase + kebab**（`input-required` / `auth-required`）、`Part` は **`RootModel[TextPart\|FilePart\|DataPart]` + `kind` discriminator**、`AgentCard` は Pydantic 18 フィールド（必須 8 / 任意 10、`authentication` は廃止 → `security` + `securitySchemes`）。ローカル uvicorn で `message/send` 1 往復 200 確認。SDK 構成: wire 形式は `a2a.compat.v0_3.types`、サーバは `a2a.types`（protobuf）+ FastAPI mount。`docs/policy/a2a-protocol.md` §2.2/§2.3/§2.5/§2.6/§3.2/§3.3/§7 更新は別 PR で提案 | [spike-8/decision.md](../spikes/spike-8-a2a-sdk/decision.md) |

（spike が終わるたびに 1 行ずつ追記する）

---

## 9. 本ドキュメントを更新するルール

- 各 spike の `decision.md` を最初に書き、本ドキュメント §8 に 1 行サマリを追記する順序
- 検証結果が `docs/planning.md` §4 / §8 を変更させる場合は、planning.md 側を **別 PR で更新**（理由付きで）
- 本ドキュメント自体は spike 完了後にもう一度全体を読み直し、過剰な記述は剪定する

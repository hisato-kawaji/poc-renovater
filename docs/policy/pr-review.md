# PR レビュー ポリシー（v0.1）

- 最終更新: 2026-06-22
- ステータス: Draft v0.1
- 関連:
  - レビュー Agent: [`.claude/agents/pr-reviewer.md`](../../.claude/agents/pr-reviewer.md)
  - 手動起動コマンド: [`.claude/commands/pr-review.md`](../../.claude/commands/pr-review.md)
  - 初回レビュー loop: [`.claude/commands/loop-pr-review.md`](../../.claude/commands/loop-pr-review.md)
  - 議論進行 loop: [`.claude/commands/loop-pr-discussion.md`](../../.claude/commands/loop-pr-discussion.md)
- 対象読者: 開発者本人 + Claude Code

---

## 0. このドキュメントの目的

PR の **自動レビューと人間レビューの併用ガードレール**を確定する。レビュー観点をここに集約し、追加・改訂を行いやすくする。`.claude/agents/pr-reviewer.md` は本書 §1 を **source of truth として参照**する（agent 側でロジックを増殖させない）。

---

## 1. レビュー観点（v0.1）

すべての PR に対して、以下 6 観点を **PASS / WARN / FAIL** の 3 値で評価する。

| # | 観点 | 概要 | 主要チェックポイント |
|---|---|---|---|
| 1 | **動作する** | 変更が実際に意図通り動くか | run.sh / test / smoke 通過、CI green、preview URL 200、エラー時の挙動が定義通り |
| 2 | **ユースケース網羅** | 関連 Issue / Charter / planning.md のユースケースを満たすか | Issue 受入条件の引き当て、demo シナリオ（[`docs/planning.md`](../planning.md) §11）への影響、未使用パスが残っていないか |
| 3 | **設計・コーディング規約** | `docs/policy/*` / `docs/app-architecture.md` / `CLAUDE.md` §7 に準拠か | Hexagonal の層越境（`domain/` から外を import しない 等）、port / adapter の方向、エラーエンベロープ形、snake_case、`any`/`unknown` 禁止、`console.log` / `print` 残り |
| 4 | **CI** | GitHub Actions のチェックが緑か | lint / typecheck / unit / integration / build / secret scan。失敗 job 名を明示 |
| 5 | **見落とし** | 見落とされがちな観点 | エッジケース・空配列・null・ネットワーク断、レースコンディション、既存機能破壊、テスト未更新、ドキュメント遅延、依存追加の理由欠落 |
| 6 | **セキュリティ** | セキュリティリスク | secret 漏洩（コミット / log / レスポンス）、認可バイパス、入力検証、SSRF / XSS / SQLi、依存脆弱性、sandbox 突破、PII の取扱い |

### 1.1 各観点の評価基準

- **PASS**: 観点に対し問題なし、または PR body で明示的に説明されている
- **WARN**: 改善余地ありだが merge 阻止までは要さない（コメント残し）
- **FAIL**: 設計違反・テスト失敗・セキュリティ問題など、merge 前に修正必須

---

## 2. 総合判定

集計の判定ルール:

- **APPROVE**: 6 観点すべて PASS、または PR body で明示的に waiver された WARN のみ。§2.1 で issue に切り出して根拠を **「WARN — tracked in #N」** とした行は、集計上 **PASS 相当**として扱いブロックしない（body waiver とは別経路だが、いずれも「この PR では解決済み」を意味する）
- **REQUEST_CHANGES**: いずれかが FAIL、または重大な WARN が複数（reviewer 裁量）
- **NEEDS_DISCUSSION**: アーキ判断・トレードオフ判断・スコープ判断が必要で、レビュー観点では結論を出せない

自動レビューは **コメントのみ**（GitHub の Approve / Request changes は **人間の専有**）。

### 2.1 追加対応は issue に寄せる（PR をスコープ外で滞留させない）

レビューで見つかった指摘が **本 PR のスコープ外** — 次のいずれか — の場合は、PR をブロックする WARN/FAIL にして滞留させず、**フォローアップ issue に切り出す**:

- 修正が diff budget（`MAX_PR_DIFF_LINES`）を超える
- 設計判断・トレードオフ判断が必要（この場合タイトルを `[Follow-up #<PR>][Design]` とし、`/loop-issue-pickup` の `[Design]` スキップ＝人間判断待ちに乗せる）
- 本 PR が触れていない領域に及ぶ
- 非ブロッキングな hardening / nice-to-have（あれば良い、無くても正しさは損なわれない）

手順:

1. `gh issue create --assignee YOUR_GITHUB_ACCOUNT` で起票。タイトルは `[Follow-up #<PR>] <one-line>`、本文に **元 PR へのリンク・`path:line` 根拠・スコープ・受け入れ条件** を含める。次フェーズをブロックするなら `--label priority:high`、それ以外は default（必要なら `enhancement`）。
2. **重複防止（完全タイトル一致で判定）**: 起票前に `gh issue list --repo YOUR_ORG/YOUR_REPO --search "Follow-up #<PR>" --state open` で候補を引き、**`[Follow-up #<PR>] <one-line>` の完全タイトル一致**で既存判定する。prefix（`[Follow-up #<PR>]`）だけで判定すると、同一 PR の **別 finding** を既存 issue が誤って抑制し、また **同一 finding** の再レビューも取りこぼす。GitHub 検索は `[` / `#` をトークン分割してゆるく当たるため、検索はゆるく引いて **最終判定は取得結果のタイトル文字列の完全一致**で行う。同一 finding は二重起票しない。
3. verdict 側では、その行を **PASS（または「WARN だが issue #N で追跡」）** とし、根拠 / 推奨アクションに **起票した issue 番号を明記**する。これにより本 PR の判定は本来のスコープだけで決まり、追加対応は roadmap（優先度順 pickup）に乗る。

切り出してよいのは「実在するが今ここで直す必要のない」指摘のみ。本 PR の正しさ・受け入れ条件に関わる指摘は issue に逃がさず、その PR で直す。

---

## 3. 自動実行 — Claude Code セッション内の 2 つの loop

自動レビューは **アクティブな Claude Code セッション内**で動かす（GitHub Actions ではない）。理由:

- API キーを Repo Secret に置く必要がない
- レビュー判断が Claude Code 全体の文脈（CLAUDE.md / policy docs / メモリ）を反映できる
- セッションの料金体系で動く（per-PR の従量課金ではない）

役割を分けた **2 つの loop** を併走させる:

| Loop | Cadence | 役割 |
|---|---|---|
| `loop-pr-review` | **12 時間（半日）** | 未レビュー head に対する **初回レビュー** |
| `loop-pr-discussion` | **5 分** | 既レビュー PR の **議論進行 + 最終判定（approve まで）** |

両者は SHA marker (`<!-- pr-reviewer: <sha> -->`) と timestamp で **責務が重ならない**。

### 3.1 起動

セッションを始めたら 2 つを 1 度ずつ:

```text
/loop 12h /loop-pr-review
/loop 5m  /loop-pr-discussion
```

- 初回レビューは半日 1 回で十分（非緊急）
- 議論は 5 分間隔で polling して、すばやく往復を成立させる
- 緊急で初回をすぐ走らせたいときは `/pr-review <PR#>`

### 3.2 cadence の選び方

#### loop-pr-review（初回レビュー）

| 間隔 | 用途 |
|---|---|
| `/loop 12h`（推奨） | 通常運用。半日 1 回のスイープ。アイドルコスト最小 |
| `/loop 6h` | 1 日 4 回。やや snappier |
| `/loop 1h` | 集中開発日。1 時間以内に feedback が欲しい |
| 10m 以下 | rapid iteration 中。代わりに `/pr-review <PR#>` を使うほうが効率的 |

#### loop-pr-discussion（議論進行）

| 間隔 | 用途 |
|---|---|
| `/loop 5m`（推奨） | 通常運用。push / 返信から 5 分以内に進行 |
| `/loop 2m` | 集中ペアプロ的に詰めたいとき |
| `/loop 15m` | 軽めの並行作業。やや lag |

idle 時はほぼ gh API call のみで LLM コスト 0。

### 3.3 skip 条件

- PR が `draft` 状態
- PR に `skip-claude-review` ラベル
- 同じ head SHA に対してレビュー済（marker で検出、initial review loop が skip）
- 議論 thread が **idle**（双方とも last word を出した後動きなし、discussion loop が skip）
- `.claude/scratch/STOP-PR-LOOP` ファイルが存在

### 3.4 discussion loop の動作詳細

各 tick で開いた非 draft の PR について:

1. 最新の `pr-reviewer` verdict コメント（SHA marker 一致）を見つける
2. verdict の WARN / FAIL 行を起点に thread を組み立て
3. **author 側 thread (我々が PR 作者の場合の対応)**:
   - thread が actionable で fix が **< 50 行・contained** → コミット + push + `Applied in <sha-short>` 返信
   - **50–200 行** → plan を提案、確認待ち
   - **> 200 行 / アーキ判断** → 自動修正せず議論コメントを残す
4. **reviewer 側 thread (我々の指摘に反論があった場合)**:
   - 反論が出たら `pr-reviewer` subagent (re-evaluation mode) を呼んで policy 再チェック
   - まだ valid → 引用して counter
   - invalid → concede（1–2 文で明示）
5. **全 thread 解決 + CI green** → `gh pr review --approve --body "..."` で approve（merge はしない）

### 3.5 安全制限（discussion loop）

- **per PR per tick で最大 1 commit**（runaway 防止）
- **per PR で通算最大 5 self-fix commit**（人間 ack なしの暴走防止）
- **`git push --force` 禁止**
- **`gh pr merge` 禁止** — approve しても merge は人間
- **`docs/policy/*` を議論を勝つために変えない** — policy 変更は別 PR
- **PR の diff 外のファイルを触らない**（thread が明示的にそのファイルを指していない限り）
- **人間 reviewer がコメントを残したら**、それが質問でない限り deference して polite ack のみ

### 3.6 セッションを跨ぐ場合

セッションが終わると両 loop も止まる。次のセッションを始めるときに 2 行打つ:

```text
/loop 12h /loop-pr-review
/loop 5m  /loop-pr-discussion
```

「Claude が動いていない時間帯」は PR がそのまま待つ（人間が merge するか、次のセッションを開始したら進む）。

---

## 4. 手動実行

```text
/pr-review <PR#>
```

- `pr-reviewer` subagent を **1 PR に対して 1 回**起動
- 結果はチャットに表示 + 同じテンプレで `gh pr comment` 投稿
- ループの cadence を待たずに再評価したいとき
- ループを動かしていないセッションでも使える

---

## 5. 観点の追加・改訂手順

新しい観点を追加するとき:

1. 本書 §1 のテーブルに行を追加（# / 観点 / 概要 / 主要チェックポイント）
2. §1.1 / §2 に閾値の差分があれば追記
3. [`.claude/agents/pr-reviewer.md`](../../.claude/agents/pr-reviewer.md) の Checklist サマリに同期（agent は本書を一次情報として参照する設計だが、サマリも合わせる）
4. `loop-pr-review` / `pr-review` コマンドの変更は通常不要（subagent を呼ぶだけ）
5. 既存 PR を再評価したいなら、PR に新規 commit を push（marker が無効になる）か `/pr-review <PR#>` を手動起動

### 5.1 観点候補（v0.2 以降で追加検討）

| 候補 | 必要になる時期 |
|---|---|
| パフォーマンス（latency / memory） | Phase 5 のデプロイ後、preview の SLO が定義されたら |
| コスト（追加クラウド資源、LLM トークン消費） | Phase 6 / 自走ループ起動後 |
| アクセシビリティ | UI が公開対象になったら |
| 国際化（i18n 影響） | 多言語対応が要件になったら |
| 後方互換性 | 公開 API が出たら（[`docs/policy/api-schema.md`](api-schema.md) §3.2） |
| 監視・可観測性 | 構造化ログ / トレース整備後 |
| データプライバシ | 個人情報を扱う要件が出たら |

---

## 6. 人間レビューの位置づけ

自動レビューは「**最低限の網羅**」であって最終承認ではない。

- main へのマージ前に **人間レビュー（少なくとも 1 人）必須**
- GitHub の **Required reviewers** / **Branch protection** で強制（Phase 0 終盤で設定）
- 自動レビューの APPROVE は人間レビューの代替にならない（あくまで人間の判断材料）

---

## 7. PR を書くがわのガイド（雑記）

- PR title: Conventional Commits prefix（`feat:` / `fix:` / `docs:` / `chore:` / `refactor:` / `test:`）
- PR body には **動機 / 変更点 / テスト方法 / 関連 Issue（Closes #N）** を入れる
- 1 PR = 1 Issue。`MAX_PR_DIFF_LINES=400` を超える場合は分割を検討（[`CLAUDE.md`](../../CLAUDE.md) §1）
- WARN を承知のうえで merge したい場合は PR body に **`Waiver: <criterion> — <理由>`** を明示

---

## 8. 更新ルール

- 観点追加・改訂は本書を起点に PR で
- `pr-reviewer` agent の振る舞いを変えるときは本書を先に更新する（agent はサマリを引いてくる）
- workflow 自体の変更は workflow + 本書 §3 を同時に更新

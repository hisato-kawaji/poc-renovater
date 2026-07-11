# フロントエンド ポリシー（叩き台 v0.1）

- 最終更新: 2026-06-22
- ステータス: Draft v0.1
- 親: [`docs/planning.md`](../planning.md) §3 / [`docs/app-architecture.md`](../app-architecture.md) §5 / [`docs/policy/api-schema.md`](api-schema.md)
- 対象読者: 開発者本人 + Claude Code

---

## 0. このドキュメントの目的

`apps/web` の **コードレベル規約** を確定する。とくに **state の分類と扱い方** を明確化する。これが揺れると、たった 1 つの一覧画面に React state / Context / Zustand / TanStack Query / nuqs が混在してメンテ困難になる。

---

## 1. スタック

| 項目 | 採用 |
|---|---|
| ランタイム | Next.js 15（App Router） |
| 言語 | TypeScript（strict, `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes` 有効） |
| パッケージマネージャ | pnpm |
| UI | shadcn/ui ベース + Tailwind v4（候補）。詳細は §9 で決める |
| アイコン | lucide-react |
| Linter | ESLint（`@typescript-eslint/strict-type-checked`）+ Biome（formatter） |
| Test | Vitest + React Testing Library（unit）+ Playwright（e2e） |
| Mock | MSW（API モック） |
| 型 | `@poc-renovater/shared`（packages/shared/ts/src 生成物）|

---

## 2. State の分類と推奨実装

UI に出てくる「state」は性質によって扱いが違う。**まず分類し、分類に応じたツールを使う**。混ぜない。

### 2.1 5 つの分類

| 分類 | 例 | 寿命 | 共有 | 推奨ツール |
|---|---|---|---|---|
| **Server state** | agent 一覧、PR 詳細、charter スコア | サーバ側の正本 | 全 client | **TanStack Query**（fetch + キャッシュ + 楽観更新） |
| **Live state** | 状態機械の遷移、CI 結果、preview URL | サーバ更新を push で受け取る | 全 client | **Firestore `onSnapshot`** を Client Component 内 Custom Hook に閉じ込め |
| **URL state** | 選択中の agent タブ、フィルタ、ページング cursor | URL に従う | URL を共有する全 client | **nuqs** |
| **Form state** | charter チャット入力、register フォーム | 提出するまで client のみ | 1 form | **React Hook Form**（zod resolver）+ Server Actions |
| **Ephemeral UI state** | ダイアログ open/close、tooltip、選択中アイテム | 一瞬 | 1 component / tree | **`useState` / `useReducer`** |
| **Shared client state**（少量） | サイドバー折りたたみ、テーマ、選択中 organization | セッション中 | 複数 component | **Zustand**（store は domain 単位で分割） |

**禁則**:
- ❌ Redux / MobX は採用しない（学習コストが ROI に見合わない）
- ❌ React Context を「状態管理」として使わない（再レンダリング制御が困難）。Context は **DI / Provider** にだけ使う
- ❌ Server state を `useState` に詰めない（同期ズレの原因）
- ❌ 同じデータを TanStack Query と Firestore listener の両方で扱わない（必ずどちらか一方）

### 2.2 Server state vs Live state の使い分け

| ケース | 採用 |
|---|---|
| 一覧の初回ロード + 操作後の refetch | **Server state**（TanStack Query） |
| 1 件の詳細で「状態が変わったら即反映」したい | **Live state**（Firestore listener） |
| Charter 壁打ちチャット | **Live state**（messages サブコレクションを listen） |
| CI 結果 / preview URL の更新通知 | **Live state** |
| Issue 一覧、PR 一覧 | 基本は **Server state**、必要なら listener 追加 |

判断基準: **「待っていれば自然に変わるもの」は Live**、**「操作の結果として変わるもの」は Server**。

### 2.3 ストアの構造化

Zustand store は **小さく分割**する:

```typescript
// apps/web/lib/stores/ui.ts
export const useUiStore = create<UiState>((set) => ({
  sidebarCollapsed: false,
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
}));

// apps/web/lib/stores/auth.ts  — Firebase Auth 状態のキャッシュ
// （Firebase SDK 自体が source of truth、これは UI 同期用）
```

`global-store.ts` のような巨大 store は禁止。

---

## 3. Server / Client Component の分割

### 3.1 デフォルトは Server Component

Next.js 15 App Router では **Server Component が既定**。Client Component には `"use client"` を明示する。

| 判断 | 採用 |
|---|---|
| 初期描画にデータが要る（agent 一覧、詳細） | **Server Component** で fetch（apps/api 経由 or fetch + revalidate）|
| Firebase Auth / Firestore listener / `useState` / イベントハンドラが要る | **Client Component** |
| Server Action を呼ぶフォーム | **どちらでも可**。フォーム自体は Client が多い |
| 静的（about ページ、404 など） | **Server Component** |

### 3.2 ハイブリッドの基本パターン

```tsx
// app/agents/[agentId]/page.tsx — Server Component
import { getAgent } from "@/lib/api/server";   // server fetch
import { AgentLiveView } from "./_components/agent-live-view";   // client

export default async function Page({ params }: { params: { agentId: string } }) {
  const initial = await getAgent(params.agentId);
  return <AgentLiveView agentId={params.agentId} initial={initial} />;
}
```

- **初期データは Server Component が取って prop で渡す**
- live 更新は Client Component が Firestore listener で上書き
- これで「初回ロードはサーバから安全に / 以後はリアルタイム」のハイブリッドが成立

### 3.3 禁則

- ❌ Client Component から `apps/api` への fetch をマウント直後にしない（Server Component で先に取って prop に）
- ❌ Server Component で Firestore Web SDK を使わない（Web SDK は client 専用）
- ❌ `"use client"` をファイル冒頭に書いたうえで React Hook を使う**だけ**の Component を増やさない（無駄に Client 化）

---

## 4. データフェッチ

### 4.1 Server Component の fetch

```typescript
// apps/web/lib/api/server.ts
import { AgentSchema, type Agent } from "@poc-renovater/shared";

export async function getAgent(id: string): Promise<Agent> {
  const r = await fetch(`${process.env.API_BASE_URL}/api/v1/agents/${id}`, {
    cache: "no-store",
    headers: { Authorization: `Bearer ${await serverIdToken()}` },
  });
  if (!r.ok) throw new ApiError(r);
  return AgentSchema.parse(await r.json());
}
```

- **必ず schema.parse**（zod or 同等）。受信時の型保証を捨てない
- `cache` は基本 `no-store`（個人化データなので CDN キャッシュ厳禁）

### 4.2 Client Component の fetch（TanStack Query）

```typescript
// apps/web/lib/api/client.ts
export const agentsQuery = (id: string) => ({
  queryKey: ["agents", id],
  queryFn: async () => AgentSchema.parse(await apiGet(`/agents/${id}`)),
});

// Component:
const { data, error, isLoading } = useQuery(agentsQuery(id));
```

- queryKey は **配列形式**（フィルタ等を追加しやすい）
- **prefetch on hover** は積極的に（特に一覧 → 詳細遷移）

### 4.3 Firestore listener（Live state）

```typescript
// apps/web/lib/firestore/use-agent-live.ts
"use client";
import { useEffect } from "react";
import { onSnapshot, doc } from "firebase/firestore";
import { useQueryClient } from "@tanstack/react-query";
import { db } from "@/lib/firebase";
import { AgentSchema } from "@poc-renovater/shared";

export function useAgentLive(agentId: string) {
  const qc = useQueryClient();
  useEffect(() => {
    return onSnapshot(doc(db, "agents", agentId), (snap) => {
      const parsed = AgentSchema.parse({ id: snap.id, ...snap.data() });
      qc.setQueryData(["agents", agentId], parsed);
    });
  }, [agentId, qc]);
}
```

- **listener は Custom Hook に閉じ込める**。Component 本体には書かない
- listener から受け取ったデータは **TanStack Query のキャッシュに書き戻す**（Server state と Live state の整合）
- unsubscribe を必ず返す（`useEffect` の cleanup）

### 4.4 書き込みは API のみ

```typescript
// apps/web/lib/api/client.ts
export async function approvePull(agentId: string, n: number) {
  return apiPost(`/agents/${agentId}/pulls/${n}:approve`, undefined, {
    headers: { "Idempotency-Key": crypto.randomUUID() },
  });
}
```

- フロントから **Firestore に直接 write しない**（書き込み権限は API のみ）
- 副作用 POST には `Idempotency-Key` を付ける（リトライ安全）

---

## 5. マルチテナントとダッシュボード (Phase 2/3 対応)

### 5.1 マルチテナント対応
APIへの全リクエストは `X-Tenant-ID` ヘッダが必須となる。
フロントエンドでは、ユーザーの所属するテナント情報を保持し、fetch関数に自動的に注入する仕組みを構築する。

- **状態保持**: ユーザーのテナント一覧や選択中の `tenant_id` を Zustand (または URL/Cookie) に保持する。
- **リクエスト注入**: `apiGet` や `apiPost` のラッパー関数内で `X-Tenant-ID` ヘッダを自動付与する。

### 5.2 マルチPoCダッシュボード (運用監視)
Phase 3 での運用監視に向けて、システム全体の状況を把握するダッシュボードを構築する。
- **データの種類**: Server state (Agent一覧、各種メトリクス) と Live state (進行中のAgent状態) をハイブリッドに組み合わせる。
- **監視要素**: 各PoCのフェーズ、エラー発生状況、プレビュー環境の稼働数。

---

## 6. フォーム

### 5.1 Charter 壁打ちなど

- React Hook Form + zod resolver
- 提出は Server Action または apiPost
- 入力中の状態は **form state（hook form 内部）**、サーバへの送信完了で **server state 更新**

### 5.2 サンプル骨格

```tsx
"use client";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { CharterMessageInputSchema } from "@poc-renovater/shared";

export function CharterInput({ agentId }: { agentId: string }) {
  const form = useForm({ resolver: zodResolver(CharterMessageInputSchema) });
  const onSubmit = form.handleSubmit(async (values) => {
    await sendCharterMessage(agentId, values);
    form.reset();
  });
  return <form onSubmit={onSubmit}>...</form>;
}
```

---

## 7. 認証

### 6.1 流れ

1. Firebase Auth でログイン（Google プロバイダ）
2. クライアントは `auth.currentUser.getIdToken()` で ID Token を取得
3. **fetch ごとに `Authorization: Bearer <token>` を付ける**（middleware で apps/api 側が検証）

### 6.2 Server Component の場合

Server Component では Firebase Auth SDK が動かない。**Token は cookie 経由で server に渡す**:

- Client が初期化時に `auth.onIdTokenChanged` で token を取得 → `/api/auth/set-cookie` に POST して httpOnly cookie を設置（Next.js Server Action 経由）
- Server Component は cookie から token を取り出して fetch

⚠ **Phase S で要確認**（spike-4 / spike-5 と併せて）: この cookie 戦略でセキュリティが回るか。代案は **API 経由でしか Server Component が GCP リソースを読まない** にすれば、Firestore Web SDK が Server で動かない問題を回避できる。

### 6.3 ログアウト後の挙動

- Firebase signOut → cookie 削除 → 全 query invalidate → ホームへ redirect

---

## 8. エラー / Loading の境界

### 7.1 Suspense と Error Boundary

- 各 route segment に `loading.tsx` / `error.tsx` を必ず置く（App Router の規約）
- Client Component 内の `useQuery` は `isLoading` / `error` で個別ハンドリング
- 401 → `/login` へリダイレクト（global interceptor 1 箇所）

### 7.2 エラー表示

- API のエラーエンベロープ（`{code, message, details, request_id}`）を **そのまま UI に出さない**。`code` で分岐したフレンドリーメッセージに変換
- `request_id` は折りたたみで表示（サポート向け）

### 7.3 トースト

- 副作用成功（PR approve など）は Toast で短く（sonner 推奨）
- 失敗は modal で詳細 + retry ボタン

---

## 9. テスト

| 種類 | ツール | 何を見る |
|---|---|---|
| 単体 | Vitest + React Testing Library | component の表示と分岐 |
| API モック | MSW | apps/api への fetch を network レベルで擬似 |
| Firestore モック | Firebase Emulator（任意） / fake listener 関数 | onSnapshot の動作 |
| e2e | Playwright | demo シナリオ §11 を browser で通す |
| 型回帰 | tsc --noEmit | packages/shared と整合確認 |

CI で **type / lint / unit / e2e の subset** を回す。

---

## 10. ⚠ 未確定項目（Phase S / Phase 0 終盤で確定）

| 項目 | 状態 | タイミング |
|---|---|---|
| UI ライブラリ（shadcn/ui か Mantine か） | shadcn/ui 推し（軽量・Tailwind 親和） | Phase 0 終盤 |
| Tailwind v4 採用可否 | v4 が GA なら採用 | Phase 0 終盤 |
| Server Component で Firebase Auth cookie 渡し戦略 | §6.2 案で進める | spike-4 / spike-5 |
| Firestore listener の Server Component 補完法 | client 限定方針で行く | spike-5 |
| MSW を CI で動かす | 採用方針、ハンドラ管理は別途 | Phase 1 で |

---

## 11. 採用ルール（短く）

1. **state はまず分類** → 分類に応じたツールを選ぶ。混ぜない
2. **Server Component が既定**、Client は理由があるときだけ
3. 初期データ = Server Component、live = Firestore listener、書き込み = API
4. 受信した JSON は **必ず zod parse**、`any` 禁止
5. 副作用 POST は **`Idempotency-Key`** をつける
6. **listener は Custom Hook**、Component 本体に直接書かない
7. エラーは `code` で分岐、`details` は折りたたみ、`request_id` は常に表示できる

---

## 12. 更新ルール

- state 分類の変更は本書の更新 → `app-architecture.md` §5 も同時に
- 新しい UI ライブラリの追加は **同種ライブラリの撤去** とセットで（並走禁止）

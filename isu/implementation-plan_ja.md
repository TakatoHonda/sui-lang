# Isu 実装方針

## 目的

- 人間の自然言語指示から、LLM が **Isu（構造化疑似コード）**を生成する
- Isu を **決定論的にパース**して **S-IR（AST）**へ変換する
- S-IR から **任意の実行ターゲット**へコンパイルする（まずは Python / Wasm / LLVM IR など既存基盤を優先）
- 失敗時は、Isu まで巻き戻して **修正ループ**を回す（IR 以降は原則決定論的）

---

## 全体アーキテクチャ

```text
[User NL]
   |
   v
[LLM] --(Isu text)--> [Parser] --(S-IR JSON AST)--> [Compiler] --> [Backend Runtime]
   ^                          |                              |
   |                          v                              v
   +------(errors/spec)--- [Validator] ------------------ [Test/Trace]
```

### レイヤの役割

- **Isu（テキスト）**: LLM が読む・書く一次成果物
- **S-IR（JSON AST）**: Isu と 1:1 対応する決定論的内部表現
- **Backend**: Python / Wasm / LLVM IR など。将来必要なら専用 VM も検討

---

## 仕様設計の基本原則

### 1. 決定論性

- Isu → S-IR は必ず一意に決まる
- 文法・字句・スコープ・型推論の曖昧さを排除する
- 曖昧さが必要な箇所は **構文で要求する**（例: `ELSE:` を必須にする、など）

### 2. 最小の制御構造

- `SEQ` / `IF` / `LOOP` / `ASSIGN` / `RETURN`
- これ以外は基本的にメタで表現（例: `BREAK` は `LOOP` の属性や `IF + RETURN` で代替する）

### 3. 閉じた語彙

- `kind` は有限集合（拡張は慎重に）
- 標準関数（例: `LEN`, `MAP_HAS`, `SPLIT_WHITESPACE`）は **小さな標準セット**として固定
- 任意のユーザ定義関数名や任意の API 名爆発を避ける

### 4. LLM 生成を前提にした文法

- 行頭キーワード固定
- **インデントを意味に使わない**（整形専用にする）
- ブロック境界は **明示トークン**で決める（`BEGIN` / `END`）
- ステップ ID は正規形では必須（`S1`, `S2_1` など）。ただし入力は `AUTO_ID` により省略を許す（後述）

---

## LLM が生成しやすい仕様（生成容易性の原則）

LLM の生成で事故りやすい点（ブロック閉じ忘れ、キー名の揺れ、Step ID の重複/欠番、式の括弧ミス）を仕様で吸収する。

### 原則

- **正規形（canonical）を 1 つに固定**し、実装は必ず「正規化」してから処理する
- **入力は多少ゆるく、出力は厳密に**する（LLM は入力、コンパイラは正規形を返す）
- **同じ意味の別名を作らない**（`TARGET/DEST` のような同義語は禁止）
- **ノードごとのフィールド順を固定**し、欠落・余剰を検出しやすくする

### 生成事故を減らす仕組み（v0 から入れる）

- **AUTO_ID**
  - 生成時は Step ID の省略を許す（`AUTO_ID: true`）
  - パーサ/正規化で `S1,S2,...` を安定採番し、以降はその ID を基準にエラー/パッチを返す
- **ブロック短縮表記**
  - `BEGIN/END` を正規形としつつ、入力として `THEN: { ... }` / `ELSE: { ... }` / `BODY: { ... }` を許す
  - `{}` は閉じ忘れが少なく、LLM の生成が安定する
- **フィールド順の固定**
  - `IF`: `COND` → `THEN` → `ELSE`
  - `LOOP`: `ITER` → `BODY`
  - `ASSIGN`: `TARGET` → `EXPR`
  - `RETURN`: `EXPR`

## v0 で固定する構文方針（最重要）

### ブロック構文（インデント非依存）

YAML 風インデントは曖昧さと事故率が高いので採用しない。v0 では以下を仕様とする。

- ブロック開始: `BEGIN`
- ブロック終了: `END`
- `THEN` / `ELSE` / `BODY` は **必ず `BEGIN` を伴う**
- 空行は許可（字句解析で無視する）
- コメント行は許可（行頭 `;` をコメントとして無視する）

### ブロック短縮表記（入力のみ許可）

- 入力として `THEN: { ... }` / `ELSE: { ... }` / `BODY: { ... }` を許す
- 正規化で必ず `BEGIN/END` へ展開し、内部処理は `BEGIN/END` のみを扱う

例:

```text
S2: IF
  COND: (lt (var i) (LEN (var xs)))
  THEN: BEGIN
    S2_1: ASSIGN
      TARGET: i
      EXPR: (add (var i) (const 1))
  END
  ELSE: BEGIN
    S2_2: RETURN
      EXPR: (const false)
  END
```

## フェーズ別実装計画

## Phase 0: 最小実行パイプライン（MVP）

### 0.1 Isu 最小仕様（v0）

必須セクション:

- `FUNC`
- `IO`
- `STATE`
- `LOCAL`
- `STEPS`

`LOCAL` は関数内の一時変数宣言セクションで、ブロックスコープは導入しない（関数スコープのみ）。

補助セクション（任意）:

- `META`
  - `AUTO_ID: true|false`（true の場合、Step ID 省略を許し、正規化で安定採番する）

必須ノード:

- `SEQ`
- `ASSIGN`
- `IF`
- `LOOP`
- `RETURN`

式（Expr DSL）最小:

v0 は「インフィックス式文字列」を捨て、パースが容易で決定論的な **前置（S式）**に統一する。

- 定数: `(const 1)`, `(const "x")`, `(const true)`
- 変数参照: `(var name)`
- 二項演算: `(add a b)`, `(sub a b)`, `(mul a b)`, `(div a b)`, `(mod a b)`
- 比較: `(eq a b)`, `(ne a b)`, `(lt a b)`, `(le a b)`, `(gt a b)`, `(ge a b)`
- 配列アクセス: `(index a i)`
- 関数呼び出し（v0は標準関数のみ）: `(call FN arg1 arg2 ...)`
  - `FN` は v0 では標準関数名に限定する（閉じた語彙の維持）
  - 例: `(call LEN (var xs))`, `(call MAP_GET (var m) (var k))`

備考:

- 優先順位・結合規則・括弧・エスケープなどの罠を v0 から排除する
- 人間可読性は pretty-printer で担保する（整形すれば読める形に寄せる）
- `CALL` ステートメントは v0 では導入しない（Expr に統一して揺れを消す）

### 0.2 パーサ実装

- PEG か Lark/ANTLR などで **公式文法**を作り、同じ文法を
  - 構文解析（Isu → S-IR）
  - LLM 出力制約（将来: grammar-constrained decoding）
  の両方に使える形で管理する

出力:

- `S-IR (JSON)` を必ず生成
- 生成した IR を再度 pretty-print して **Isu に戻せる**（双方向整形）ことを最初から入れる
- 解析後に必ず **正規化（canonicalize）** を行い、以降の処理は正規形のみを対象にする
  - `{}` ブロックは `BEGIN/END` に展開
  - `AUTO_ID` が true の場合、Step ID を安定採番
  - フィールド順・必須キーを正規形に揃える

### 0.3 バリデータ（静的検査）

- ステップ ID の一意性
- 参照されるステップ ID の存在
- 変数の宣言済みチェック（`STATE` + `IO` + `LOCAL` 以外の変数出現禁止）
- 型の整合（初期は弱くてよいが、`int` と `string` の混在程度は弾く）
- `RETURN` の型が関数シグネチャと一致

### 0.4 バックエンド（最初はインタプリタ、その後 Python）

- v0 は **S-IR インタプリタ**を実装し、実行とトレースの正しさを最優先する
- 実行時例外は Isu のステップ ID へマップして返す（重要）
- Python バックエンド（`ast` 生成やソース生成）は v0 の次に段階導入する（性能や配布都合に応じて）

### 0.5 パッチ適用（修正ループの核を先に作る）

Phase 1 に送る前に、v0 で最小のパッチ適用器を実装する。

- `REPLACE <StepID>:` のみ対応
- 適用は「S-IR への変換後」に行う（テキスト編集より決定論的で壊れにくい）
- パッチ本文は Isu の断片を許し、差し替え対象のステップを **断片だけパースして S-IR に正規化**してから置換する
- 置換後は必ず pretty-printer を通し、正規形の Isu を返せるようにする
- 適用後は必ず validator を再実行し、差分が最小になるよう pretty-printer を通す

---

## Phase 1: エラーフィードバックと修正ループ

### 1.1 エラーモデル

エラーを必ず構造化して返す。

- `ParseError`（Isu 文法違反）
- `StaticError`（未宣言変数、型不整合、未定義ステップ参照）
- `RuntimeError`（ゼロ除算、範囲外アクセス、キー不存在など）
- `TestFail`（入出力例に対する不一致）

### 1.2 ステップ単位の差分指示

LLM に返すフィードバックは「ステップ ID 単位」。

例:

- `S2_1` の `COND` が常に false
- `S3_2` の `ASSIGN` で `v_best` の更新条件が誤り
- `S4` の `RETURN` 型が `int` であるべき

### 1.3 反復生成戦略

- 1回目: LLM は Isu 全体生成
- 2回目以降: LLM は **対象ステップのみ再生成**（パッチ形式）

パッチ形式例:

```text
PATCH:
  REPLACE S2_1:
    S2_1: IF "..."
      COND: ...
      THEN: BEGIN
        ...
      END
```

パッチ適用はコンパイラ側で決定論的に行う。

---

## Phase 2: 標準ライブラリと「閉じた語彙」の拡張

### 2.1 標準関数（例）

- 配列: `LEN`, `PUSH`, `POP`, `SLICE`
- マップ: `MAP_HAS`, `MAP_GET`, `MAP_SET`
- 文字列: `SPLIT_WHITESPACE`, `JOIN`, `LOWER`
- 数学: `ABS`, `MIN`, `MAX`

原則:

- 同じ意味の API を増やさない
- 形（引数順・戻り値）を統一する

### 2.2 型システムの強化（段階的）

- v1: `int`, `bool`, `string`, `T[]`, `map<K,V>`
- v2: `struct`（固定フィールドのみ）
- v3: 参照/所有の概念（必要なら）

---

## Phase 3: ターゲット拡張

### 3.1 Wasm

- S-IR → Wasm（WAT かバイナリ）へコンパイル
- まずは整数・配列・ループ中心の subset に限定

### 3.2 LLVM IR

- S-IR → LLVM IR を生成
- SSA 化はコンパイラ側で行う（Isu は SSA を要求しない）

---

## ディレクトリ構成案

```text
isu/
  spec/
    isu.ebnf
    sir.schema.json
    stdlib.md
  isu/
    parser/
    ast/
    validator/
    compiler/
      python_backend/
      wasm_backend/
      llvm_backend/
  tests/
    golden/
    property/
  tools/
    fmt/
    patch/
    trace/
```

---

## 重要な仕様決定（早期に固めるべき）

1. **インデント規則**
   - v0 はインデント非依存（整形専用）
   - タブ禁止（見た目の安定のため）
   - ブロックは `BEGIN/END` で決める（決定論性の要）

2. **ステップ ID の形式**
   - `S` + 数字 + `_` + 数字… を許すか
   - ソート順が構造順になるルール（デバッグ容易性）
   - `AUTO_ID` を許すか（許すなら正規化で安定採番し、以降はその ID を基準にする）

3. **式 DSL の文法**
   - v0 は S式（前置）に固定する（優先順位問題を消す）
   - 関数呼び出しの許可範囲（標準関数のみ）

4. **スコープ**
   - 変数は関数スコープのみ（ブロックスコープなし）にすると単純
   - ループ変数は `LOCAL` で宣言し、`ITER` は代入先（名前）として参照する

5. **未定義挙動の排除**
   - 範囲外アクセスは必ず例外
   - `MAP_GET` はキーなしなら例外（または `MAP_GET_OR` を導入）

---

## LLM 連携の実装方針

### 出力制約

- 最初は正規表現ベースで最低限の制約
- 次に EBNF/PEG による grammar-constrained decoding を導入
- さらに JSON Schema による S-IR 直接生成も選択肢として残す（ただし主流は Isu）

### 生成プロンプト方針（要点）

- `FUNC/IO/STATE/LOCAL/STEPS` の順を強制
- `META` を使う場合は先頭に置く（例: `META: AUTO_ID: true`）
- ステップ ID を必ず付与
  - ただし `AUTO_ID: true` の場合は省略可とし、コンパイラが正規形を返すことを前提にする
- `COND`, `ITER`, `THEN`, `ELSE`, `BODY` を省略不可にする
- `THEN/ELSE/BODY` は必ず `BEGIN/END` で囲む
  - 生成容易性のため、入力として `{}` を許す場合は `{}` を推奨し、正規化で `BEGIN/END` に落とす
- v0 の関数呼び出しは `(call FN ...)` に統一する（FNは標準関数のみ）

最小テンプレ（生成用）:

```text
META:
  AUTO_ID: true
FUNC:
  NAME: f
  ARGS: []
  RETURNS: int
IO:
  INPUT: []
  OUTPUT: []
STATE: []
LOCAL: []
STEPS:
  SEQ: BEGIN
    ASSIGN:
      TARGET: x
      EXPR: (const 0)
    RETURN:
      EXPR: (var x)
  END
```

---

## 関連手法の調査と比較（Isu の立ち位置）

Isu は「LLM の出力を、決定論的に実行可能な中間言語へ落とす」設計である。近い手法は多数あるが、**置き換え関係**と**補完関係**が混ざるため、用途別に整理する。

### 1) JSON Schema / Function Calling / Structured Outputs（構造化出力）

- **概要**: LLM に JSON を生成させ、スキーマ一致を強制する。S-IR を直接出させる方向に近い。
- **強い点**: 構文崩壊（パース不能）が激減し、バリデーションも単純になる。
- **Isu の優位性**:
  - 人間がレビュー/編集しやすい一次成果物を残しやすい
  - Step 単位の差分パッチ運用を前提にしやすい
- **優位性が薄いケース**:
  - 人間可読な中間表現が不要で、最初から AST（JSON）で回せる場合は **S-IR 直生成の方が単純**になりやすい

### 2) Grammar-constrained decoding（文法制約生成: EBNF/CFG 等）

- **概要**: デコード時に文法でトークンをマスクして、文法違反の出力をそもそも生成しない。
- **強い点**: Isu を採用するなら、これを入れるだけで `ParseError` を大幅に減らせる。
- **Isu との関係**: 競合ではなく補完で、Isu の「決定論パース」を現実的にする必須寄りの技術だ。

### 3) SCoT（Structured Chain-of-Thought）系

- **概要**: CoT の中間推論を、コードに近い構造（sequence/branch/loop 等）へ寄せて生成品質を上げるプロンプト手法。
- **強い点**: 「考え方の形」をモデルに強制でき、コード生成の pass@1 を上げる報告がある。
- **Isu の優位性**:
  - SCoT はあくまで **プロンプト戦術**で、生成物の意味論/実行は外部で担保されない
  - Isu は **仕様・パーサ・validator・トレース**を含む枠組みなので、運用/デバッグの再現性が取りやすい
- **結論**: SCoT は「Isu を生成させるためのプロンプト設計」として取り込むのが自然で、直接の競合ではない。

### 4) ReAct / Reflexion（エージェント的ループ）

- **概要**: 推論と行動を交互に出し、外部ツールや環境からフィードバックを得て修正する。
- **強い点**: 探索と情報収集に強く、閉じた語彙では表現しにくいタスクで前に進みやすい。
- **Isu の優位性**: 実行経路がテキスト推論に引きずられにくく、**決定論パイプラインで再現性**を確保しやすい。
- **結論**: ReAct/Reflexion は「Isu 生成・修正の外側の制御ループ」として併用するのが相性が良い。

### 5) PAL（Program-Aided Language Models）/ 直接コード生成 + 実行

- **概要**: LLM が Python 等のプログラムを中間生成し、インタプリタで実行して推論を補助する。
- **強い点**: 立ち上げが速く、既存言語の実行系・ライブラリを即利用できる。
- **Isu の優位性**:
  - ターゲット非依存（Python 偏重を避け、Wasm/LLVM へも拡張しやすい）
  - ステップ ID と validator により、**実行時のエラー局所化**を設計に組み込める

### 6) ToT（Tree of Thoughts）/ Self-Consistency（探索・サンプリング）

- **概要**:
  - ToT: 複数の思考分岐を探索し、評価して枝刈りする
  - Self-Consistency: 複数サンプルから多数決/整合で最終解を選ぶ
- **Isu との関係**:
  - 複数の候補 Isu を生成し、validator とテストでスコアリングして選ぶ設計に落とし込みやすい
  - `AUTO_ID` と正規化があると、候補比較・差分適用が安定する

### 7) DSPy（プロンプト最適化/宣言的パイプライン）

- **概要**: 手作業プロンプトではなく、評価指標を使ってプロンプトを最適化する枠組み。
- **Isu との関係**: 「Isu 生成器」を DSPy で最適化し、validator/test を教師信号にできる。

### 参考リンク

- SCoT（code generation）: [Structured Chain-of-Thought Prompting for Code Generation（arXiv:2305.06599）](https://arxiv.org/abs/2305.06599)
- ReAct: [ReAct: Synergizing Reasoning and Acting in Language Models（arXiv:2210.03629）](https://arxiv.org/abs/2210.03629)
- PAL: [PAL: Program-Aided Language Models（arXiv:2211.10435）](https://arxiv.org/abs/2211.10435)
- ToT: [Tree of Thoughts（arXiv:2305.10601）](https://arxiv.org/abs/2305.10601)
- Self-Consistency: [Self-Consistency Improves Chain of Thought Reasoning（arXiv:2203.11171）](https://arxiv.org/abs/2203.11171)
- Reflexion: [Reflexion: Language Agents with Verbal Reinforcement Learning（arXiv:2303.11366）](https://arxiv.org/abs/2303.11366)
- Structured Outputs（OpenAI）: [Introducing Structured Outputs in the API](https://openai.com/index/introducing-structured-outputs-in-the-api/)
- LMQL constraints: [LMQL: Output Constraints](https://lmql.ai/docs/language/constraints.html)
- Outlines CFG: [Outlines: Context-free grammars](https://dottxt-ai.github.io/outlines/latest/reference/generation/cfg/)
- Guidance: [guidance-ai/guidance（GitHub）](https://github.com/guidance-ai/guidance)
- DSPy: [stanfordnlp/dspy（GitHub）](https://github.com/stanfordnlp/dspy)

## テスト戦略

### 1. ゴールデンテスト

- Isu → S-IR → Isu（整形）で同値性チェック
- Isu → 実行（v0 はインタプリタ） の期待値チェック

### 2. プロパティテスト

- 生成したランダム S-IR を Isu へ落とし、再パースして同値であること
- ループ境界や配列アクセスの例外が正しく出ること

### 3. ラウンドトリップ評価（将来）

- Isu → NL 要約 → Isu の往復で意味保存性を測る（RTC 的評価）

---

## 成功指標（最初に測る）

- **決定論性**: 同一入力 Isu が常に同一 S-IR（シリアライズの完全同値）になる
- **トレース整合**: 実行時例外の大半が「ステップ ID + 変数名 + 型/値」で特定できる
- **修正効率**: パッチ 1〜2 回でテストに通る割合を継続測定し、下がったら仕様/validator/stdlib を見直す

## この方針における最重要ポイント

- **LLM が触るのは Isu のみ**
- **Isu → S-IR は 100% 決定論的**
- **S-IR → 実行コードも決定論的**
- 失敗時は **Isu レベルに戻して修正**する
- 「閉じた語彙」「最小構造」を徹底し、LLM に過度な自由度を与えない

# 粋 (Sui) - LLMのためのプログラミング言語

> 構文エラー率ゼロ。タイポ不可能。LLMが書いたコードがそのまま動く。

[English README](README.md)

## 概要

**粋 (Sui)** は「洗練」「無駄を削ぎ落とす」という日本語の美意識から名付けられた、LLMが**100%正確なコード**を生成できるように設計されたプログラミング言語である。希望的観測ではなく、構造的保証によって実現する。

## なぜSuiか

**現在のLLMコード生成の問題：**
- 括弧の対応ミス `if (x { }`
- 変数名のタイポ `coutn` vs `count`
- インデントエラー
- 複雑なネスト

**Suiはこれらのエラーを構造的に不可能にする：**

| 問題 | Suiの解決策 |
|------|-------------|
| 括弧の対応ミス | 関数定義の`{}`のみ、ネストなし |
| 変数名のタイポ | 連番のみ（v0, v1, g0）- スペルミス不可能 |
| インデントエラー | 行ベース、インデントは無視 |
| 複雑なネスト | 1行1命令、一時変数に分解 |

## 設計原則

1. **構文エラー率ゼロ** - 構造的に構文エラーが発生しない
2. **タイポ率ゼロ** - 変数は数値、名前ではない
3. **行単位独立性** - 各行が完全に自己完結
4. **純粋ロジック言語** - 計算のみ、UIは任意のフレームワークに委譲
5. **将来のトークン効率** - LLMがSuiを学習すれば、従来言語を超える効率に

## インストール

```bash
# PyPI（基本）
pip install sui-lang

# PyPI（WebAssemblyサポート付き）
pip install sui-lang[wasm]

# Homebrew (macOS/Linux)
brew tap TakatoHonda/sui
brew install sui-lang

# ソースから
git clone https://github.com/TakatoHonda/sui-lang.git
cd sui-lang
```

## クイックスタート

### インタラクティブモード (REPL)

```bash
# REPL起動
sui

# セッション例
>>> = v0 10
>>> + v1 v0 5
>>> . v1
>>>
15
>>> .exit
```

コマンド: `.exit` / `.quit` (終了), `.reset` (状態リセット)

### インタプリタ

```bash
# ファイル実行
sui examples/fibonacci.sui

# 引数付き実行
sui examples/fib_args.sui 15

# バリデーション
sui --validate examples/fibonacci.sui

# ヘルプ表示
sui --help
```

### トランスパイラ（Sui → Python）

```bash
# 変換結果を表示
sui2py examples/fibonacci.sui

# ファイルに出力
sui2py examples/fibonacci.sui -o fib.py

# 変換して即実行
sui2py examples/fib_args.sui --run 15
```

### トランスパイラ（Python → Sui）人間向け

```bash
# 変換結果を表示
py2sui your_code.py

# ファイルに出力
py2sui your_code.py -o output.sui
```

### WebAssembly

```bash
# WebAssembly Text Format (WAT) に変換
sui2wat examples/fibonacci.sui
sui2wat examples/fibonacci.sui -o fib.wat

# WebAssemblyで直接実行（要: pip install sui-lang[wasm]）
suiwasm examples/fibonacci.sui
```

### ブラウザUI

Suiは**純粋ロジック言語**。UIは任意のフレームワーク（React, Vue, Hono.js, vanilla JS等）で実装可能。

SuiはWasmにコンパイルされ、以下をexportする：
- `main()` - 初期化
- `f0()`, `f1()`, ... - 関数（JSから呼び出し可能）
- `g0`, `g1`, ... - グローバル変数（`.value`で読み書き）

```javascript
// 任意のフレームワークで動作
const wasm = await WebAssembly.instantiate(wasmBytes, { env: { print_i32: console.log }});
button.onclick = () => { wasm.exports.f0(); display.textContent = wasm.exports.g0.value; };
```

### インストールせずに実行（ソースから）

```bash
# pythonコマンドで直接実行
python sui.py examples/fibonacci.sui
python sui2py.py examples/fibonacci.sui
python py2sui.py your_code.py
```

## 構文

### 命令一覧

| 命令 | 形式 | 説明 |
|------|------|------|
| `=` | `= var value` | 代入 |
| `+` | `+ result a b` | 加算 |
| `-` | `- result a b` | 減算 |
| `*` | `* result a b` | 乗算 |
| `/` | `/ result a b` | 除算 |
| `%` | `% result a b` | 剰余 |
| `<` | `< result a b` | 小なり（結果0/1） |
| `>` | `> result a b` | 大なり（結果0/1） |
| `~` | `~ result a b` | 等価（結果0/1） |
| `!` | `! result a` | NOT |
| `&` | `& result a b` | AND |
| `\|` | `\| result a b` | OR |
| `?` | `? cond label` | 条件ジャンプ |
| `@` | `@ label` | 無条件ジャンプ |
| `:` | `: label` | ラベル定義 |
| `#` | `# id argc {` | 関数定義開始 |
| `}` | `}` | 関数定義終了 |
| `$` | `$ result func args...` | 関数呼び出し |
| `^` | `^ value` | return |
| `[` | `[ var size` | 配列作成 |
| `]` | `] result arr idx` | 配列読取 |
| `{` | `{ arr idx value` | 配列書込 |
| `.` | `. value` | 出力 |
| `,` | `, var` | 入力 |

### 変数

| 形式 | 意味 |
|------|------|
| `v0`, `v1`, ... | ローカル変数 |
| `g0`, `g1`, ... | グローバル変数 |
| `a0`, `a1`, ... | 関数引数 |
| `g100` | argc（コマンドライン引数の数） |
| `g101`, `g102`, ... | argv（コマンドライン引数） |

## 例

### フィボナッチ

```sui
# 0 1 {
< v0 a0 2
! v1 v0
? v1 1
^ a0
: 1
- v2 a0 1
$ v3 0 v2
- v4 a0 2
$ v5 0 v4
+ v6 v3 v5
^ v6
}
= g0 10
$ g1 0 g0
. g1
```

**出力**: `55`

### FizzBuzz

```sui
= v0 1
: 0
> v1 v0 100
? v1 9
% v2 v0 15
~ v3 v2 0
? v3 1
% v4 v0 3
~ v5 v4 0
? v5 2
% v6 v0 5
~ v7 v6 0
? v7 3
. v0
@ 4
: 1
. "FizzBuzz"
@ 4
: 2
. "Fizz"
@ 4
: 3
. "Buzz"
@ 4
: 4
+ v0 v0 1
@ 0
: 9
```

### リストの合計

```sui
[ g0 5
{ g0 0 10
{ g0 1 20
{ g0 2 30
{ g0 3 40
{ g0 4 50
= g1 0
= v0 0
: 0
< v1 v0 5
! v2 v1
? v2 1
] v3 g0 v0
+ g1 g1 v3
+ v0 v0 1
@ 0
: 1
. g1
```

**出力**: `150`

## ファイル構成

```
sui/
├── README.md           # 英語版README
├── README_ja.md        # このファイル（日本語）
├── LICENSE             # MITライセンス
├── sui.py              # インタプリタ
├── sui2py.py           # Sui → Python トランスパイラ
├── sui2wat.py          # Sui → WebAssembly Text Format トランスパイラ
├── suiwasm.py          # WebAssemblyランタイム（wasmtimeで実行）
├── py2sui.py           # Python → Sui トランスパイラ（人間向け）
├── examples/
│   ├── fibonacci.sui
│   ├── fib_args.sui
│   ├── fizzbuzz.sui
│   ├── list_sum.sui
│   └── args_demo.sui
└── prompts/
    ├── system_prompt_en.md  # LLM用システムプロンプト（英語）
    ├── system_prompt_ja.md  # LLM用システムプロンプト（日本語）
    └── examples.md          # アプリケーション例（Sui + UI）
```

## LLM連携

SuiはLLMによるコード生成のために設計されている。`prompts/` ディレクトリのプロンプトを使用：

1. `prompts/system_prompt_ja.md` からシステムプロンプトをコピー
2. ChatGPT / Claude / Gemini 等に貼り付け
3. タスクを指定してSuiコードを生成させる
4. `sui your_code.sui` で実行

プロンプトテンプレートと期待される出力は [prompts/examples.md](prompts/examples.md) を参照。

## 名前の由来

**粋（すい/いき）** - 日本語で「洗練されている」「無駄がない」という意味。余計なものを削ぎ落とし、本質だけを残す美意識を表す。

## トークン効率：現在 vs 将来

**現状**（LLMはまだSuiを知らない）：
| 言語 | フィボナッチ | カウンター |
|------|-------------|-----------|
| Sui | 79 tokens | 44 tokens |
| Python | 30 tokens | 30 tokens |

**将来**（LLMがSuiを学習した後）：
- `v0`, `g0` → 各1トークン（現在は2）
- `+ g0 g0 1` のようなパターン → 圧縮される
- 予測：**40-50%削減**

**しかしトークン数は本質ではない。** 真の価値：
- **構文エラー率0%**（Python/JSは約5-10%）
- **タイポ率0%**（変数名のスペルミスが構造的に不可能）
- **100%パース可能**（すべての行が有効か明確に無効）

## 他言語との比較

### vs Python/JavaScript

| 観点 | Python/JS | Sui |
|------|-----------|-----|
| 構文エラー | よくある | 不可能 |
| 変数タイポ | よくある | 不可能 |
| 括弧の対応 | エラー多発 | 自明 |
| トークン効率（現在）| 良い | 悪い |
| トークン効率（将来）| 同等 | より良い |

### vs アセンブラ

| 観点 | アセンブラ | Sui |
|------|-----------|-----|
| 命令数 | 数百 | ~20 |
| レジスタ | 8-32 | 無制限 |
| 学習コスト | 高い | 最小 |

## 今後の改善案

- [x] インタプリタ（Python）
- [x] トランスパイラ（Sui → Python）
- [x] トランスパイラ（Python → Sui、人間向け）
- [x] インタラクティブモード (REPL)
- [x] WebAssembly出力（WAT + ランタイム）
- [ ] 型注釈（オプション）
- [ ] LLVM IR出力

## ライセンス

MIT License


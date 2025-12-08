# 粋 (Sui) - LLMのためのプログラミング言語

> LLMが最も正確にコードを生成できるように設計された行ベース言語

[English README](README.md)

## 概要

**粋 (Sui)** は「洗練」「無駄を削ぎ落とす」という日本語の美意識から名付けられた、LLM（大規模言語モデル）が正確にコードを生成することを最優先に設計されたプログラミング言語である。

## 設計原則

1. **行単位独立性** - 各行が完全に自己完結
2. **括弧問題の最小化** - ネストは関数ブロック `{}` のみ
3. **1文字命令** - トークン効率最大化
4. **連番変数** - 意味のある名前は不要（v0, v1, g0, a0）
5. **明示的制御フロー** - ラベルとジャンプ

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
| `P` | `P result "func" args...` | Python FFI |

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

### Python FFI

```sui
; 数学関数
P g0 "math.sqrt" 16
. g0

; 乱数
P g1 "random.randint" 1 100
. g1

; 型変換
P g2 "int" "123"
+ g3 g2 1
. g3
```

**出力**: `4.0`、乱数、`124`

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
│   ├── args_demo.sui
│   └── ffi_demo.sui
└── prompts/
    ├── system_prompt.md  # LLM用システムプロンプト
    └── examples.md       # 生成例
```

## LLM連携

SuiはLLMによるコード生成のために設計されている。`prompts/` ディレクトリのプロンプトを使用：

1. `prompts/system_prompt.md` からシステムプロンプトをコピー
2. ChatGPT / Claude / Gemini 等に貼り付け
3. タスクを指定してSuiコードを生成させる
4. `sui your_code.sui` で実行

プロンプトテンプレートと期待される出力は [prompts/examples.md](prompts/examples.md) を参照。

## なぜSuiか

### 名前の由来

**粋（すい/いき）** - 日本語で「洗練されている」「無駄がない」という意味。余計なものを削ぎ落とし、本質だけを残す美意識を表す。

### LLMの弱点を回避

| LLMの弱点 | Suiの対策 |
|----------|-------------|
| 括弧の対応ミス | 括弧は `{}` のみ（関数定義） |
| 長距離依存 | 各行が独立 |
| 変数名のタイポ | 連番のみ（v0, v1...） |
| 複雑なネスト | ネスト禁止、一時変数に分解 |

### vs アセンブラ

| 観点 | アセンブラ | Sui |
|------|-----------|------|
| 命令数 | 数百〜数千 | ~20 |
| レジスタ | 8〜32個 | 無制限 |
| 関数呼び出し | 複雑（ABI） | 単純 |

### vs Python

| 観点 | Python | Sui |
|------|--------|------|
| トークン数 | 多い | 少ない |
| 構文の複雑さ | 高い | 低い |
| エラー検出 | 行単位困難 | 行単位可能 |

## 今後の改善案

- [x] トランスパイラ（Python出力）
- [x] トランスパイラ（Python入力、人間向け）
- [x] インタラクティブモード (REPL)
- [x] WebAssembly出力（WATトランスパイラ + ランタイム）
- [ ] トランスパイラ（JavaScript出力）
- [ ] 型注釈（オプション）
- [ ] LLVM IR出力

## ライセンス

MIT License


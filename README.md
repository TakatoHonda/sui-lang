# Sui (粋) - A Programming Language for LLMs

> Zero syntax errors. Zero typos. LLMs generate code that just works.

[日本語版 README](README_ja.md)

## Overview

**Sui (粋)** is a programming language named after the Japanese aesthetic concept meaning "refined" and "elimination of excess." It is designed so that LLMs can generate **100% accurate code** - not through hope, but through structural guarantees.

## Why Sui?

**Current LLM code generation problems:**
- Bracket mismatches `if (x { }` 
- Variable typos `coutn` vs `count`
- Indentation errors
- Complex nested expressions

**Sui makes these errors structurally impossible:**

| Problem | Sui's Solution |
|---------|----------------|
| Bracket mismatch | Only `{}` for functions, no nesting |
| Variable typos | Sequential numbers only (v0, v1, g0) - can't misspell |
| Indentation errors | Line-based, indentation is ignored |
| Complex nesting | One instruction per line, decompose to temps |

## Design Principles

1. **Zero Syntax Error Rate** - Structurally impossible to make syntax errors
2. **Zero Typo Rate** - Variables are numbers, not names
3. **Line Independence** - Each line is completely self-contained
4. **Pure Logic Language** - Computation only; UI delegated to any framework
5. **Future-Proof Efficiency** - As LLMs learn Sui, token efficiency will surpass traditional languages

## Installation

```bash
# PyPI (basic)
pip install sui-lang

# PyPI with WebAssembly support
pip install sui-lang[wasm]

# Homebrew (macOS/Linux)
brew tap TakatoHonda/sui
brew install sui-lang

# From source
git clone https://github.com/TakatoHonda/sui-lang.git
cd sui-lang
```

## Quick Start

### Interactive Mode (REPL)

```bash
# Start REPL
sui

# Example session
>>> = v0 10
>>> + v1 v0 5
>>> . v1
>>>
15
>>> .exit
```

Commands: `.exit` / `.quit` (exit), `.reset` (reset state)

### Interpreter

```bash
# Run file
sui examples/fibonacci.sui

# Run with arguments
sui examples/fib_args.sui 15

# Validate
sui --validate examples/fibonacci.sui

# Show help
sui --help
```

### Transpiler (Sui → Python)

```bash
# Show converted code
sui2py examples/fibonacci.sui

# Output to file
sui2py examples/fibonacci.sui -o fib.py

# Convert and execute
sui2py examples/fib_args.sui --run 15
```

### Transpiler (Python → Sui) for humans

```bash
# Show converted code
py2sui your_code.py

# Output to file
py2sui your_code.py -o output.sui
```

### WebAssembly

```bash
# Transpile to WebAssembly Text Format (WAT)
sui2wat examples/fibonacci.sui
sui2wat examples/fibonacci.sui -o fib.wat

# Execute directly via WebAssembly (requires: pip install sui-lang[wasm])
suiwasm examples/fibonacci.sui
```

### Browser UI

Sui is a **pure logic language**. UI can be implemented with any framework (React, Vue, Hono.js, vanilla JS, etc).

Sui compiles to Wasm with exports:
- `main()` - Initialization
- `f0()`, `f1()`, ... - Functions (callable from JS)
- `g0`, `g1`, ... - Global variables (read/write via `.value`)

```javascript
// Any framework works
const wasm = await WebAssembly.instantiate(wasmBytes, { env: { print_i32: console.log }});
button.onclick = () => { wasm.exports.f0(); display.textContent = wasm.exports.g0.value; };
```

### Running without Installation (from source)

```bash
# Using python directly
python sui.py examples/fibonacci.sui
python sui2py.py examples/fibonacci.sui
python py2sui.py your_code.py
```

## Syntax

### Instructions

| Instr | Format | Description |
|-------|--------|-------------|
| `=` | `= var value` | Assignment |
| `+` | `+ result a b` | Addition |
| `-` | `- result a b` | Subtraction |
| `*` | `* result a b` | Multiplication |
| `/` | `/ result a b` | Division |
| `%` | `% result a b` | Modulo |
| `<` | `< result a b` | Less than (0/1) |
| `>` | `> result a b` | Greater than (0/1) |
| `~` | `~ result a b` | Equality (0/1) |
| `!` | `! result a` | NOT |
| `&` | `& result a b` | AND |
| `\|` | `\| result a b` | OR |
| `?` | `? cond label` | Conditional jump |
| `@` | `@ label` | Unconditional jump |
| `:` | `: label` | Label definition |
| `#` | `# id argc {` | Function definition start |
| `}` | `}` | Function definition end |
| `$` | `$ result func args...` | Function call |
| `^` | `^ value` | Return |
| `[` | `[ var size` | Array create |
| `]` | `] result arr idx` | Array read |
| `{` | `{ arr idx value` | Array write |
| `.` | `. value` | Output |
| `,` | `, var` | Input |

### Variables

| Format | Meaning |
|--------|---------|
| `v0`, `v1`, ... | Local variables |
| `g0`, `g1`, ... | Global variables |
| `a0`, `a1`, ... | Function arguments |
| `g100` | argc (command-line argument count) |
| `g101`, `g102`, ... | argv (command-line arguments) |

## Examples

### Fibonacci

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

**Output**: `55`

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

## File Structure

```
sui/
├── README.md           # This file (English)
├── README_ja.md        # Japanese README
├── LICENSE             # MIT License
├── sui.py              # Interpreter
├── sui2py.py           # Sui → Python transpiler
├── sui2wat.py          # Sui → WebAssembly Text Format transpiler
├── suiwasm.py          # WebAssembly runtime (execute via wasmtime)
├── py2sui.py           # Python → Sui transpiler (for humans)
├── examples/
│   ├── fibonacci.sui
│   ├── fib_args.sui
│   ├── fizzbuzz.sui
│   ├── list_sum.sui
│   └── args_demo.sui
└── prompts/
    ├── system_prompt_en.md  # LLM system prompt (English)
    ├── system_prompt_ja.md  # LLM system prompt (Japanese)
    └── examples.md          # Application examples (Sui + UI)
```

## LLM Integration

Sui is designed for LLM code generation. Use the prompts in `prompts/` directory:

1. Copy the system prompt from `prompts/system_prompt_en.md`
2. Paste it into ChatGPT / Claude / Gemini / etc.
3. Ask to generate Sui code for your task
4. Run with `sui your_code.sui`

See [prompts/examples.md](prompts/examples.md) for prompt templates and expected outputs.

## Name Origin

**Sui (粋)** - A Japanese word meaning "refined," "sophisticated," or "the essence." It represents the aesthetic of eliminating excess and keeping only what is essential.

## Token Efficiency: Now vs Future

**Current state** (LLMs don't know Sui yet):
| Language | Fibonacci | Counter |
|----------|-----------|---------|
| Sui | 79 tokens | 44 tokens |
| Python | 30 tokens | 30 tokens |

**Future state** (after LLMs learn Sui):
- `v0`, `g0` → 1 token each (currently 2)
- Patterns like `+ g0 g0 1` → compressed
- Estimated: **40-50% reduction**

**But token count isn't the point.** The real value:
- **0% syntax error rate** (vs ~5-10% for Python/JS)
- **0% typo rate** (variables can't be misspelled)
- **100% parseable output** (every line is valid or clearly invalid)

## vs Other Languages

### vs Python/JavaScript

| Aspect | Python/JS | Sui |
|--------|-----------|-----|
| Syntax errors | Common | Impossible |
| Variable typos | Common | Impossible |
| Bracket matching | Error-prone | Trivial |
| Token efficiency (now) | Better | Worse |
| Token efficiency (future) | Same | Better |

### vs Assembly

| Aspect | Assembly | Sui |
|--------|----------|-----|
| Instructions | Hundreds | ~20 |
| Registers | 8-32 | Unlimited |
| Learning curve | Steep | Minimal |

## Roadmap

- [x] Interpreter (Python)
- [x] Transpiler (Sui → Python)
- [x] Transpiler (Python → Sui, for humans)
- [x] Interactive mode (REPL)
- [x] WebAssembly output (WAT + runtime)
- [ ] Type annotations (optional)
- [ ] LLVM IR output

## License

MIT License

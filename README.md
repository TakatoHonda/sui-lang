# Sui (粋) - A Programming Language for LLMs

> A line-based programming language optimized for accurate LLM code generation

[日本語版 README](README_ja.md)

## Overview

**Sui (粋)** is a programming language named after the Japanese aesthetic concept meaning "refined" and "elimination of excess." It is designed with LLM (Large Language Model) code generation accuracy as the top priority.

## Design Principles

1. **Line Independence** - Each line is completely self-contained
2. **Minimal Bracket Matching** - Nesting only for function blocks `{}`
3. **Single-Character Instructions** - Maximum token efficiency
4. **Sequential Variables** - No meaningful names needed (v0, v1, g0, a0)
5. **Explicit Control Flow** - Labels and jumps

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
| `P` | `P result "func" args...` | Python FFI |

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

### Python FFI

```sui
; Math functions
P g0 "math.sqrt" 16
. g0

; Random number
P g1 "random.randint" 1 100
. g1

; Type conversion
P g2 "int" "123"
+ g3 g2 1
. g3
```

**Output**: `4.0`, random number, `124`

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
│   ├── args_demo.sui
│   └── ffi_demo.sui
└── prompts/
    ├── system_prompt.md  # LLM system prompts
    └── examples.md       # Generation examples
```

## LLM Integration

Sui is designed for LLM code generation. Use the prompts in `prompts/` directory:

1. Copy the system prompt from `prompts/system_prompt.md`
2. Paste it into ChatGPT / Claude / Gemini / etc.
3. Ask to generate Sui code for your task
4. Run with `sui your_code.sui`

See [prompts/examples.md](prompts/examples.md) for prompt templates and expected outputs.

## Why Sui?

### Name Origin

**Sui (粋)** - A Japanese word meaning "refined," "sophisticated," or "the essence." It represents the aesthetic of eliminating excess and keeping only what is essential.

### Avoiding LLM Weaknesses

| LLM Weakness | Sui's Solution |
|--------------|----------------|
| Bracket mismatch | Only `{}` for functions |
| Long-range dependencies | Each line is independent |
| Variable name typos | Only sequential numbers (v0, v1...) |
| Complex nesting | No nesting, decompose to temp variables |

### vs Assembly

| Aspect | Assembly | Sui |
|--------|----------|-----|
| Instruction count | Hundreds to thousands | ~20 |
| Registers | 8-32 | Unlimited |
| Function calls | Complex (ABI) | Simple |

### vs Python

| Aspect | Python | Sui |
|--------|--------|-----|
| Token count | High | Low |
| Syntax complexity | High | Low |
| Line-by-line errors | Hard | Easy |

## Roadmap

- [x] Transpiler (Python output)
- [x] Transpiler (Python input, for humans)
- [x] Interactive mode (REPL)
- [x] WebAssembly output (WAT transpiler + runtime)
- [ ] Transpiler (JavaScript output)
- [ ] Type annotations (optional)
- [ ] LLVM IR output

## License

MIT License

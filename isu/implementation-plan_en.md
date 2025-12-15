# Isu Implementation Plan

## Goals

- The LLM generates **Isu (structured pseudocode)** from human natural-language instructions.
- Isu is **parsed deterministically** into **S-IR (AST)**.
- S-IR is compiled to **any execution target** (prioritize existing foundations such as Python / Wasm / LLVM IR first).
- On failure, roll back to Isu and run a **repair loop** (everything after IR is deterministic in principle).

---

## Overall Architecture

```text
[User NL]
   |
   v
[LLM] --(Isu text)--> [Parser] --(S-IR JSON AST)--> [Compiler] --> [Backend Runtime]
   ^                          |                              |
   |                          v                              v
   +------(errors/spec)--- [Validator] ------------------ [Test/Trace]
```

### Layer responsibilities

- **Isu (text)**: the primary artifact that the LLM reads/writes
- **S-IR (JSON AST)**: a deterministic internal representation that corresponds 1:1 with Isu
- **Backend**: Python / Wasm / LLVM IR, etc. Consider a dedicated VM only if needed later.

---

## Core principles of the specification

### 1. Determinism

- Isu → S-IR must be uniquely determined.
- Eliminate ambiguity in grammar, lexing, scoping, and type inference.
- Where ambiguity is needed, **require explicit syntax** (e.g., make `ELSE:` mandatory).

### 2. Minimal control constructs

- `SEQ` / `IF` / `LOOP` / `ASSIGN` / `RETURN`
- Everything else should be expressed as metadata where possible (e.g., `BREAK` can be modeled via loop attributes or by `IF + RETURN`).

### 3. Closed vocabulary

- `kind` must be a finite set (extensions should be cautious).
- Standard functions (e.g., `LEN`, `MAP_HAS`, `SPLIT_WHITESPACE`) are fixed as a **small standard set**.
- Avoid explosion of arbitrary user-defined function names or arbitrary API names.

### 4. Grammar designed for LLM generation

- Fixed line-leading keywords
- **Indentation is not semantic** (formatting only)
- Block boundaries are determined by **explicit tokens** (`BEGIN` / `END`)
- Step IDs are required in canonical form (`S1`, `S2_1`, …), but input may omit them via `AUTO_ID` (see below)

---

## LLM-friendly specification (generation robustness principles)

Absorb typical generation failure modes (missing block terminators, key-name variance, Step ID duplication/gaps, parenthesis errors in expressions) at the spec level.

### Principles

- Fix a single **canonical form**, and always “canonicalize” before processing.
- Make input slightly permissive, but make output strict (LLM produces input; compiler returns canonical form).
- Do not introduce synonyms with the same meaning (e.g., disallow `TARGET/DEST`).
- Fix field ordering per node to make missing/extra keys easier to detect.

### Mechanisms to reduce generation errors (include from v0)

- **AUTO_ID**
  - Allow omission of Step IDs when generating (`AUTO_ID: true`).
  - Canonicalization assigns stable `S1,S2,...`; subsequent errors/patches refer to these IDs.
- **Block shorthand**
  - Canonical form is `BEGIN/END`, but input may use `THEN: { ... }` / `ELSE: { ... }` / `BODY: { ... }`.
  - `{}` reduces missing-end errors and stabilizes generation.
- **Fixed field order**
  - `IF`: `COND` → `THEN` → `ELSE`
  - `LOOP`: `ITER` → `BODY`
  - `ASSIGN`: `TARGET` → `EXPR`
  - `RETURN`: `EXPR`

## v0: hard decisions (most important)

### Block syntax (indentation-independent)

YAML-like indentation is error-prone and ambiguous, so do not adopt it. v0 specifies:

- Block start: `BEGIN`
- Block end: `END`
- `THEN` / `ELSE` / `BODY` must **always** include a `BEGIN`
- Blank lines are allowed (ignored by lexer)
- Comment lines are allowed (a line starting with `;` is ignored)

### Block shorthand (input-only)

- Input may use `THEN: { ... }` / `ELSE: { ... }` / `BODY: { ... }`.
- Canonicalization always expands `{}` into `BEGIN/END`; internal processing only handles `BEGIN/END`.

Example:

```text
S2: IF
  COND: (lt (var i) (call LEN (var xs)))
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

## Phased implementation plan

## Phase 0: Minimum executable pipeline (MVP)

### 0.1 Minimum Isu spec (v0)

Required sections:

- `FUNC`
- `IO`
- `STATE`
- `LOCAL`
- `STEPS`

`LOCAL` declares temporary variables within a function; do not introduce block scope (function scope only).

Optional helper section:

- `META`
  - `AUTO_ID: true|false` (if true, Step ID omission is allowed and stable IDs are assigned during canonicalization)

Required nodes:

- `SEQ`
- `ASSIGN`
- `IF`
- `LOOP`
- `RETURN`

Minimum expression DSL:

In v0, drop infix-string expressions and use a deterministic **prefix (S-expression)** form.

- Constants: `(const 1)`, `(const "x")`, `(const true)`
- Variables: `(var name)`
- Binary ops: `(add a b)`, `(sub a b)`, `(mul a b)`, `(div a b)`, `(mod a b)`
- Comparisons: `(eq a b)`, `(ne a b)`, `(lt a b)`, `(le a b)`, `(gt a b)`, `(ge a b)`
- Indexing: `(index a i)`
- Function calls (v0: standard functions only): `(call FN arg1 arg2 ...)`
  - `FN` is restricted to standard function names to keep a closed vocabulary
  - Examples: `(call LEN (var xs))`, `(call MAP_GET (var m) (var k))`

Notes:

- Remove precedence/associativity/escaping pitfalls from v0.
- Human readability is handled by the pretty-printer.
- Do not introduce a separate `CALL` statement in v0; unify calls inside expressions to remove variance.

### 0.2 Parser

- Build an **official grammar** using PEG or Lark/ANTLR, and manage it in a form usable for both:
  - Parsing (Isu → S-IR)
  - Constraining LLM output later (grammar-constrained decoding)

Output:

- Always produce `S-IR (JSON)`.
- Pretty-print the IR back to Isu (round-trip formatting) from the beginning.
- Always run **canonicalization** after parsing; all subsequent processing targets canonical form only:
  - Expand `{}` blocks into `BEGIN/END`
  - Assign stable Step IDs when `AUTO_ID` is true
  - Normalize field order and required keys

### 0.3 Validator (static checks)

- Step ID uniqueness
- Existence of referenced Step IDs
- Declared-variable checks (no variables outside `STATE` + `IO` + `LOCAL`)
- Basic type consistency (initially weak is OK; at least reject `int`/`string` mixing)
- `RETURN` type matches the function signature

### 0.4 Backend (interpreter first, then Python)

- Implement an **S-IR interpreter** in v0; prioritize correct execution and tracing.
- Map runtime exceptions back to Isu Step IDs (critical).
- Introduce Python backend (AST generation or source generation) after v0 as needed.

### 0.5 Patch application (build the repair loop core early)

Before Phase 1, implement a minimal patch applier in v0.

- Support only `REPLACE <StepID>:`.
- Apply patches **after converting to S-IR** (more deterministic and less fragile than text editing).
- Allow Isu fragments as patch bodies; parse only the fragment, canonicalize to S-IR, then replace the target step.
- After replacement, always run the pretty-printer so canonical Isu can be returned.
- Re-run validator after applying patches.

---

## Phase 1: Error feedback and repair loop

### 1.1 Error model

Always return structured errors:

- `ParseError` (Isu grammar violation)
- `StaticError` (undeclared variables, type mismatch, missing step reference)
- `RuntimeError` (division by zero, out-of-range indexing, missing key, etc.)
- `TestFail` (mismatch against IO examples)

### 1.2 Step-level feedback

Feedback to the LLM is step-ID based.

Examples:

- `S2_1` has a condition that is always false
- `S3_2` updates `v_best` under the wrong condition
- `S4` should return `int`

### 1.3 Iterative generation strategy

- First pass: LLM generates the entire Isu
- Subsequent passes: LLM regenerates only target steps (patch format)

Patch example:

```text
PATCH:
  REPLACE S2_1:
    S2_1: IF "..."
      COND: ...
      THEN: BEGIN
        ...
      END
```

Patch application is deterministic on the compiler side.

---

## Phase 2: Standard library and closed-vocabulary expansion

### 2.1 Standard functions (examples)

- Arrays: `LEN`, `PUSH`, `POP`, `SLICE`
- Maps: `MAP_HAS`, `MAP_GET`, `MAP_SET`
- Strings: `SPLIT_WHITESPACE`, `JOIN`, `LOWER`
- Math: `ABS`, `MIN`, `MAX`

Principles:

- Do not add multiple APIs for the same meaning.
- Standardize shapes (argument order, return values).

### 2.2 Gradual type-system strengthening

- v1: `int`, `bool`, `string`, `T[]`, `map<K,V>`
- v2: `struct` (fixed fields only)
- v3: references/ownership if needed

---

## Phase 3: Target expansion

### 3.1 Wasm

- Compile S-IR → Wasm (WAT or binary)
- Start with an integer/array/loop-centric subset

### 3.2 LLVM IR

- Generate LLVM IR from S-IR
- SSA conversion happens in the compiler (Isu does not require SSA)

---

## Proposed directory layout

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

## Spec decisions to lock early

1. **Indentation rules**
   - v0 is indentation-independent (formatting only)
   - tabs disallowed (stable formatting)
   - blocks are delimited by `BEGIN/END`

2. **Step ID format**
   - allow `S` + digits + `_` + digits…
   - sorting rules that match structural order (debuggability)
   - whether to allow `AUTO_ID` (if yes, canonicalize and refer to assigned IDs thereafter)

3. **Expression DSL grammar**
   - v0 uses prefix S-expressions (removes precedence ambiguity)
   - function calls: standard functions only

4. **Scope**
   - function scope only (no block scope)
   - loop variables are declared in `LOCAL`; `ITER` refers to the assignment target name

5. **Eliminate undefined behavior**
   - out-of-range access always raises
   - `MAP_GET` raises if key is missing (or introduce `MAP_GET_OR`)

---

## LLM integration approach

### Output constraints

- Start with minimal regex constraints
- Then introduce grammar-constrained decoding using EBNF/PEG
- Keep JSON Schema direct S-IR generation as an option (but Isu remains primary)

### Prompt policy (high-level)

- Enforce `FUNC/IO/STATE/LOCAL/STEPS` order
- If using `META`, place it at the beginning (e.g., `META: AUTO_ID: true`)
- Require Step IDs (unless `AUTO_ID: true`)
- Do not omit `COND`, `ITER`, `THEN`, `ELSE`, `BODY`
- Always wrap `THEN/ELSE/BODY` with `BEGIN/END`
  - if `{}` is allowed, recommend `{}` for generation and canonicalize to `BEGIN/END`
- In v0, unify function calls as `(call FN ...)` (FN must be a standard function)

Minimum template (for generation):

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

## Related approaches and comparisons (positioning of Isu)

Isu is designed to take LLM output into a deterministically executable intermediate language. Many neighboring techniques exist; some are substitutes, others are complementary.

### 1) JSON Schema / Function Calling / Structured Outputs

- **Summary**: force LLM outputs to match a JSON schema; close to direct S-IR generation.
- **Strength**: greatly reduces unparsable outputs; validation becomes simpler.
- **Isu advantage**:
  - easier to keep a human-reviewable primary artifact
  - step-level patch workflow is natural
- **When Isu is less advantageous**:
  - if a human-readable intermediate artifact is unnecessary, direct S-IR (JSON) generation can be simpler

### 2) Grammar-constrained decoding (EBNF/CFG)

- **Summary**: mask tokens during decoding so invalid strings cannot be generated.
- **Strength**: if Isu is adopted, this alone can drastically reduce `ParseError`.
- **Relationship to Isu**: complementary (close to essential) for making deterministic parsing practical.

### 3) SCoT (Structured Chain-of-Thought)

- **Summary**: a prompting technique that structures intermediate reasoning into code-like constructs (sequence/branch/loop).
- **Strength**: reported improvements in code-generation pass@1.
- **Isu advantage**:
  - SCoT is a prompt tactic; semantics/execution are not guaranteed by itself
  - Isu is a framework including spec, parser, validator, and trace for reproducible operation/debugging
- **Conclusion**: use SCoT as a prompt design to generate Isu; not a direct competitor.

### 4) ReAct / Reflexion

- **Summary**: interleave reasoning and actions; use external tools/environment feedback.
- **Strength**: good for exploration and information gathering.
- **Isu advantage**: easier to ensure reproducibility via a deterministic pipeline.
- **Conclusion**: combine as an outer control loop for Isu generation/repair.

### 5) PAL / direct code generation + execution

- **Summary**: let the model generate programs (e.g., Python) and execute them in an interpreter.
- **Strength**: fast to bootstrap; reuse existing runtimes/libraries.
- **Isu advantage**:
  - target-agnostic (avoid Python lock-in; extend to Wasm/LLVM)
  - step IDs and validator can be designed in to localize runtime errors

### 6) ToT / Self-Consistency

- **Summary**:
  - ToT: explore multiple branches of reasoning and prune with evaluation
  - Self-Consistency: sample multiple solutions and pick by consistency/majority
- **Relationship to Isu**:
  - generate multiple Isu candidates, score with validator/tests, and select
  - `AUTO_ID` + canonicalization stabilizes comparison/diff workflows

### 7) DSPy

- **Summary**: optimize prompts using evaluation signals rather than manual prompt engineering.
- **Relationship to Isu**: optimize the “Isu generator” using validator/tests as supervision.

References:

- SCoT (code generation): https://arxiv.org/abs/2305.06599
- ReAct: https://arxiv.org/abs/2210.03629
- PAL: https://arxiv.org/abs/2211.10435
- ToT: https://arxiv.org/abs/2305.10601
- Self-Consistency: https://arxiv.org/abs/2203.11171
- Reflexion: https://arxiv.org/abs/2303.11366
- Structured Outputs (OpenAI): https://openai.com/index/introducing-structured-outputs-in-the-api/
- LMQL constraints: https://lmql.ai/docs/language/constraints.html
- Outlines CFG: https://dottxt-ai.github.io/outlines/latest/reference/generation/cfg/
- Guidance: https://github.com/guidance-ai/guidance
- DSPy: https://github.com/stanfordnlp/dspy

## Test strategy

### 1. Golden tests

- Isu → S-IR → Isu (pretty-print) round-trip equivalence
- Isu → execution (v0: interpreter) expected outputs

### 2. Property tests

- Generate random S-IR, lower to Isu, re-parse, and check equivalence
- Verify correct exceptions for loop bounds and out-of-range indexing

### 3. Round-trip evaluation (future)

- Isu → NL summary → Isu to measure meaning preservation

---

## Success metrics (measure early)

- **Determinism**: identical input Isu always yields identical S-IR (byte-level serialized equality)
- **Trace alignment**: most runtime errors can be pinpointed via “Step ID + variable name + type/value”
- **Repair efficiency**: continuously measure how often 1–2 patches make tests pass; if it degrades, revisit spec/validator/stdlib

## Most important points in this approach

- **The LLM only touches Isu**
- **Isu → S-IR is 100% deterministic**
- **S-IR → executable code is also deterministic**
- On failure, **return to the Isu level and repair**
- Enforce “closed vocabulary” and “minimal structure” to avoid giving the model excessive freedom

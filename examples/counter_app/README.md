# Counter App Example

A simple counter application demonstrating Sui + WebAssembly + HTML/JS integration.

## Quick Start

**⚠️ Note: Opening `index.html` directly (`file://`) won't work due to CORS restrictions. You must use a local server.**

```bash
# 1. Navigate to this directory
cd examples/counter_app

# 2. Start local server
python -m http.server 8080

# 3. Open in browser
open http://localhost:8080
```

The `logic.wasm` is pre-compiled and included. No build step required.

## Files

| File | Description |
|------|-------------|
| `logic.sui` | Sui source code |
| `logic.wasm` | Compiled WebAssembly (included) |
| `index.html` | UI (vanilla JS) |

## Rebuild (Optional)

If you modify `logic.sui`, recompile:

```bash
sui2wasm logic.sui -o logic.wasm
```

Requires: `brew install wabt`

## Architecture

```
┌─────────────────┐     ┌─────────────────┐
│   index.html    │────▶│   logic.wasm    │
│   (UI Layer)    │     │   (Sui Logic)   │
└─────────────────┘     └─────────────────┘
        │                       │
        │   f0() increment      │
        │   f1() decrement      │
        │   f2() reset          │
        │   g0   state          │
        └───────────────────────┘
```

## Wasm Exports

| Export | Type | Description |
|--------|------|-------------|
| `g0` | Global | Counter state (read via `.value`) |
| `f0()` | Function | Increment counter |
| `f1()` | Function | Decrement counter |
| `f2()` | Function | Reset to 0 |
| `main()` | Function | Initialize |

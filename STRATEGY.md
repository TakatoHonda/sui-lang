# Sui Strategic Roadmap

> Goal: Make Sui the de facto standard for LLM code generation

## Current Status

| Area | Status | Evaluation |
|------|--------|------------|
| Language Design | High completeness | ✅ |
| Runtime | Python + Wasm | ✅ |
| Documentation | Basic only | ⚠️ |
| Ecosystem | None | ❌ |
| LLM Integration | Prompts only | ⚠️ |
| Awareness | Near zero | ❌ |

## Strategic Actions

### Priority 1: Benchmark Paper (Academic Proof)

**Goal**: Scientifically prove "LLMs can write Sui with 100% accuracy"

- [ ] Create `sui-bench` benchmark suite
- [ ] Compare Sui vs Python vs JavaScript
- [ ] Measure: syntax error rate, execution success rate, token efficiency
- [ ] Expected metrics:

| Metric | Sui | Python | JS |
|--------|-----|--------|-----|
| Syntax Error Rate | 0% | ~12% | ~15% |
| Execution Success | 100% | ~78% | ~72% |

**Target Venues:**

| Category | Conference | Tier | Focus |
|----------|------------|------|-------|
| **PL** | PLDI | A* | Language design, implementation |
| | POPL | A* | PL theory, semantics |
| | OOPSLA | A* | OOP, language systems |
| **AI/ML** | NeurIPS | A* | Machine learning |
| | ICML | A* | Machine learning |
| | ICLR | A* | Deep learning, representations |
| | AAAI | A* | Artificial intelligence |
| **NLP** | ACL | A* | Computational linguistics |
| | EMNLP | A | NLP methods |
| | NAACL | A | NLP (North America) |
| **SE** | ICSE | A* | Software engineering |
| | FSE | A* | Software engineering foundations |
| | ASE | A | Automated SE |

**Paper Angles:**
- PL venues: "A syntax designed for LLM generation"
- AI/ML venues: "Improving code generation accuracy via language design"
- SE venues: "Human-AI collaboration in programming"

### Priority 2: VSCode Extension (Developer Experience)

**Goal**: Lower adoption barrier for developers

- [ ] Syntax highlighting
- [ ] Code snippets
- [ ] Error diagnostics
- [ ] LSP (Language Server Protocol) implementation
- [ ] Cursor AI prompt optimization

### Priority 3: LLM Provider Outreach

**Goal**: Get Sui into LLM training data / system prompts

| Provider | Action | Status |
|----------|--------|--------|
| Anthropic | Direct contact, propose collaboration | ⬜ |
| OpenAI | Create Custom GPT for Sui | ⬜ |
| Google | DeepMind outreach | ⬜ |
| Hugging Face | Publish Sui dataset | ⬜ |

### Priority 4: Killer Application

**Goal**: Prove practical utility

Candidates:
- [ ] AI Agent logic description standard
- [ ] Smart contract logic layer
- [ ] Educational programming language
- [ ] Scientific computing (with math extensions)

### Priority 5: Standard Packages (#8, #9)

**Goal**: Provide common functionality via packages (not built-in)

- [ ] Package manager implementation (#9)
- [ ] `sui-math` package: matrix, statistics (#8)
- [ ] `sui-crypto` package: hash, encryption
- [ ] `sui-algo` package: sort, search, graph

See [Issue #8](https://github.com/TakatoHonda/sui-lang/issues/8) and [Issue #9](https://github.com/TakatoHonda/sui-lang/issues/9)

## Ecosystem Development

### Package Manager (#9)

**Design**: Hash-based package IDs (zero identifiers)

```
Package ID = hash(package_name)[:48bit]  → 281 trillion unique IDs
Function ID = sequential within package  → 65,536 per package
```

**Example:**
```sui
; X <pkg_id> <func_id> <result> <args...>
X 182947362847591 0 v2 v0 v1   ; sui-math:matmul
X 56284719384756 0 v3 v0       ; sui-crypto:sha256
```

**Collision Analysis** (Birthday Paradox):

| Packages | 32bit | 48bit | 64bit |
|----------|-------|-------|-------|
| 614K (PyPI現在) | 100% | 0.07% | ~0% |
| 3M (5倍成長) | 100% | 1.6% | ~0% |
| 6M (10倍成長) | 100% | 6.2% | ~0% |

**Recommendation**: 48bit minimum, 64bit for future-proofing

**Key Features:**
- Deterministic: same name → same ID (globally)
- Distributed: no central authority for ID assignment
- Collision handling: registry + salt on conflict

See [Issue #9](https://github.com/TakatoHonda/sui-lang/issues/9)

### Standard Library

| Module | Operations |
|--------|------------|
| Math | Matrix, vector, statistics |
| String | (TBD - may require identifiers) |
| Crypto | Hash, encrypt/decrypt |

## Marketing & Awareness

- [ ] Twitter/X presence
- [ ] Blog posts explaining philosophy
- [ ] Conference talks (PyCon, JSConf, etc.)
- [ ] YouTube tutorials
- [ ] Collaboration with AI influencers

## Timeline (Proposed)

| Quarter | Focus |
|---------|-------|
| Q1 2025 | Benchmark paper, VSCode extension |
| Q2 2025 | LLM provider outreach, killer app prototype |
| Q3 2025 | Package manager (#9), standard packages (#8) |
| Q4 2025 | Rust implementation (#10), community building |

### Rust Implementation (#10)

**Goal**: Production-quality compiler with single-binary distribution

- [ ] Core library (lexer, parser, interpreter)
- [ ] Wasm codegen (native, no wabt dependency)
- [ ] Python bindings (PyO3) for backward compatibility
- [ ] Browser compiler (wasm-pack) for Playground

See [Issue #10](https://github.com/TakatoHonda/sui-lang/issues/10)

## Success Metrics

| Metric | Target (1 year) |
|--------|-----------------|
| GitHub Stars | 1,000+ |
| PyPI Downloads/month | 10,000+ |
| Academic Citations | 10+ |
| LLM native support | 1+ provider |

## Core Philosophy (Never Compromise)

1. **Zero syntax errors** - Structural guarantee
2. **Zero typos** - Variables are numbers only
3. **One instruction per line** - Line independence
4. **Pure logic** - UI/IO delegated to external frameworks
5. **No identifiers** - All operations use numeric IDs

---

*"Sui is the sanctuary of logic. The dirty outside world is left to existing languages."*


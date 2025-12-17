# Isu - 为大语言模型设计的结构化伪代码（Sui项目）

本仓库正在将主要关注点从原始的基于行的 **Sui** 语言转向 **Isu**，一种为确定性解析和步骤级修复循环设计的结构化伪代码。

[English README](README.md) [日本語版 README](README_ja.md)

## 项目状态

- **Isu（新）**：实现为最小化v0管道（`isu/`）— Isu文本 ⇄ **IIR**（JSON兼容AST）⇄ 规范化Isu。
- **Sui（已弃用）**：已移至 `sui_legacy/` 目录，并通过兼容性包装器保持维护（`sui.py`、`sui2py.py` 等）。

## Isu 是什么？

Isu 是大语言模型**主要读写的工件**。它被确定性地解析为 **IIR（Isu中间表示）**，一种闭合词汇表AST，设计用于：

- 确定性解析和规范化（`AUTO_ID`、固定形状）
- 步骤级错误定位和修补工作流
- 后端独立性（计划支持Python/Wasm/LLVM IR；尚未实现）

设计文档：

- `isu/implementation-plan_en.md`
- `isu/implementation-plan_ja.md`

## 快速开始（源码运行）

Isu 目前是一个仓库本地的Python包。请从仓库根目录运行：

```bash
python -c 'from isu import parse_isu, pretty_print_isu; \
src = """META:\n  AUTO_ID: true\nFUNC:\n  NAME: f\nIO:\n  INPUT: []\n  OUTPUT: []\nSTATE:\n  []\nLOCAL:\n  []\nSTEPS:\n  SEQ:  BEGIN\n    ASSIGN:\n      TARGET: x\n      EXPR:  (const 1)\n    RETURN:\n [...]
p = parse_isu(src); print(pretty_print_isu(p))'
```

## 仓库结构（高层概览）

```text
isu/          # Isu v0 管道（解析器/规范化器/美化打印器/验证器）
tests/        # pytest（包括Isu v0往返测试）
sui_legacy/   # 已弃用的Sui实现（解释器/转译器/wasm工具）
sui.py        # 兼容性包装器 -> sui_legacy.sui
```

## 已弃用的Sui（暂时保留）

原始Sui语言/工具仍然可用：

- 游乐场：`playground/index.html`
- 示例：`examples/`
- 工具：`sui.py`、`sui2py.py`、`py2sui.py`、`sui2wasm.py`、`suiwasm.py`（包装器）

它被明确标记为**已弃用**，新的工作应该面向 **Isu/IIR**。

## 许可证

MIT License

# event-chain-decision

> Agent-driven, evidence-grounded decision framework for market event chains
> (IPO / M&A / catalyst chains). Scripts compute facts; the agent decides what
> they mean and whether any trade is executable — FREEZE / WATCH / ACT / RETIRE.

[English](#english) | [中文](#中文)

## English

### What it is
A runtime-agnostic protocol an agent uses to turn live market snapshots into a
disciplined decision instead of mechanically firing on script triggers. The core
is domain-agnostic; the SPCX / aerospace chain ships as a sanitized reference
implementation under `examples/spcx-chain/`.

### Core ideas
- **Data / judgment separation** — Python computes numbers and freshness; the
  agent judges regime, causality, and trust. See `PRINCIPLES.md`.
- **Time-anchored freshness gate** — action-critical realtime data older than one
  trading day blocks ACT, enforced by the validator.
- **Four-lens assessment + opponent model** — structure, macro, narrative, market;
  always ask who is on the other side. See `docs/decision-protocol.md`.
- **Deterministic position sizing** — `ecd.position_sizing`, never prose.

### Layout
- `src/ecd/` — stdlib-only framework helpers (freshness, position sizing, generic
  envelope).
- `docs/` — generic protocol, schema, and sizing docs.
- `examples/spcx-chain/` — a complete, installable Claude Code skill built on the
  framework (sanitized).

### Quick start
```bash
pip install -e .
python examples/spcx-chain/scripts/spcx_decision_pack.py template --out reports/pack.json
python examples/spcx-chain/scripts/spcx_decision_pack.py validate --input reports/pack.json
python -m pytest -q
```

### Fork your own chain
1. Copy `examples/spcx-chain/` to `examples/<your-chain>/`.
2. Replace the domain fields in the template and the chain validator.
3. Reuse `ecd.freshness.check_block_freshness` for action-critical staleness.
4. Keep domain fields out of `src/ecd/` — that layer stays generic.

### License
MIT.

## 中文

### 这是什么
一套与运行时无关的决策协议:让 agent 把实时市场快照转化为有纪律的决策
(FREEZE / WATCH / ACT / RETIRE),而不是机械地按脚本触发器下单。核心层与领域无关;
SPCX / 航天链作为脱敏后的参考实现放在 `examples/spcx-chain/`。

### 核心理念
- **数据-判断分离** —— Python 算数字和新鲜度,agent 判断 regime/因果/可信度。见 `PRINCIPLES.md`。
- **时间锚定的新鲜度闸门** —— 行动关键的实时数据超过 1 个交易日即阻断 ACT,由校验器强制执行。
- **四镜头评估 + 对手方模型** —— 结构/宏观/叙事/市场,永远先问"谁在你对面"。见 `docs/decision-protocol.md`。
- **确定性仓位** —— 由 `ecd.position_sizing` 计算,绝不用散文拍脑袋。

### 目录
- `src/ecd/` —— 纯标准库的框架工具(新鲜度、仓位、通用信封)。
- `docs/` —— 通用协议/schema/仓位文档。
- `examples/spcx-chain/` —— 基于框架、脱敏后的完整可安装 Claude Code skill。

### 快速上手
见上方 English 的 Quick start。

### 派生你自己的链
复制 `examples/spcx-chain/` 为 `examples/<your-chain>/`,替换领域字段,复用
`ecd.freshness`,通用层 `src/ecd/` 保持领域无关。

### 许可证
MIT。

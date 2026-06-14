# spcx-chain-dynamic-decision

> Dynamic, evidence-grounded decision protocol for the SpaceX (SPCX) IPO event chain —
> and any super-IPO / M&A / catalyst chain. Scripts compute facts; the agent decides
> what they mean and whether any trade is executable: FREEZE / WATCH / ACT / RETIRE.

[English](#english) | [中文](#中文)

## English

### What it is
A runtime-agnostic skill (Claude Code, Codex, OpenClaw, ...) that turns daily SPCX-chain
market snapshots into a disciplined decision instead of mechanically firing on script
triggers. It treats the prior research report as a hypothesis to update from current
evidence, not a target to fit. The SPCX / aerospace chain is the shipped reference
implementation; the underlying engine is generic, so you can fork it for any super-IPO
(OpenAI, Anthropic, xAI, Stripe, Databricks, ...).

### Core ideas
- **Data / judgment separation** -- Python computes numbers and freshness; the agent
  judges regime, causality, and trust. See `PRINCIPLES.md`.
- **Time-anchored freshness gate** -- action-critical realtime data older than one
  trading day blocks ACT, enforced by the validator.
- **Four-lens assessment + opponent model** -- structure, macro, narrative, market;
  always ask who is on the other side. See `docs/decision-protocol.md`.
- **Six regimes** -- mechanical_bid / macro_shock / narrative_drain / narrative_migration
  / data_collision / no_edge.
- **Deterministic position sizing** -- `ecd.position_sizing`, never prose.

### Layout
- `examples/spcx-chain/` -- the SPCX reference skill (SKILL.md + references + validator),
  installable as a Claude Code skill.
- `src/ecd/` -- stdlib-only generic engine (freshness, position sizing, generic envelope).
- `docs/` -- generic protocol, schema, and sizing docs.

### Quick start
```bash
pip install -e .
python examples/spcx-chain/scripts/spcx_decision_pack.py template --out reports/pack.json
python examples/spcx-chain/scripts/spcx_decision_pack.py validate --input reports/pack.json
python -m pytest -q
```
(The `reports/` directory is created automatically and is gitignored.)

### Use it in your agent
- **Claude Code**: `/loop` each trading day after US close -> daily decision brief.
- **OpenClaw / Codex / others**: run collectors -> `validate` the evidence pack -> prompt
  the agent with `examples/spcx-chain/SKILL.md` + the pack. See
  `examples/spcx-chain/references/runtime-integration.md`. The agent never places orders.

### Fork your own chain
1. Copy `examples/spcx-chain/` to `examples/<your-chain>/`.
2. Replace the domain fields in the template and the chain validator.
3. Reuse `ecd.freshness.check_block_freshness` for action-critical staleness.
4. Keep domain fields out of `src/ecd/` -- that layer stays generic.

### License
MIT.

## 中文

### 这是什么
一个与运行时无关的 skill(Claude Code / Codex / OpenClaw 等):把每日 SPCX 航天链的市场快照,
转化为有纪律的决策(FREEZE / WATCH / ACT / RETIRE),而不是机械地按脚本触发器下单。它把此前的
研报当作"需要用当前证据更新的假设",而非"要去拟合的目标"。SPCX / 航天链是随仓库附带的参考实现;
底层引擎是通用的,可 fork 到任意超级 IPO(OpenAI、Anthropic、xAI、Stripe、Databricks……)。

### 核心理念
- **数据-判断分离** —— Python 算数字和新鲜度,agent 判断 regime/因果/可信度。见 `PRINCIPLES.md`。
- **时间锚定的新鲜度闸门** —— 行动关键的实时数据超过 1 个交易日即阻断 ACT,由校验器强制执行。
- **四镜头 + 对手方模型** —— 结构/宏观/叙事/市场,永远先问"谁在你对面"。见 `docs/decision-protocol.md`。
- **六种 regime** —— mechanical_bid / macro_shock / narrative_drain / narrative_migration / data_collision / no_edge。
- **确定性仓位** —— 由 `ecd.position_sizing` 计算,绝不用散文拍脑袋。

### 目录
- `examples/spcx-chain/` —— SPCX 参考 skill(SKILL.md + references + 校验器),可作为 Claude Code skill 安装。
- `src/ecd/` —— 纯标准库的通用引擎(新鲜度、仓位、通用信封)。
- `docs/` —— 通用协议/schema/仓位文档。

### 快速上手
见上方 English 的 Quick start。`reports/` 目录会自动创建并已被 gitignore。

### 在你的 agent 里使用
- **Claude Code**:`/loop` 每个交易日收盘后跑一遍,输出当天决策简报。
- **OpenClaw / Codex / 其他**:采集器产出证据包 → `validate` 把关 → 用 `examples/spcx-chain/SKILL.md` + 证据包提示 agent。详见 `runtime-integration.md`。agent 永不下单。

### 派生你自己的链
复制 `examples/spcx-chain/` 为 `examples/<your-chain>/`,替换领域字段,复用 `ecd.freshness`,通用层 `src/ecd/` 保持领域无关。

### 许可证
MIT。

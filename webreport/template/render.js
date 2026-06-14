(async function () {
  const data = window.REPORT_DATA ||
    await fetch('../sample/decision_sample.json').then(r => r.json());
  const STATIC = window.REPORT_STATIC === true ||
    new URLSearchParams(location.search).has('static');
  const deck = document.getElementById('deck');

  const STATUS_ORDER = { ACT: 0, WATCH: 1, FREEZE: 2, RETIRE: 3 };
  const DASH = [
    ['spcx', 'SPCX 主标的仪表盘'],
    ['macro', '宏观仪表盘'],
    ['mapped_stocks', '映射股仪表盘'],
    ['fundamental', '基本面 / 硬数据仪表盘'],
    ['sats_gs_supply', 'SATS / GS / 供应链仪表盘'],
    ['merger', '合并概念监测仪表盘'],
  ];
  const NA = '待补';
  const v = (x) => (x === null || x === undefined || x === '') ? NA : String(x);

  function page(cls) {
    const s = document.createElement('section');
    s.className = 'page ' + (cls || '');
    deck.appendChild(s);
    return s;
  }
  function h(parent, tag, cls, html) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html !== undefined) e.innerHTML = html;
    parent.appendChild(e);
    return e;
  }

  // 1. Cover
  {
    const p = page('cover');
    h(p, 'div', 'kicker', v(data.report_title));
    h(p, 'h1', 'stance', v(data.overall_stance));
    h(p, 'div', 'asof', '基准日 ' + v(data.analysis_as_of));
  }

  // 2. Phase state machine
  {
    const p = page('map');
    h(p, 'h2', null, '博弈地图 · 阶段状态机');
    const labels = { phase_0: 'Phase 0 冻结', phase_1: 'Phase 1 机械买盘', phase_2: 'Phase 2 主战场', post_august_reassessment: '8月后重估' };
    const row = h(p, 'div', 'phase-row');
    ['phase_0', 'phase_1', 'phase_2', 'post_august_reassessment'].forEach(ph => {
      const cell = h(row, 'div', 'phase-cell' + (ph === data.active_phase ? ' active' : ''), labels[ph]);
      if (ph === data.active_phase) h(cell, 'div', 'here', '你在这里');
    });
    h(p, 'div', 'note', v(data.phase_note));
  }

  // 3. Narrative cycle + word frequency
  {
    const p = page('map');
    h(p, 'h2', null, '博弈地图 · 叙事四阶段');
    const labels = { seeding: '播种', acceleration: '加速', saturation: '饱和', falsification: '证伪' };
    const row = h(p, 'div', 'cycle-row');
    ['seeding', 'acceleration', 'saturation', 'falsification'].forEach(s =>
      h(row, 'div', 'cycle-cell' + (s === data.narrative_cycle ? ' active' : ''), labels[s]));
    const wf = data.narrative_wordfreq || {};
    const bars = h(p, 'div', 'bars');
    [['a', 'A 财富神话'], ['b', 'B 抽血/解禁'], ['c', 'C 泡沫集中度'], ['d', 'D 垂直迁移']].forEach(([k, lab]) => {
      const b = h(bars, 'div', 'bar');
      h(b, 'div', 'bar-label', lab);
      const track = h(b, 'div', 'bar-track');
      h(track, 'div', 'bar-fill', '').style.width = Math.min(100, Number(wf[k] || 0)) + '%';
      h(b, 'div', 'bar-val', v(wf[k]));
    });
    h(p, 'div', 'note', 'B+C 连续超 A 天数：' + v(wf.bc_gt_a_consecutive_days));
  }

  // 3b. Narrative decision tree (hero) — defined in tree.js
  window.renderNarrativeTree(page('tree'), data, { static: STATIC, v: v, h: h });

  // 4. Opponent map
  {
    const p = page('map');
    h(p, 'h2', null, '博弈地图 · 对手盘');
    const o = data.opponent_model || {};
    h(p, 'div', 'kv', '可能对手：' + v(o.likely_counterparty));
    h(p, 'div', 'kv pos-' + v(o.retail_position), '散户位置：' + v(o.retail_position));
    h(p, 'div', 'kv risk-' + v(o.liquidity_trap_risk), '流动性陷阱风险：' + v(o.liquidity_trap_risk));
    h(p, 'div', 'note', v(o.why_this_price));
  }

  // 5. Timeline
  {
    const p = page('timeline');
    h(p, 'h2', null, '三连击时间线');
    const tl = h(p, 'div', 'tl');
    (data.timeline || []).forEach(t => {
      const item = h(tl, 'div', 'tl-item st-' + v(t.status));
      h(item, 'div', 'tl-date', v(t.date));
      h(item, 'div', 'tl-event', v(t.event));
    });
  }

  // 6. Card status board
  const sortedCards = (data.cards || []).slice().sort((a, b) =>
    ((STATUS_ORDER[a.status] ?? 9) - (STATUS_ORDER[b.status] ?? 9)));
  {
    const p = page('board');
    h(p, 'h2', null, '卡片状态总览 · ' + v(data.analysis_as_of));
    const grid = h(p, 'div', 'card-grid');
    sortedCards.forEach(c => {
      const chip = h(grid, 'div', 'chip s-' + v(c.status));
      h(chip, 'div', 'chip-name', v(c.label) + (c.changed_today ? ' ★' : ''));
      h(chip, 'div', 'chip-status', v(c.status));
    });
  }

  // 7..N per-card detail
  const GATES = [['data', '数据'], ['time', '时间'], ['structure', '结构'], ['narrative', '叙事'], ['rr', 'R/R']];
  sortedCards.forEach(c => {
    const p = page('card');
    h(p, 'div', 'card-head s-' + v(c.status), v(c.label) + ' · ' + v(c.status) + (c.changed_today ? ' ★今日变化' : ''));
    const g = h(p, 'div', 'gates');
    const gates = c.gates || {};
    GATES.forEach(([k, lab]) => {
      const cell = h(g, 'div', 'gate g-' + v(gates[k]));
      h(cell, 'div', 'gate-lab', lab);
      h(cell, 'div', 'gate-dot', '');
    });
    h(p, 'div', 'field', '卡住于：' + v(c.blocking_field));
    h(p, 'div', 'field', '距触发：' + v(c.distance_to_trigger));
    h(p, 'div', 'field inval', '失效触发：' + v(c.invalidation));
  });

  // dashboards (generic tables)
  const dash = data.dashboards || {};
  DASH.forEach(([key, title]) => {
    const p = page('dash');
    h(p, 'h2', null, title);
    const rows = dash[key] || [];
    const table = h(p, 'div', 'table');
    if (!rows.length) { h(table, 'div', 'empty', NA); return; }
    rows.forEach(r => {
      const tr = h(table, 'div', 'tr st-' + v(r.state));
      Object.keys(r).filter(k => k !== 'state').forEach(k => h(tr, 'div', 'td', v(r[k])));
    });
  });

  // daily review (8 questions)
  {
    const p = page('dash review');
    h(p, 'h2', null, '每日复盘 8 问');
    const list = h(p, 'div', 'qa');
    (dash.daily_review || []).forEach((qa, i) => {
      const item = h(list, 'div', 'qa-item');
      h(item, 'div', 'q', (i + 1) + '. ' + v(qa.q));
      h(item, 'div', 'a', v(qa.answer));
    });
  }

  // closing
  {
    const p = page('closing');
    h(p, 'div', 'disclaimer', v(data.disclaimer));
    h(p, 'div', 'attrib', 'powered by ' + v(data.skill_attribution));
  }

  window.__RENDER_DONE = true;
})();

// Narrative decision tree: vertical time axis (top=past -> bottom=future).
// Exposes window.renderNarrativeTree(page, data, opts).
window.renderNarrativeTree = function (page, data, opts) {
  const v = opts.v;
  const h = opts.h;
  const isStatic = !!opts.static;

  h(page, 'h2', null, '叙事决策树 · 过去 / 现在 / 未来');

  const tree = (data && data.narrative_tree) || {};
  const days = tree.days || [];
  const nodes = tree.nodes || [];
  const edges = tree.edges || [];

  if (!nodes.length) {
    h(page, 'div', 'empty', '待补');
    return;
  }

  // ---- precomputed vertical layout ----
  const CX = 460;          // spine center x (viewBox is 920 wide)
  const TOP = 110;
  const STEP = 210;        // gap between spine nodes
  const FAN_GAP = 320;     // present -> future vertical gap
  const SPREAD = 290;      // horizontal spread between future branches
  const pos = {};

  const spine = nodes.filter(n => n.tense === 'past' || n.tense === 'present');
  const futures = nodes.filter(n => n.tense === 'future');
  spine.forEach((n, i) => { pos[n.id] = { x: CX, y: TOP + i * STEP, r: 48, node: n }; });
  const presentY = spine.length ? pos[spine[spine.length - 1].id].y : TOP;
  futures.forEach((n, j) => {
    const x = CX + (j - (futures.length - 1) / 2) * SPREAD;
    pos[n.id] = { x: x, y: presentY + FAN_GAP, r: 42, node: n };
  });
  const H = presentY + FAN_GAP + 320;

  // ---- edges ----
  const edgeSvg = edges.map(e => {
    const a = pos[e.from], b = pos[e.to];
    if (!a || !b) return '';
    const my = (a.y + b.y) / 2;
    const d = 'M ' + a.x + ' ' + (a.y + a.r) +
      ' C ' + a.x + ' ' + my + ', ' + b.x + ' ' + my + ', ' + b.x + ' ' + (b.y - b.r);
    const prob = (e.prob !== undefined && e.prob !== null)
      ? '<text class="te-prob" x="' + ((a.x + b.x) / 2 + 24) + '" y="' + my + '">' +
        Math.round(Number(e.prob) * 100) + '%</text>' : '';
    return '<path class="tedge te-' + v(e.tense) + '" d="' + d + '" fill="none"/>' + prob;
  }).join('');

  // ---- nodes ----
  const nodeSvg = nodes.map(n => {
    const pp = pos[n.id];
    if (!pp) return '';
    const present = n.tense === 'present';
    const future = n.tense === 'future';
    const cls = 'tnode tn-' + v(n.tense) + (present ? ' pulse' : '') + (future ? ' clickable' : '');
    const probBadge = (future && n.prob != null)
      ? '<text class="tn-prob" x="' + pp.x + '" y="' + (pp.y - pp.r - 16) + '" text-anchor="middle">' +
        Math.round(Number(n.prob) * 100) + '%</text>' : '';
    const trig = future
      ? '<text class="tn-trig" x="' + pp.x + '" y="' + (pp.y + pp.r + 76) + '" text-anchor="middle">触发：' + v(n.trigger) + '</text>'
      : '';
    return '<g class="' + cls + '" data-node="' + v(n.id) + '">' +
      probBadge +
      '<circle cx="' + pp.x + '" cy="' + pp.y + '" r="' + pp.r + '"/>' +
      '<text class="tn-lab" x="' + pp.x + '" y="' + (pp.y + pp.r + 40) + '" text-anchor="middle">' + v(n.label) + '</text>' +
      trig +
      '</g>';
  }).join('');

  const wrap = h(page, 'div', 'tree-wrap');
  wrap.innerHTML = '<svg viewBox="0 0 920 ' + H + '" class="ntree" preserveAspectRatio="xMidYMin meet">' +
    edgeSvg + nodeSvg + '</svg>';

  // ---- day mini-bars (word-frequency at the current cursor; static => last day) ----
  const barWrap = h(page, 'div', 'tbars');
  const BAR_KEYS = [['a', 'A'], ['b', 'B'], ['c', 'C'], ['d', 'D']];
  function paintBars(idx) {
    const wf = (days[idx] && days[idx].wordfreq) || {};
    barWrap.innerHTML = '';
    BAR_KEYS.forEach(([k, lab]) => {
      const col = document.createElement('div');
      col.className = 'tbar';
      const fill = document.createElement('div');
      fill.className = 'tbar-fill';
      fill.style.height = Math.min(100, Number(wf[k] || 0)) + '%';
      const l = document.createElement('div');
      l.className = 'tbar-lab';
      l.textContent = lab + ' ' + v(wf[k]);
      col.appendChild(fill);
      col.appendChild(l);
      barWrap.appendChild(col);
    });
  }
  const lastIdx = Math.max(0, days.length - 1);
  paintBars(lastIdx);

  h(page, 'div', 'note', '上：叙事如何从过去流到现在、未来分叉与触发条件（虚线=未发生，标注为概率） · 下：词频随日演化');

  // expose state so Task E can attach playback/detail without re-laying-out
  window.__TREE = { page, wrap, pos, nodes, futures, days, paintBars, lastIdx, v: v };

  if (!isStatic && typeof window.attachTreeInteractivity === 'function') {
    window.attachTreeInteractivity(window.__TREE);
  }
};

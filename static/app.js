/* 2026 World Cup Group Stage Visualizer */

let overviewData = {};
let activeGroup = null;
let detailData = {};
let slotOpponents = {};

// ── Boot ─────────────────────────────────────────────────────────────────────
async function init() {
  const res = await fetch('/api/overview');
  overviewData = await res.json();
  renderOverview();
}

// ── Overview grid ─────────────────────────────────────────────────────────────
function renderOverview() {
  const grid = document.getElementById('overview-grid');
  grid.innerHTML = '';
  const letters = Object.keys(overviewData).sort();
  for (const letter of letters) {
    const d = overviewData[letter];
    const card = buildGroupCard(letter, d.standings, d.adv, d.matches);
    grid.appendChild(card);
  }
}

function buildGroupCard(letter, standings, adv, matches) {
  const card = document.createElement('div');
  card.className = 'group-card';
  card.dataset.letter = letter;
  card.addEventListener('click', () => openGroup(letter));

  // Mini standings with Adv%
  let tableHtml = `<h2>Group ${letter}</h2>
  <table class="mini-table">
    <thead><tr><th>Team</th><th>Pts</th><th>GD</th><th>Adv%</th></tr></thead>
    <tbody>`;

  // Order by current standings position
  const orderedTeams = standings.map(s => s.team);
  standings.forEach((s, i) => {
    const a = adv[s.team];
    const advPct = Math.round(a.advance * 100);
    const advClass = advPct >= 80 ? 'adv-green' : advPct >= 40 ? 'adv-yellow' : 'adv-red';
    tableHtml += `<tr class="rank-${i+1}">
      <td>${s.team}</td>
      <td>${s.pts}</td>
      <td>${s.gd >= 0 ? '+' : ''}${s.gd}</td>
      <td><span class="adv-badge ${advClass}">${advPct}%</span></td>
    </tr>`;
  });
  tableHtml += `</tbody></table>`;

  // Prob bars (stacked per team: 1st/2nd/3rd-adv/3rd-out/4th)
  let barsHtml = `<div class="prob-bars">`;
  for (const team of orderedTeams) {
    const a = adv[team];
    const p = a.pos;
    const thirdAdv = p['3rd'] * a.third_advance;
    const thirdOut = p['3rd'] * (1 - a.third_advance);
    barsHtml += `<div class="prob-row">
      <span class="prob-name">${team}</span>
      <div class="bar-track">
        <div class="bar-seg bar-1st" style="width:${p['1st']*100}%"></div>
        <div class="bar-seg bar-2nd" style="width:${p['2nd']*100}%"></div>
        <div class="bar-seg bar-3rd-adv" style="width:${thirdAdv*100}%"></div>
        <div class="bar-seg bar-3rd-out" style="width:${thirdOut*100}%"></div>
        <div class="bar-seg bar-4th" style="width:${p['4th']*100}%"></div>
      </div>
    </div>`;
  }
  barsHtml += `</div>`;

  card.innerHTML = tableHtml + barsHtml;
  return card;
}

// ── Group Detail ──────────────────────────────────────────────────────────────
async function openGroup(letter) {
  if (activeGroup === letter) {
    closeGroup();
    return;
  }
  activeGroup = letter;

  document.querySelectorAll('.group-card').forEach(c => {
    c.classList.toggle('active', c.dataset.letter === letter);
  });

  const panel = document.getElementById('group-detail');
  panel.classList.remove('hidden');
  panel.innerHTML = `<div class="loading">Loading Group ${letter}…</div>`;

  const res = await fetch(`/api/group/${letter}`);
  detailData = await res.json();
  slotOpponents = detailData.slot_opponents || {};
  renderDetail(detailData);
}

function closeGroup() {
  activeGroup = null;
  document.querySelectorAll('.group-card').forEach(c => c.classList.remove('active'));
  document.getElementById('group-detail').classList.add('hidden');
}

function renderDetail(data) {
  const panel = document.getElementById('group-detail');
  const { letter, matches, standings, adv, ranked, tiebreak_reasons } = data;

  panel.innerHTML = `
    <div class="detail-header">
      <h2>Group ${letter}</h2>
      <button class="close-btn" onclick="closeGroup()">Close</button>
    </div>
    <div class="detail-cols">
      <div>
        <div class="section-title">Matches</div>
        <div class="match-list" id="match-list"></div>
        <div class="sim-actions">
          <button class="btn-primary" onclick="simulate()">Simulate with these scores</button>
          <button class="btn-secondary" onclick="resetScores()">Reset to actual</button>
        </div>
      </div>
      <div>
        <div class="section-title">Standings &amp; Advancement</div>
        <div id="standings-container"></div>
        <div class="detail-probs" id="detail-probs"></div>
        <div class="legend">
          <div class="legend-item"><div class="legend-dot" style="background:#3fb950"></div>1st</div>
          <div class="legend-item"><div class="legend-dot" style="background:#58a6ff"></div>2nd</div>
          <div class="legend-item"><div class="legend-dot" style="background:#d29922"></div>3rd✓</div>
          <div class="legend-item"><div class="legend-dot" style="background:#6e4e00"></div>3rd✗</div>
          <div class="legend-item"><div class="legend-dot" style="background:#6e7681"></div>4th</div>
        </div>
      </div>
    </div>`;

  renderMatchList(matches);
  renderStandings(ranked, tiebreak_reasons, adv);
  renderDetailProbs(adv, ranked);
}

function renderMatchList(matches) {
  const list = document.getElementById('match-list');
  list.innerHTML = '';
  for (const m of matches) {
    const row = document.createElement('div');
    row.className = 'match-row';
    if (m.played) {
      row.innerHTML = `
        <span class="match-team">${m.home}</span>
        <div class="match-score">
          <span class="score-display">${m.home_score} – ${m.away_score}</span>
          <span class="played-badge">✓</span>
        </div>
        <span class="match-team away">${m.away}</span>`;
    } else {
      row.innerHTML = `
        <span class="match-team">${m.home}</span>
        <div class="match-score">
          <input class="score-input" type="number" min="0" max="20"
            data-home="${m.home}" data-away="${m.away}" data-side="home"
            placeholder="–">
          <span class="score-sep">–</span>
          <input class="score-input" type="number" min="0" max="20"
            data-home="${m.home}" data-away="${m.away}" data-side="away"
            placeholder="–">
        </div>
        <span class="match-team away">${m.away}</span>`;
    }
    list.appendChild(row);
  }
}

function renderStandings(ranked, reasons, adv) {
  const container = document.getElementById('standings-container');
  let html = `<table class="standings-table">
    <thead><tr><th>#</th><th>Team</th><th>Pts</th><th>GD</th><th>GF</th><th>Adv%</th></tr></thead>
    <tbody>`;
  ranked.forEach((s, i) => {
    const pos = i + 1;
    const a = adv[s.team];
    const advPct = Math.round(a.advance * 100);
    const advClass = advPct >= 80 ? 'adv-green' : advPct >= 40 ? 'adv-yellow' : 'adv-red';
    const reason = reasons[s.team] ? `<span class="tiebreak-tag">${reasons[s.team]}</span>` : '';

    // R32 slot breakdown for teams with non-zero r32_slots
    let slotHtml = '';
    const slots = a.r32_slots || {};
    const slotEntries = Object.entries(slots).sort((x, y) => y[1] - x[1]);
    if (slotEntries.length > 0) {
      const parts = slotEntries
        .filter(([, p]) => p > 0.001)
        .map(([sid, p]) => {
          const opp = slotOpponents[sid] || `Slot ${sid}`;
          return `${opp} (${Math.round(p * 100)}%)`;
        });
      if (parts.length) {
        slotHtml = `<div class="slot-breakdown">${parts.join(' · ')}</div>`;
      }
    }

    html += `<tr>
      <td><span class="pos-badge pos-${pos}">${pos}</span></td>
      <td>${s.team}${reason}${slotHtml}</td>
      <td>${s.pts}</td>
      <td>${s.gd >= 0 ? '+' : ''}${s.gd}</td>
      <td>${s.gf}</td>
      <td><span class="adv-badge ${advClass}">${advPct}%</span></td>
    </tr>`;
  });
  html += `</tbody></table>`;
  container.innerHTML = html;
}

function renderDetailProbs(adv, ranked) {
  const container = document.getElementById('detail-probs');
  container.innerHTML = '<div class="section-title" style="margin-top:1.25rem">Finishing Position Probabilities</div>';
  for (const s of ranked) {
    const team = s.team;
    const a = adv[team];
    const p = a.pos;
    const thirdAdv = p['3rd'] * a.third_advance;
    const thirdOut = p['3rd'] * (1 - a.third_advance);
    const row = document.createElement('div');
    row.className = 'detail-prob-row';
    row.innerHTML = `
      <span class="detail-prob-name">${team}</span>
      <div class="detail-bar-track">
        <div class="bar-seg bar-1st" style="width:${p['1st']*100}%"></div>
        <div class="bar-seg bar-2nd" style="width:${p['2nd']*100}%"></div>
        <div class="bar-seg bar-3rd-adv" style="width:${thirdAdv*100}%"></div>
        <div class="bar-seg bar-3rd-out" style="width:${thirdOut*100}%"></div>
        <div class="bar-seg bar-4th" style="width:${p['4th']*100}%"></div>
      </div>
      <div class="detail-prob-pcts">
        <span class="pct-1st">${fmt(p['1st'])}</span>
        <span class="pct-2nd">${fmt(p['2nd'])}</span>
        <span class="pct-3rd">${fmt(p['3rd'])}</span>
        <span class="pct-4th">${fmt(p['4th'])}</span>
      </div>`;
    container.appendChild(row);
  }
}

function fmt(p) {
  const v = Math.round(p * 100);
  return v === 0 ? '–' : v + '%';
}

// ── Simulate ──────────────────────────────────────────────────────────────────
async function simulate() {
  const inputs = document.querySelectorAll('.score-input[data-side="home"]');
  const scores = [];

  for (const homeInput of inputs) {
    const home = homeInput.dataset.home;
    const away = homeInput.dataset.away;
    const awayInput = document.querySelector(
      `.score-input[data-home="${home}"][data-away="${away}"][data-side="away"]`
    );
    const hs = homeInput.value.trim();
    const as_ = awayInput.value.trim();
    scores.push({
      home,
      away,
      home_score: hs !== '' ? parseInt(hs) : null,
      away_score: as_ !== '' ? parseInt(as_) : null,
    });
  }

  const btn = document.querySelector('.btn-primary');
  btn.textContent = 'Simulating…';
  btn.disabled = true;

  try {
    const res = await fetch(`/api/group/${activeGroup}/simulate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scores }),
    });
    const data = await res.json();
    slotOpponents = data.slot_opponents || slotOpponents;
    renderStandings(data.ranked, data.tiebreak_reasons, data.adv);
    renderDetailProbs(data.adv, data.ranked);

    // Update the group card in the overview to reflect hypothetical adv probs
    overviewData[activeGroup].adv = data.adv;
    overviewData[activeGroup].standings = data.standings;
    refreshGroupCard(activeGroup, data.standings, data.adv);
  } finally {
    btn.textContent = 'Simulate with these scores';
    btn.disabled = false;
  }
}

// ── Refresh group card in the overview grid ───────────────────────────────────
function refreshGroupCard(letter, standings, adv) {
  const card = document.querySelector(`.group-card[data-letter="${letter}"]`);
  if (!card) return;
  const wasActive = card.classList.contains('active');
  const newCard = buildGroupCard(letter, standings, adv, overviewData[letter].matches);
  if (wasActive) newCard.classList.add('active');
  card.parentNode.replaceChild(newCard, card);
}

// ── Reset ─────────────────────────────────────────────────────────────────────
function resetScores() {
  const orig = overviewData[activeGroup];
  renderMatchList(detailData.matches);
  renderStandings(detailData.ranked, detailData.tiebreak_reasons, detailData.adv);
  renderDetailProbs(detailData.adv, detailData.ranked);
  // Revert the group card to the startup probabilities
  overviewData[activeGroup].adv = detailData.adv;
  overviewData[activeGroup].standings = detailData.standings || orig.standings;
  refreshGroupCard(activeGroup, overviewData[activeGroup].standings, detailData.adv);
}

// ── Go ────────────────────────────────────────────────────────────────────────
init();

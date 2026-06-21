/* 2026 World Cup Group Stage Visualizer */

let overviewData = {};
let activeGroup = null;
let detailData = {};

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
    const card = buildGroupCard(letter, d.standings, d.probs, d.matches);
    grid.appendChild(card);
  }
}

function buildGroupCard(letter, standings, probs, matches) {
  const card = document.createElement('div');
  card.className = 'group-card';
  card.dataset.letter = letter;
  card.addEventListener('click', () => openGroup(letter));

  // Mini standings
  let tableHtml = `<h2>Group ${letter}</h2>
  <table class="mini-table">
    <thead><tr><th>Team</th><th>Pts</th><th>GD</th><th>GF</th></tr></thead>
    <tbody>`;
  standings.forEach((s, i) => {
    tableHtml += `<tr class="rank-${i+1}">
      <td>${s.team}</td>
      <td>${s.pts}</td>
      <td>${s.gd >= 0 ? '+' : ''}${s.gd}</td>
      <td>${s.gf}</td>
    </tr>`;
  });
  tableHtml += `</tbody></table>`;

  // Prob bars (stacked per team)
  const orderedTeams = standings.map(s => s.team);
  let barsHtml = `<div class="prob-bars">`;
  for (const team of orderedTeams) {
    const p = probs[team];
    const topProb = Math.round(p['1st'] * 100);
    barsHtml += `<div class="prob-row">
      <span class="prob-name">${team}</span>
      <div class="bar-track">
        <div class="bar-seg bar-1st" style="width:${p['1st']*100}%"></div>
        <div class="bar-seg bar-2nd" style="width:${p['2nd']*100}%"></div>
        <div class="bar-seg bar-3rd" style="width:${p['3rd']*100}%"></div>
        <div class="bar-seg bar-4th" style="width:${p['4th']*100}%"></div>
      </div>
      <span class="prob-pct">${Math.round(p['1st']*100)}%</span>
    </div>`;
  }
  barsHtml += `</div>`;

  card.innerHTML = tableHtml + barsHtml;
  return card;
}

// ── Group Detail ──────────────────────────────────────────────────────────────
async function openGroup(letter) {
  // Toggle
  if (activeGroup === letter) {
    closeGroup();
    return;
  }
  activeGroup = letter;

  // Mark active card
  document.querySelectorAll('.group-card').forEach(c => {
    c.classList.toggle('active', c.dataset.letter === letter);
  });

  const panel = document.getElementById('group-detail');
  panel.classList.remove('hidden');
  panel.innerHTML = `<div class="loading">Loading Group ${letter}…</div>`;

  const res = await fetch(`/api/group/${letter}`);
  detailData = await res.json();
  renderDetail(detailData);
}

function closeGroup() {
  activeGroup = null;
  document.querySelectorAll('.group-card').forEach(c => c.classList.remove('active'));
  document.getElementById('group-detail').classList.add('hidden');
}

function renderDetail(data) {
  const panel = document.getElementById('group-detail');
  const { letter, matches, standings, probs, ranked, tiebreak_reasons } = data;

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
        <div class="section-title">Current Standings</div>
        <div id="standings-container"></div>
        <div class="detail-probs" id="detail-probs"></div>
        <div class="legend">
          <div class="legend-item"><div class="legend-dot" style="background:#3fb950"></div>1st</div>
          <div class="legend-item"><div class="legend-dot" style="background:#58a6ff"></div>2nd</div>
          <div class="legend-item"><div class="legend-dot" style="background:#d29922"></div>3rd</div>
          <div class="legend-item"><div class="legend-dot" style="background:#6e7681"></div>4th</div>
        </div>
      </div>
    </div>`;

  renderMatchList(matches);
  renderStandings(ranked, tiebreak_reasons);
  renderDetailProbs(probs, ranked);
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

function renderStandings(ranked, reasons) {
  const container = document.getElementById('standings-container');
  let html = `<table class="standings-table">
    <thead><tr><th>#</th><th>Team</th><th>Pts</th><th>GD</th><th>GF</th><th>GA</th></tr></thead>
    <tbody>`;
  ranked.forEach((s, i) => {
    const pos = i + 1;
    const reason = reasons[s.team] ? `<span class="tiebreak-tag">${reasons[s.team]}</span>` : '';
    html += `<tr>
      <td><span class="pos-badge pos-${pos}">${pos}</span></td>
      <td>${s.team}${reason}</td>
      <td>${s.pts}</td>
      <td>${s.gd >= 0 ? '+' : ''}${s.gd}</td>
      <td>${s.gf}</td>
      <td>${s.ga}</td>
    </tr>`;
  });
  html += `</tbody></table>`;
  container.innerHTML = html;
}

function renderDetailProbs(probs, ranked) {
  const container = document.getElementById('detail-probs');
  container.innerHTML = '<div class="section-title" style="margin-top:1.25rem">Finishing Position Probabilities</div>';
  for (const s of ranked) {
    const team = s.team;
    const p = probs[team];
    const row = document.createElement('div');
    row.className = 'detail-prob-row';
    row.innerHTML = `
      <span class="detail-prob-name">${team}</span>
      <div class="detail-bar-track">
        <div class="bar-seg bar-1st" style="width:${p['1st']*100}%"></div>
        <div class="bar-seg bar-2nd" style="width:${p['2nd']*100}%"></div>
        <div class="bar-seg bar-3rd" style="width:${p['3rd']*100}%"></div>
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
    renderStandings(data.ranked, data.tiebreak_reasons);
    renderDetailProbs(data.probs, data.ranked);
  } finally {
    btn.textContent = 'Simulate with these scores';
    btn.disabled = false;
  }
}

// ── Reset ─────────────────────────────────────────────────────────────────────
function resetScores() {
  renderMatchList(detailData.matches);
  renderStandings(detailData.ranked, detailData.tiebreak_reasons);
  renderDetailProbs(detailData.probs, detailData.ranked);
}

// ── Go ────────────────────────────────────────────────────────────────────────
init();

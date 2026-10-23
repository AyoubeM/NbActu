// NBA Actu Dashboard Logic

let currentData = null;
let isSpoilerMode = true;

document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  initSpoilerToggle();
  initPlayerSearch();
  loadData();
});

// Load data.json
async function loadData() {
  try {
    const res = await fetch("data.json?t=" + new Date().getTime());
    if (!res.ok) throw new Error("Impossible de charger data.json");
    currentData = await res.json();
    renderAll(currentData);
  } catch (err) {
    console.warn("data.json not loaded yet, trying data/recap.json or fallback", err);
    try {
      const resFallback = await fetch("../data/recap.json");
      if (resFallback.ok) {
        currentData = await resFallback.json();
        renderAll(currentData);
        return;
      }
    } catch (_) {}
    document.getElementById("games-container").innerHTML = `
      <div style="grid-column: 1/-1; text-align: center; padding: 3rem; color: var(--text-dim);">
        <h3>Aucune donnée chargée pour le moment</h3>
        <p>Lancez le script <code>python main.py</code> pour générer les données de la nuit.</p>
      </div>
    `;
  }
}

function renderAll(data) {
  if (!data) return;

  // Header date and games count
  if (data.date_formatted) {
    document.getElementById("recap-date").textContent = `Nuit du ${data.date_formatted}`;
  }
  const gamesCount = (data.games || []).length;
  document.getElementById("games-count-tag").textContent = `${gamesCount} Match(s) disputé(s)`;

  renderGames(data.games || []);
  renderUpcoming(data.upcoming || []);
  renderPerformers(data.players_analysis?.top_performers || []);
  renderFrench(data.players_analysis?.french_players || []);
  renderStandings(data.standings || {});
  renderAllPlayers(data.players_analysis?.all_players || []);
}

// 1. Render Completed Games
function renderGames(games) {
  const container = document.getElementById("games-container");
  if (!games.length) {
    container.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 2rem;">Aucun match terminé cette nuit.</div>`;
    return;
  }

  container.innerHTML = games.map((g, index) => {
    const home = g.home;
    const away = g.away;
    const highlight = g.highlight || {};
    const broadcaster = g.broadcaster || "NBA League Pass";
    const boxId = `boxscore-${index}`;

    return `
      <div class="game-card">
        <div class="game-card-header">
          <span class="broadcast-badge">${broadcaster}</span>
          <span style="color: var(--text-dim); font-size: 0.75rem;">${g.status_detail || "Terminé"}</span>
        </div>
        <div class="match-body">
          <div class="team-box">
            <img class="team-logo" src="${away.logo}" alt="${away.name}" onerror="this.style.display='none'">
            <div class="team-name">${away.shortName || away.name}</div>
            <div class="team-meta">${away.record || ""}</div>
            <div class="streak-tag">${g.away_form?.streak_formatted || "-"}</div>
          </div>
          <div class="score-box">
            <div class="score-display spoiled-score" onclick="this.classList.toggle('revealed')">
              ${away.score} - ${home.score}
            </div>
          </div>
          <div class="team-box">
            <img class="team-logo" src="${home.logo}" alt="${home.name}" onerror="this.style.display='none'">
            <div class="team-name">${home.shortName || home.name}</div>
            <div class="team-meta">${home.record || ""}</div>
            <div class="streak-tag">${g.home_form?.streak_formatted || "-"}</div>
          </div>
        </div>
        <div class="game-card-footer">
          <a class="btn btn-primary" href="${highlight.url}" target="_blank" rel="noopener">
            ▶ Résumé (${highlight.language || "VO"})
          </a>
          <button class="btn btn-secondary" onclick="toggleBoxscore('${boxId}')">
            📊 Boxscore
          </button>
        </div>
        <div id="${boxId}" class="boxscore-drawer">
          ${renderBoxscoreTables(g.boxscore)}
        </div>
      </div>
    `;
  }).join("");
}

// 1b. Render Upcoming Games (Tonight)
function renderUpcoming(upcomingGames) {
  const container = document.getElementById("upcoming-container");
  if (!container) return;
  if (!upcomingGames.length) {
    container.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 2rem;">Aucun match programmé pour les prochaines 24h.</div>`;
    return;
  }

  container.innerHTML = upcomingGames.map(g => {
    const home = g.home;
    const away = g.away;
    const broadcaster = g.broadcaster || "NBA League Pass";
    const statusText = g.status_detail || "À venir ce soir";

    return `
      <div class="game-card">
        <div class="game-card-header">
          <span class="broadcast-badge">${broadcaster}</span>
          <span style="color: #60a5fa; font-size: 0.75rem; font-weight: 600;">⏰ ${statusText}</span>
        </div>
        <div class="match-body">
          <div class="team-box">
            <img class="team-logo" src="${away.logo}" alt="${away.name}" onerror="this.style.display='none'">
            <div class="team-name">${away.shortName || away.name}</div>
            <div class="team-meta">${away.record || ""}</div>
          </div>
          <div class="score-box">
            <div style="font-size: 0.9rem; font-weight: 700; color: var(--text-dim);">VS</div>
          </div>
          <div class="team-box">
            <img class="team-logo" src="${home.logo}" alt="${home.name}" onerror="this.style.display='none'">
            <div class="team-name">${home.shortName || home.name}</div>
            <div class="team-meta">${home.record || ""}</div>
          </div>
        </div>
        <div class="game-card-footer" style="justify-content: center; font-size: 0.8rem; color: var(--text-dim);">
          Diffusion officielle en direct : ${broadcaster}
        </div>
      </div>
    `;
  }).join("");
}

function renderBoxscoreTables(boxscore) {
  if (!boxscore || !boxscore.teams || !boxscore.teams.length) {
    return `<div style="padding: 1rem; color: var(--text-dim);">Détails du boxscore non disponibles.</div>`;
  }

  return boxscore.teams.map(team => `
    <div style="margin-bottom: 1.25rem;">
      <h4 style="color: #60a5fa; margin-bottom: 0.5rem; font-size: 0.85rem;">${team.team_name}</h4>
      <table class="boxscore-table">
        <thead>
          <tr>
            <th>Joueur</th><th>MIN</th><th>PTS</th><th>REB</th><th>AST</th><th>+/-</th>
          </tr>
        </thead>
        <tbody>
          ${(team.players || []).map(p => `
            <tr>
              <td><strong>${p.name}</strong> <span style="color: var(--text-dim)">${p.position || ""}</span></td>
              <td>${p.minutes}</td>
              <td class="player-highlight">${p.pts}</td>
              <td>${p.reb}</td>
              <td>${p.ast}</td>
              <td style="color: ${String(p.plus_minus).startsWith('+') ? '#34d399' : '#f87171'}">${p.plus_minus}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
  `).join("");
}

window.toggleBoxscore = function(id) {
  const el = document.getElementById(id);
  if (el) el.classList.toggle("open");
};

// 2. Render Top Performers
function renderPerformers(performers) {
  const container = document.getElementById("performers-container");
  if (!performers.length) {
    container.innerHTML = `<div style="grid-column: 1/-1; text-align: center;">Aucune stat individuelle disponible.</div>`;
    return;
  }

  container.innerHTML = performers.map((p, i) => `
    <div class="performer-card">
      <span class="performer-badge">#${i + 1} MVP Nuit</span>
      <div class="performer-name">${p.name}</div>
      <div class="performer-team">${p.team_name} • ${p.position || "Joueur"}</div>
      <div class="performer-stats">
        <div class="stat-chip"><div class="val">${p.pts}</div><div class="lbl">PTS</div></div>
        <div class="stat-chip"><div class="val">${p.reb}</div><div class="lbl">REB</div></div>
        <div class="stat-chip"><div class="val">${p.ast}</div><div class="lbl">AST</div></div>
        <div class="stat-chip"><div class="val">${p.game_score}</div><div class="lbl">GameScore</div></div>
      </div>
    </div>
  `).join("");
}

// 3. Render French Focus 🇫🇷
function renderFrench(frenchPlayers) {
  const container = document.getElementById("french-container");
  if (!frenchPlayers.length) {
    container.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 2rem; color: var(--text-dim);">Aucun joueur français n'a joué sur les parquets cette nuit.</div>`;
    return;
  }

  container.innerHTML = frenchPlayers.map(p => `
    <div class="performer-card" style="border-left: 3px solid #3b82f6;">
      <span class="performer-badge" style="background: rgba(59, 130, 246, 0.2); color: #60a5fa;">🇫🇷 France</span>
      <div class="performer-name">${p.name}</div>
      <div class="performer-team">${p.team_name} • ${p.minutes} MIN</div>
      <div class="performer-stats">
        <div class="stat-chip"><div class="val">${p.pts}</div><div class="lbl">PTS</div></div>
        <div class="stat-chip"><div class="val">${p.reb}</div><div class="lbl">REB</div></div>
        <div class="stat-chip"><div class="val">${p.ast}</div><div class="lbl">AST</div></div>
        <div class="stat-chip"><div class="val">${p.blk || 0}</div><div class="lbl">BLK</div></div>
      </div>
    </div>
  `).join("");
}

// 4. Render Standings
function renderStandings(standings) {
  const eastTbody = document.getElementById("east-standings-body");
  const westTbody = document.getElementById("west-standings-body");

  const teams = Object.values(standings);
  // deduplicate by team_name
  const uniqueTeams = Array.from(new Map(teams.map(t => [t.team_name, t])).values());

  const east = uniqueTeams.filter(t => t.conference === "Est").sort((a, b) => parseInt(a.rank) - parseInt(b.rank));
  const west = uniqueTeams.filter(t => t.conference === "Ouest").sort((a, b) => parseInt(a.rank) - parseInt(b.rank));

  const buildRows = list => list.map(t => `
    <tr>
      <td>${t.rank}</td>
      <td><strong>${t.team_name}</strong></td>
      <td>${t.record}</td>
      <td>${t.streak_formatted || t.streak}</td>
      <td>${t.l10}</td>
    </tr>
  `).join("");

  if (eastTbody) eastTbody.innerHTML = buildRows(east);
  if (westTbody) westTbody.innerHTML = buildRows(west);
}

// 5. Render All Players
function renderAllPlayers(players) {
  const tbody = document.getElementById("all-players-body");
  if (!tbody) return;

  tbody.innerHTML = players.map(p => `
    <tr class="player-row" data-name="${p.name.toLowerCase()}">
      <td><strong>${p.name}</strong> ${p.is_french ? "🇫🇷" : ""}</td>
      <td>${p.team_abbrev || p.team_name}</td>
      <td>${p.minutes}</td>
      <td class="player-highlight">${p.pts}</td>
      <td>${p.reb}</td>
      <td>${p.ast}</td>
      <td>${p.stl}</td>
      <td>${p.blk}</td>
      <td>${p.fg}</td>
      <td>${p.three_pt}</td>
      <td style="color: ${String(p.plus_minus).startsWith('+') ? '#34d399' : '#f87171'}">${p.plus_minus}</td>
      <td><strong>${p.game_score}</strong></td>
    </tr>
  `).join("");
}

// Search Filter
function initPlayerSearch() {
  const searchInput = document.getElementById("player-search");
  if (!searchInput) return;

  searchInput.addEventListener("input", (e) => {
    const q = e.target.value.toLowerCase().trim();
    document.querySelectorAll(".player-row").forEach(row => {
      const name = row.getAttribute("data-name") || "";
      row.style.display = name.includes(q) ? "" : "none";
    });
  });
}

// Tabs
function initTabs() {
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));

      btn.classList.add("active");
      const target = document.getElementById(btn.getAttribute("data-tab"));
      if (target) target.classList.add("active");
    });
  });
}

// Spoiler Toggle
function initSpoilerToggle() {
  const btn = document.getElementById("spoiler-toggle");
  const text = document.getElementById("spoiler-text");

  btn.addEventListener("click", () => {
    isSpoilerMode = !isSpoilerMode;
    document.body.classList.toggle("spoiler-mode", isSpoilerMode);
    btn.classList.toggle("active", isSpoilerMode);
    text.textContent = isSpoilerMode ? "Anti-Spoiler : Activé" : "Anti-Spoiler : Désactivé";
  });
}

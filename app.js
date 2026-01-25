// =========================================================
// IriLine Collective — APP JS (STATIC VERSION)
// - Loads hero from data/live.json
// - Builds ticker
// - Builds grids (Latest / Sports / Meme)
// - Tab switches the "Latest" grid content (LATEST/SPORTS/MEME)
// =========================================================

// ==============================
// DATA SOURCES (GitHub Pages)
// ==============================
const LIVE_URL = "data/live.json";
const ARCHIVE_URL = "data/archive.json"; // optional (not used yet)

// Rotation settings
const HERO_ROTATE_MS = 9000;   // readable pace
const HERO_FADE_MS = 450;

// Keep hero rotating between these sections
const HERO_SOURCES = ["LATEST", "SPORTS", "MEME"];

// ==============================
// Helpers
// ==============================
function qs(id) { return document.getElementById(id); }
function safeText(x) { return (x ?? "").toString(); }

function timeAgo(iso) {
  if (!iso) return "";
  const now = new Date();
  const then = new Date(iso);
  const diff = Math.floor((now - then) / 1000);

  if (diff < 60) return "Just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

async function loadJSON(url) {
  const r = await fetch(url, { cache: "no-store" });
  if (!r.ok) throw new Error(`Failed to load: ${url}`);
  return await r.json();
}

// ==============================
// Hero
// ==============================
let heroPool = [];
let heroIndex = 0;
let heroTimer = null;

function setHero(item) {
  if (!item) return;

  qs("heroCategory").textContent = safeText(item.sectionLabel || item.category || item.type || "FEATURE");
  qs("heroTitle").textContent = safeText(item.title);
  qs("heroDek").textContent = safeText(item.dek);
  qs("heroLink").href = `article.html?id=${encodeURIComponent(item.id)}`;

  if (item.image) {
    qs("hero").style.backgroundImage =
      `linear-gradient(90deg, rgba(15,15,15,0.86) 0%, rgba(15,15,15,0.52) 55%, rgba(15,15,15,0.20) 100%), url("${item.image}")`;
  }
}

function fadeSwapHero(nextItem) {
  const hero = qs("hero");
  if (!hero) return;

  hero.style.transform = "scale(1.015)";
  hero.style.opacity = "0";

  setTimeout(() => {
    setHero(nextItem);
    hero.style.opacity = "1";
    hero.style.transform = "scale(1)";
  }, HERO_FADE_MS);
}

function pickHeroPool(items) {
  const bySection = {};
  HERO_SOURCES.forEach(s => (bySection[s] = []));

  items.forEach(it => {
    if (bySection[it.section]) bySection[it.section].push(it);
  });

  const pool = [];
  HERO_SOURCES.forEach(s => {
    bySection[s]
      .sort((a, b) => (b.publishedAt || "").localeCompare(a.publishedAt || ""))
      .slice(0, 2)
      .forEach(x => pool.push(x));
  });

  return pool.length ? pool : items.slice(0, 5);
}

function startHeroRotation() {
  if (heroTimer) clearInterval(heroTimer);

  heroTimer = setInterval(() => {
    if (!heroPool.length) return;
    heroIndex = (heroIndex + 1) % heroPool.length;
    fadeSwapHero(heroPool[heroIndex]);
  }, HERO_ROTATE_MS);
}

// ==============================
// Cards + Grids
// ==============================
function buildCard(item) {
  const card = document.createElement("div");
  card.className = "card card--withThumb";

  const thumb = document.createElement("div");
  thumb.className = "card__thumb";
  thumb.style.backgroundImage = `url("${item.image || ""}")`;

  const right = document.createElement("div");

  const meta = document.createElement("div");
  meta.className = "card__meta";

  const isBreaking =
    item.publishedAt &&
    (Date.now() - new Date(item.publishedAt)) < 30 * 60 * 1000;

  if (isBreaking) {
    const breaking = document.createElement("span");
    breaking.className = "pill pill--breaking";
    breaking.textContent = "BREAKING";
    meta.appendChild(breaking);
  }

  const typePill = document.createElement("span");
  typePill.className = "pill " + (item.type === "MEME" ? "pill--meme" : "");
  typePill.textContent = item.type || "REAL";

  const catPill = document.createElement("span");
  catPill.className = "pill pill--muted";
  catPill.textContent = item.category || item.sectionLabel || "GENERAL";

  const time = document.createElement("span");
  time.className = "card__time";
  time.textContent = timeAgo(item.publishedAt);

  meta.append(typePill, catPill, time);

  const title = document.createElement("h3");
  title.className = "card__title";
  title.textContent = item.title || "";

  const dek = document.createElement("p");
  dek.className = "card__dek";
  dek.textContent = item.dek || "";

  const link = document.createElement("a");
  link.className = "card__link";
  link.href = `article.html?id=${encodeURIComponent(item.id)}`;
  link.textContent = "Open story →";

  right.append(meta, title, dek, link);
  card.append(thumb, right);

  return card;
}

function fillGrid(gridId, items) {
  const grid = qs(gridId);
  if (!grid) return;

  const empty = grid.parentElement?.querySelector(".empty-state");

  grid.innerHTML = "";

  if (!items || items.length === 0) {
    if (empty) empty.hidden = false;
    return;
  }

  if (empty) empty.hidden = true;

  items.forEach(item => {
    grid.appendChild(buildCard(item));
  });
}

// ==============================
// Ticker
// ==============================
function fillTicker(items) {
  const track = qs("tickerTrack");
  if (!track) return;

  track.innerHTML = "";

  const doubled = items.concat(items);

  doubled.forEach(item => {
    const node = document.createElement("div");
    node.className = "ticker__item";

    const pill = document.createElement("span");
    pill.className = "ticker__pill";
    pill.textContent = `${item.type || "REAL"} • ${item.category || item.sectionLabel || "GENERAL"}`;

    const a = document.createElement("a");
    a.className = "ticker__link";
    a.href = `article.html?id=${encodeURIComponent(item.id)}`;
    a.textContent = item.title || "";

    node.append(pill, a);
    track.appendChild(node);
  });
}

// ==============================
// Tabs (switches what shows in latestGrid)
// ==============================
function setupTabs(items) {
  const tabs = document.querySelectorAll(".tab");
  const grid = qs("latestGrid");
  if (!tabs.length || !grid) return;

  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      tabs.forEach(t => t.classList.remove("active"));
      tab.classList.add("active");

      const section = tab.dataset.section; // LATEST / SPORTS / MEME
      const filtered = items.filter(i => i.section === section);

      grid.style.opacity = "0";
      setTimeout(() => {
        grid.innerHTML = "";
        filtered.slice(0, 9).forEach(i => grid.appendChild(buildCard(i)));
        grid.style.opacity = "1";
      }, 180);
    });
  });
}

// ==============================
// Main init
// ==============================
async function init() {
  const liveData = await loadJSON(LIVE_URL);
  const items = liveData.items || [];

  // Hero
  heroPool = pickHeroPool(items);
  heroIndex = 0;
  if (heroPool.length) setHero(heroPool[0]);
  startHeroRotation();

  // Ticker
  fillTicker(items.slice(0, 10));

  // Grids
  fillGrid("latestGrid", items.filter(x => x.section === "LATEST").slice(0, 9));
  fillGrid("realGrid", items.filter(x => x.section === "SPORTS").slice(0, 9));
  fillGrid("memeGrid", items.filter(x => x.section === "MEME").slice(0, 9));

  // Tabs
  setupTabs(items);

  // Footer year
  const y = qs("year");
  if (y) y.textContent = String(new Date().getFullYear());
}

init().catch(console.error);

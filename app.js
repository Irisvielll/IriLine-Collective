// =========================================================
// IriLine Collective — APP JS (CLEAN BUILD)
// Uses:
// - data/live.json
// - data/archive.json
// Matches index.html EXACTLY
// =========================================================

// --------------------
// CONFIG
// --------------------
const LIVE_URL = "data/live.json";
const ARCHIVE_URL = "data/archive.json";

const HERO_ROTATE_MS = 9000;
const HERO_FADE_MS = 450;
const HERO_SOURCES = ["LATEST", "SPORTS", "MEME"];

// --------------------
// HELPERS
// --------------------
function qs(id) {
  return document.getElementById(id);
}

function timeAgo(iso) {
  if (!iso) return "";
  const diff = Math.floor((Date.now() - new Date(iso)) / 1000);
  if (diff < 60) return "Just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

async function loadJSON(url) {
  const r = await fetch(url, { cache: "no-store" });
  if (!r.ok) throw new Error(`Failed to load ${url}`);
  return r.json();
}
function uniqueByImage(items) {
  const seen = new Set();
  return items.filter(item => {
    if (!item.image || seen.has(item.image)) return false;
    seen.add(item.image);
    return true;
  });
}

// --------------------
// HERO
// --------------------
let heroPool = [];
let heroIndex = 0;
let heroTimer = null;

function setHero(item) {
  qs("heroCategory").textContent =
    item.sectionLabel || item.category || item.type || "FEATURE";
  qs("heroTitle").textContent = item.title || "";
  qs("heroDek").textContent = item.dek || "";
  qs("heroLink").href = `article.html?id=${encodeURIComponent(item.id)}`;

  if (item.image) {
    qs("hero").style.backgroundImage =
      `linear-gradient(90deg, rgba(15,15,15,.85), rgba(15,15,15,.4)), url("${item.image}")`;
  }
}

function fadeSwapHero(next) {
  const hero = qs("hero");
  hero.style.opacity = "0";
  hero.style.transform = "scale(1.02)";

  setTimeout(() => {
    setHero(next);
    hero.style.opacity = "1";
    hero.style.transform = "scale(1)";
  }, HERO_FADE_MS);
}

function pickHeroPool(items) {
  const grouped = {};
  HERO_SOURCES.forEach(s => (grouped[s] = []));

  items.forEach(i => {
    if (grouped[i.section]) grouped[i.section].push(i);
  });

  const pool = [];
  HERO_SOURCES.forEach(s => {
    grouped[s]
      .sort((a, b) => (b.publishedAt || "").localeCompare(a.publishedAt || ""))
      .slice(0, 2)
      .forEach(x => pool.push(x));
  });

  return pool.length ? pool : items.slice(0, 5);
}

function startHeroRotation() {
  clearInterval(heroTimer);
  heroTimer = setInterval(() => {
    heroIndex = (heroIndex + 1) % heroPool.length;
    fadeSwapHero(heroPool[heroIndex]);
  }, HERO_ROTATE_MS);
}

// --------------------
// CARDS
// --------------------
function buildCard(item) {
  const card = document.createElement("div");
  card.className = "card card--withThumb";

  const thumb = document.createElement("div");
  thumb.className = "card__thumb";
  thumb.style.backgroundImage = `url("${item.image || ""}")`;

  const right = document.createElement("div");

  const meta = document.createElement("div");
  meta.className = "card__meta";

  if (
    item.publishedAt &&
    Date.now() - new Date(item.publishedAt) < 30 * 60 * 1000
  ) {
    const br = document.createElement("span");
    br.className = "pill pill--breaking";
    br.textContent = "BREAKING";
    meta.appendChild(br);
  }

  const type = document.createElement("span");
  type.className = "pill " + (item.type === "MEME" ? "pill--meme" : "");
  type.textContent = item.type;

  const cat = document.createElement("span");
  cat.className = "pill pill--muted";
  cat.textContent = item.category || "GENERAL";

  const time = document.createElement("span");
  time.className = "card__time";
  time.textContent = timeAgo(item.publishedAt);

  meta.append(type, cat, time);

  const title = document.createElement("h3");
  title.className = "card__title";
  title.textContent = item.title;

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

// --------------------
// GRIDS + TICKER
// --------------------
function fillGrid(id, items) {
  const grid = qs(id);
  const empty = grid.parentElement.querySelector(".empty-state");
  grid.innerHTML = "";

  if (!items.length) {
    empty.hidden = false;
    return;
  }
  empty.hidden = true;
  items.forEach(i => grid.appendChild(buildCard(i)));
}

function fillTicker(items) {
  const track = qs("tickerTrack");
  track.innerHTML = "";

  [...items, ...items].forEach(i => {
    const node = document.createElement("div");
    node.className = "ticker__item";

    const pill = document.createElement("span");
    pill.className = "ticker__pill";
    pill.textContent = `${i.type} • ${i.category || "GENERAL"}`;

    const a = document.createElement("a");
    a.className = "ticker__link";
    a.href = `article.html?id=${encodeURIComponent(i.id)}`;
    a.textContent = i.title;

    node.append(pill, a);
    track.appendChild(node);
  });
}

// --------------------
// TABS
// --------------------
function setupTabs(items) {
  const tabs = document.querySelectorAll(".tab");
  const grid = qs("latestGrid");

  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      tabs.forEach(t => t.classList.remove("active"));
      tab.classList.add("active");

      const filtered = items.filter(i => i.section === tab.dataset.section);
      grid.style.opacity = "0";

      setTimeout(() => {
        grid.innerHTML = "";
        filtered.slice(0, 9).forEach(i => grid.appendChild(buildCard(i)));
        grid.style.opacity = "1";
      }, 180);
    });
  });
}

// --------------------
// INIT
// --------------------
async function init() {
  const live = await loadJSON(LIVE_URL);
  const items = live.items || [];

  heroPool = pickHeroPool(items);
  heroIndex = 0;
  setHero(heroPool[0]);
  startHeroRotation();

  fillTicker(items.slice(0, 10));

  fillGrid("latestGrid", items.filter(i => i.section === "LATEST").slice(0, 9));
  fillGrid("realGrid", items.filter(i => i.section === "SPORTS").slice(0, 9));
  fillGrid("memeGrid", items.filter(i => i.section === "MEME").slice(0, 9));

  setupTabs(items);

  qs("year").textContent = new Date().getFullYear();
}

init().catch(console.error);

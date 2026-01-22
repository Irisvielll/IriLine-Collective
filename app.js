// =========================================================
// IriLine Collective — APP JS
// - Loads hero
// - Builds ticker (constant shifting but readable pace)
// - Builds news grids
// - Rotates ads slowly
// =========================================================

let offset = 0;
const pageSize = 9;

function el(tag, className, html) {
  const x = document.createElement(tag);
  if (className) x.className = className;
  if (html !== undefined) x.innerHTML = html;
  return x;
}
// ==============================
// DATA SOURCES (GitHub Pages)
// ==============================
const LIVE_URL = "data/live.json";
const ARCHIVE_URL = "data/archive.json";

// Rotation settings
const HERO_ROTATE_MS = 9000;   // readable pace
const HERO_FADE_MS = 450;

// Keep hero rotating between these sections
const HERO_SOURCES = ["LATEST", "SPORTS", "MEME"];

// ==============================
// Helpers
// ==============================
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


function qs(id) { return document.getElementById(id); }

function safeText(x) { return (x ?? "").toString(); }

function setHero(item) {
  // You already have these IDs in index.html
  qs("heroCategory").textContent = safeText(item.sectionLabel || item.category || item.type || "FEATURE");
  qs("heroTitle").textContent = safeText(item.title);
  qs("heroDek").textContent = safeText(item.dek);
  qs("heroLink").href = `article.html?id=${encodeURIComponent(item.id)}`;

  // Optional: set a background image per hero story if your CSS supports it
  // Example: set CSS variable used by .hero background
  if (item.image) {
    qs("hero").style.backgroundImage =
      `linear-gradient(90deg, rgba(15,15,15,0.86) 0%, rgba(15,15,15,0.52) 55%, rgba(15,15,15,0.20) 100%), url("${item.image}")`;
  }
}

function fadeSwapHero(nextItem) {
  const hero = qs("hero");

  hero.style.transform = "scale(1.015)";
  hero.style.opacity = "0";

  setTimeout(() => {
    setHero(nextItem);
    hero.style.opacity = "1";
    hero.style.transform = "scale(1)";
  }, HERO_FADE_MS);
}

// =====================================================================================================================================================================================================================
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
  typePill.textContent = item.type;

  const catPill = document.createElement("span");
  catPill.className = "pill pill--muted";
  catPill.textContent = item.category || item.sectionLabel || "GENERAL";

  meta.append(typePill, catPill);

  const time = document.createElement("span");
time.className = "card__time";
time.textContent = timeAgo(item.publishedAt);
meta.appendChild(time);
.card__time{
  margin-left: auto;
  font-size: 11px;
  opacity: 0.65;
  font-weight: 700;
}

  const title = document.createElement("h3");
  title.className = "card__title";
  title.textContent = item.title;

  const dek = document.createElement("p");
  dek.className = "card__dek";
  dek.textContent = item.dek;

  const link = document.createElement("a");
  link.className = "card__link";
  link.href = `article.html?id=${encodeURIComponent(item.id)}`;
  link.textContent = "Open story →";

  right.append(meta, title, dek, link);

  card.append(thumb, right);
  return card;
}


function fillGrid(gridId, items) {
  const grid = document.getElementById(gridId);
  if (!grid) return;
  grid.innerHTML = "";
  items.forEach(i => grid.appendChild(buildCard(i)));
}

function fillTicker(items) {
  const track = document.getElementById("tickerTrack");
  if (!track) return;
  track.innerHTML = "";

  // duplicate list for continuous scroll
  const doubled = items.concat(items);

  doubled.forEach(item => {
    const node = document.createElement("div");
    node.className = "ticker__item";

    const pill = document.createElement("span");
    pill.className = "ticker__pill";
    pill.textContent = `${item.type} • ${item.category || item.sectionLabel || "GENERAL"}`;

    const a = document.createElement("a");
    a.className = "ticker__link";
    a.href = `article.html?id=${encodeURIComponent(item.id)}`;
    a.textContent = item.title;

    node.append(pill, a);
    track.appendChild(node);
  });
}

// ==============================
// Main init
// ==============================
let liveData = null;
let heroPool = [];
let heroIndex = 0;
let heroTimer = null;

async function loadJSON(url) {
  const r = await fetch(url, { cache: "no-store" });
  if (!r.ok) throw new Error(`Failed: ${url}`);
  return await r.json();
}

function pickHeroPool(items) {
  const bySection = {};
  HERO_SOURCES.forEach(s => (bySection[s] = []));

  items.forEach(it => {
    if (bySection[it.section]) bySection[it.section].push(it);
  });

  // pick up to 2 from each section, newest first
  const pool = [];
  HERO_SOURCES.forEach(s => {
    bySection[s]
      .sort((a,b) => (b.publishedAt || "").localeCompare(a.publishedAt || ""))
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

async function init() {
  // Load live + archive==========================================================================================================================
  liveData = await loadJSON(LIVE_URL);
  const items = liveData.items || [];

  // Fill hero & ticker
  heroPool = pickHeroPool(items);
  heroIndex = 0;
  setHero(heroPool[heroIndex]);
  startHeroRotation();

  // Ticker uses top 10 newest
  fillTicker(items.slice(0, 10));

  // Fill sections (you can rename Not-So-Serious News label in HTML)
  fillGrid("latestGrid", items.filter(x => x.section === "LATEST").slice(0, 9));
  fillGrid("realGrid", items.filter(x => x.section === "LATEST").slice(0, 9));
  fillGrid("memeGrid", items.filter(x => x.section === "MEME").slice(0, 9));

  // Archive
  const archive = await loadJSON(ARCHIVE_URL);
  fillGrid("archiveGrid", (archive.items || []).slice(0, 12));

  // Year
  const y = document.getElementById("year");
  if (y) y.textContent = String(new Date().getFullYear());
}

init().catch(err => console.error(err));
}
function makeCard(a) {
  const card = el("div", "card");

  // ===== LABELS for easy edits =====
  // card meta pills: REAL/MEME + category
  const meta = el("div", "card__meta");
  const typePill = el("span", "pill " + (a.type === "MEME" ? "pill--meme" : ""), a.type || "REAL");
  const catPill  = el("span", "pill pill--muted", a.category || "GENERAL");
  meta.appendChild(typePill);
  meta.appendChild(catPill);

  const title = el("h3", "card__title");
  title.textContent = a.title || "";

  const dek = el("p", "card__dek");
  dek.textContent = a.dek || "";

  const link = el("a", "card__link");
  link.href = `article.html?id=${encodeURIComponent(a.id)}`;
  link.textContent = "Open story →";

  card.appendChild(meta);
  card.appendChild(title);
  card.appendChild(dek);
  card.appendChild(link);

  return card;
}

function addTickerItem(track, a) {
  const item = el("div", "ticker__item");
  const pill = el("span", "ticker__pill", (a.type || "REAL") + " • " + (a.category || "GENERAL"));

  const link = el("a", "ticker__link");
  link.href = `article.html?id=${encodeURIComponent(a.id)}`;
  link.textContent = a.title || "";

  item.appendChild(pill);
  item.appendChild(link);
  track.appendChild(item);
}

async function loadHero() {
  // Load some news and pick hero=true, else fallback first
  const res = await fetch(`/api/news?offset=0&limit=50`);
  const items = await res.json();

  let hero = items.find(x => x.hero === true) || items[0];
  if (!hero) return;

  document.getElementById("heroCategory").textContent = hero.category || "FEATURE";
  document.getElementById("heroTitle").textContent = hero.title || "";
  document.getElementById("heroDek").textContent = hero.dek || "";
  document.getElementById("heroLink").href = `article.html?id=${encodeURIComponent(hero.id)}`;
}

async function buildTicker() {
  const track = document.getElementById("tickerTrack");
  const res = await fetch(`/api/news?offset=0&limit=20`);
  const items = await res.json();

  // Build once
  items.forEach(a => addTickerItem(track, a));

  // Duplicate so the CSS scroll looks continuous (no gap)
  items.forEach(a => addTickerItem(track, a));
}

async function loadAds() {
  const res = await fetch(`/api/ads`);
  const ads = await res.json();

  const top = ads.topAds || [];
  const rentals = ads.rentalAds || [];

  // Slow rotation (readable)
  let topIdx = 0;
  let rentIdx = 0;

  function renderAd(targetId, ad) {
    const wrap = document.getElementById(targetId);
    wrap.innerHTML = "";

    const t = el("h4", "adCard__title");
    t.textContent = ad.title || "Ad";

    const p = el("p", "adCard__text");
    p.textContent = ad.text || "";

    const a = el("a", "adCard__link");
    a.href = ad.link || "#";
    a.textContent = "Learn more →";

    wrap.appendChild(t);
    wrap.appendChild(p);
    wrap.appendChild(a);
  }

  if (top.length) renderAd("adTop", top[topIdx]);
  if (rentals.length) renderAd("adRentals", rentals[rentIdx]);

  // Rotate slowly
  setInterval(() => {
    if (!top.length) return;
    topIdx = (topIdx + 1) % top.length;
    renderAd("adTop", top[topIdx]);
  }, 8500);

  setInterval(() => {
    if (!rentals.length) return;
    rentIdx = (rentIdx + 1) % rentals.length;
    renderAd("adRentals", rentals[rentIdx]);
  }, 10000);
}

async function loadNewsBatch() {
  const res = await fetch(`/api/news?offset=${offset}&limit=${pageSize}`);
  const items = await res.json();
  offset += items.length;

  const latestGrid = document.getElementById("latestGrid");
  const realGrid   = document.getElementById("realGrid");
  const memeGrid   = document.getElementById("memeGrid");
  const archGrid   = document.getElementById("archiveGrid");

  items.forEach(a => {
    // Latest always gets it
    latestGrid.appendChild(makeCard(a));

    // Type-specific sections
    if (a.type === "MEME") memeGrid.appendChild(makeCard(a));
    else realGrid.appendChild(makeCard(a));

    // Archive gets everything too
    archGrid.appendChild(makeCard(a));
  });
}

function setupLoadMore() {
  const btn = document.getElementById("loadMoreBtn");
  btn.addEventListener("click", loadNewsBatch);
}

function setYear() {
  document.getElementById("year").textContent = String(new Date().getFullYear());
}

async function init() {
  setYear();
  await loadHero();
  await buildTicker();
  await loadAds();
  await loadNewsBatch();
  setupLoadMore();
}

init();
// Tab switch function
function setupTabs(items) {
  const tabs = document.querySelectorAll(".tab");
  const grid = document.getElementById("latestGrid");

  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      tabs.forEach(t => t.classList.remove("active"));
      tab.classList.add("active");

      const section = tab.dataset.section;
      const filtered = items.filter(i => i.section === section);

      grid.style.opacity = "0";  // fade out current grid
      setTimeout(() => {
        grid.innerHTML = "";
        filtered.slice(0, 9).forEach(i => grid.appendChild(buildCard(i)));
        grid.style.opacity = "1";  // fade back in
      }, 180);  // Small delay to allow opacity change
    });
  });
}

setupTabs(items);

fetch("data/live.json")
  .then(response => response.json())
  .then(liveData => {
    const heroItems = liveData.items.filter(i =>
      ["LATEST", "SPORTS", "MEME"].includes(i.section)
    );

    let heroIndex = 0;

    function rotateHero() {
      const item = heroItems[heroIndex % heroItems.length];
      renderHero(item);
      heroIndex++;
    }

    rotateHero();
    setInterval(rotateHero, 3 * 60 * 60 * 1000); // every 3 hours
  });

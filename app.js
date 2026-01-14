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


/*
 * Homepage holographic card.
 * A small, dependency-free re-implementation of the pointer-tilt + holo-foil
 * interaction from pokemon-cards-css (GPL-3.0, © 2022 Simon Goellner
 * @simeydotme), as used on TonyCrane's note homepage. Ported from that
 * project's src/lib/components/Card.svelte + src/lib/helpers/Math.js.
 *
 * Renders ONE "rare secret" card into #app. Config comes from #app data-*:
 *   data-card-img    front image URL (pass via Jinja `| url` for portability)
 *   data-card-rarity defaults to "rare secret"
 * No pokemon database, no hardcoded paths, no click-to-zoom/orientation.
 */

// ---- math helpers (from Math.js) ----
const round = (v, p = 3) => parseFloat(v.toFixed(p));
const clamp = (v, min = 0, max = 100) => Math.min(Math.max(v, min), max);
const adjust = (v, fromMin, fromMax, toMin, toMax) =>
  round(toMin + ((toMax - toMin) * (v - fromMin)) / (fromMax - fromMin));

// ---- minimal spring (per-frame integrator, matches svelte/motion feel) ----
function makeSpring(initial, opts = {}) {
  const settings = { stiffness: 0.066, damping: 0.25, precision: 0.01, ...opts };
  const cur = { ...initial };
  const tgt = { ...initial };
  const vel = {};
  for (const k in initial) vel[k] = 0;
  return {
    value: cur,
    settings,
    set(next, { hard = false } = {}) {
      Object.assign(tgt, next);
      if (hard) {
        Object.assign(cur, tgt);
        for (const k in vel) vel[k] = 0;
      }
    },
    tick() {
      let moving = false;
      for (const k in tgt) {
        const delta = tgt[k] - cur[k];
        const accel = settings.stiffness * delta - settings.damping * vel[k];
        vel[k] += accel;
        if (Math.abs(vel[k]) < settings.precision && Math.abs(delta) < settings.precision) {
          cur[k] = tgt[k];
          vel[k] = 0;
        } else {
          cur[k] += vel[k];
          moving = true;
        }
      }
      return moving;
    },
  };
}

function initCard() {
  const app = document.getElementById("app");
  if (!app) return;

  const imgDark = app.dataset.cardImg || "";
  const imgLight = app.dataset.cardImgLight || imgDark;
  const rarity = (app.dataset.cardRarity || "rare secret").toLowerCase();

  // ---- build DOM ----
  const card = document.createElement("div");
  card.className = "card interactive loading";
  card.dataset.rarity = rarity;
  card.innerHTML =
    '<div class="card__translater">' +
      '<div class="card__rotator">' +
        '<div class="card__front">' +
          '<img alt="Vigilux\'s Notebook holographic card" />' +
          '<div class="card__shine"></div>' +
          '<div class="card__glare"></div>' +
        "</div>" +
      "</div>" +
    "</div>";
  app.appendChild(card);

  const rotator = card.querySelector(".card__rotator");
  const frontImg = card.querySelector(".card__front img");
  frontImg.addEventListener("load", () => card.classList.remove("loading"));
  // Pick the card art matching Material's colour scheme ("slate" = dark art,
  // "default" = light art) and swap it when the user toggles the theme.
  const pickImg = () =>
    document.body.getAttribute("data-md-color-scheme") === "slate" ? imgDark : imgLight;
  const applyImg = () => {
    const src = pickImg();
    if (frontImg.getAttribute("src") !== src) frontImg.src = src;
  };
  applyImg();
  if (frontImg.complete) card.classList.remove("loading");
  new MutationObserver(applyImg).observe(document.body, {
    attributes: true,
    attributeFilter: ["data-md-color-scheme"],
  });

  // ---- springs ----
  const springRotate = makeSpring({ x: 0, y: 0 });
  const springGlare = makeSpring({ x: 50, y: 50, o: 0 });
  const springBg = makeSpring({ x: 50, y: 50 });
  const INTERACT = { stiffness: 0.066, damping: 0.25 };
  const SNAP = { stiffness: 0.01, damping: 0.06 };
  const SHOWCASE = { stiffness: 0.02, damping: 0.5 };
  const applySettings = (s) => {
    Object.assign(springRotate.settings, s);
    Object.assign(springGlare.settings, s);
    Object.assign(springBg.settings, s);
  };

  // ---- rAF render loop (runs only while animating) ----
  let rafId = null;
  const render = () => {
    const r = springRotate.value;
    const g = springGlare.value;
    const b = springBg.value;
    const fromCenter = clamp(
      Math.sqrt((g.y - 50) * (g.y - 50) + (g.x - 50) * (g.x - 50)) / 50,
      0,
      1
    );
    card.style.cssText =
      "--pointer-x:" + g.x + "%;" +
      "--pointer-y:" + g.y + "%;" +
      "--pointer-from-center:" + fromCenter + ";" +
      "--pointer-from-top:" + g.y / 100 + ";" +
      "--pointer-from-left:" + g.x / 100 + ";" +
      "--card-opacity:" + g.o + ";" +
      "--rotate-x:" + r.x + "deg;" +
      "--rotate-y:" + r.y + "deg;" +
      "--background-x:" + b.x + "%;" +
      "--background-y:" + b.y + "%;";
  };
  const loop = () => {
    const moving = [springRotate.tick(), springGlare.tick(), springBg.tick()].some(Boolean);
    render();
    rafId = moving ? requestAnimationFrame(loop) : null;
  };
  const kick = () => {
    if (rafId === null) rafId = requestAnimationFrame(loop);
  };

  // ---- showcase intro (cute load animation) ----
  let showcaseInterval, showcaseStart, showcaseEnd;
  let showcaseRunning = true;
  const endShowcase = () => {
    if (!showcaseRunning) return;
    clearTimeout(showcaseStart);
    clearTimeout(showcaseEnd);
    clearInterval(showcaseInterval);
    showcaseRunning = false;
  };

  // ---- interaction ----
  const interactEnd = (delay = 500) => {
    setTimeout(() => {
      applySettings(SNAP);
      springRotate.set({ x: 0, y: 0 });
      springGlare.set({ x: 50, y: 50, o: 0 });
      springBg.set({ x: 50, y: 50 });
      card.classList.remove("interacting");
      kick();
    }, delay);
  };

  const interact = (e) => {
    endShowcase();
    applySettings(INTERACT);
    card.classList.add("interacting");
    const rect = rotator.getBoundingClientRect();
    const absolute = { x: e.clientX - rect.left, y: e.clientY - rect.top };
    const percent = {
      x: clamp(round((100 / rect.width) * absolute.x)),
      y: clamp(round((100 / rect.height) * absolute.y)),
    };
    const center = { x: percent.x - 50, y: percent.y - 50 };
    springBg.set({
      x: adjust(percent.x, 0, 100, 37, 63),
      y: adjust(percent.y, 0, 100, 33, 67),
    });
    springRotate.set({ x: round(-(center.x / 3.5)), y: round(center.y / 3.5) });
    springGlare.set({ x: round(percent.x), y: round(percent.y), o: 1 });
    kick();
  };

  rotator.addEventListener("pointermove", interact);
  rotator.addEventListener("pointerleave", () => interactEnd());

  showcaseStart = setTimeout(() => {
    card.classList.add("interacting");
    applySettings(SHOWCASE);
    let r = 0;
    showcaseInterval = setInterval(() => {
      r += 0.05;
      springRotate.set({ x: Math.sin(r) * 25, y: Math.cos(r) * 25 });
      springGlare.set({ x: 55 + Math.sin(r) * 55, y: 55 + Math.cos(r) * 55, o: 0.8 });
      springBg.set({ x: 20 + Math.sin(r) * 20, y: 20 + Math.cos(r) * 20 });
      kick();
    }, 20);
    showcaseEnd = setTimeout(() => {
      clearInterval(showcaseInterval);
      interactEnd(0);
    }, 4000);
  }, 2000);

  render();
}

if (document.readyState !== "loading") initCard();
else document.addEventListener("DOMContentLoaded", initCard);

/*
 * Homepage holographic card interaction — original work for Vigilux's Notebook.
 *
 * Pointer position -> spring-smoothed CSS custom properties consumed by
 * card-holo.css. Includes a small original spring integrator and a brief
 * "showcase" shimmer on first load. No third-party code.
 */
(function () {
  "use strict";

  var card = document.getElementById("app");
  if (!card || !card.classList.contains("holo-card")) return;

  var reduce = window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---- minimal spring: v chases target with velocity, stiffness & retention ---- */
  function Spring(value, stiffness, retention) {
    this.v = value; this.target = value; this.vel = 0;
    this.k = stiffness; this.r = retention;
  }
  Spring.prototype.step = function () {
    this.vel = (this.vel + (this.target - this.v) * this.k) * this.r;
    this.v += this.vel;
    return Math.abs(this.vel) > 0.0004 || Math.abs(this.target - this.v) > 0.0004;
  };

  var K = 0.13, R = 0.78;                       // lively but settles
  var rx = new Spring(0, K, R), ry = new Spring(0, K, R);
  var px = new Spring(50, K, R), py = new Spring(50, K, R);
  var op = new Spring(0, 0.10, 0.80);
  var raf = null;

  function render() {
    var moving = rx.step() | ry.step() | px.step() | py.step() | op.step();
    var cx = px.v, cy = py.v;
    var pfc = Math.min(Math.sqrt((cx - 50) * (cx - 50) + (cy - 50) * (cy - 50)) / 50, 1);
    var s = card.style;
    s.setProperty("--rx", rx.v.toFixed(2) + "deg");
    s.setProperty("--ry", ry.v.toFixed(2) + "deg");
    s.setProperty("--px", cx.toFixed(2) + "%");
    s.setProperty("--py", cy.toFixed(2) + "%");
    s.setProperty("--pfc", pfc.toFixed(3));
    s.setProperty("--op", op.v.toFixed(3));
    s.setProperty("--scale", (1 + op.v * 0.05).toFixed(4));
    raf = moving ? requestAnimationFrame(render) : null;
  }
  function kick() { if (raf === null) raf = requestAnimationFrame(render); }

  var MAX = reduce ? 5 : 16;                    // max tilt in degrees
  function fromPointer(e) {
    var r = card.getBoundingClientRect();
    if (!r.width) return;
    var x = (e.clientX - r.left) / r.width;
    var y = (e.clientY - r.top) / r.height;
    x = x < 0 ? 0 : x > 1 ? 1 : x;
    y = y < 0 ? 0 : y > 1 ? 1 : y;
    px.target = x * 100; py.target = y * 100;
    ry.target = (x - 0.5) * 2 * MAX;           // rotateY
    rx.target = (0.5 - y) * 2 * MAX;           // rotateX
    op.target = 1;
    kick();
  }

  card.addEventListener("pointermove", function (e) {
    endShowcase();
    card.classList.add("is-active");
    fromPointer(e);
  });
  card.addEventListener("pointerleave", function () {
    card.classList.remove("is-active");
    px.target = 50; py.target = 50; rx.target = 0; ry.target = 0; op.target = 0;
    kick();
  });

  /* ---- brief showcase shimmer on first load (skipped for reduced motion) ---- */
  var show = null;
  function endShowcase() {
    if (!show) return;
    clearInterval(show.iv); clearTimeout(show.end);
    show = null;
  }
  if (!reduce) {
    var startTimer = setTimeout(function () {
      card.classList.add("is-active");
      var t = 0;
      op.target = 0.9;
      var iv = setInterval(function () {
        t += 0.05;
        px.target = 50 + Math.sin(t) * 46;
        py.target = 50 + Math.cos(t * 0.9) * 42;
        ry.target = Math.sin(t) * 13;
        rx.target = Math.cos(t * 0.9) * 11;
        kick();
      }, 24);
      var end = setTimeout(function () {
        endShowcase();
        card.classList.remove("is-active");
        px.target = 50; py.target = 50; rx.target = 0; ry.target = 0; op.target = 0;
        kick();
      }, 2600);
      show = { iv: iv, end: end };
    }, 900);
    card.addEventListener("pointerenter", function () { clearTimeout(startTimer); }, { once: true });
  }
})();

/*
 * Homepage holographic card interaction.
 * Written from scratch for Vigilux's Notebook — original work, no third-party code.
 * Tracks the pointer over #app.holo-card and drives the CSS custom properties
 * consumed by card-holo.css. Eased return-to-rest is handled by CSS transitions.
 */
(function () {
  "use strict";
  var card = document.getElementById("app");
  if (!card || !card.classList.contains("holo-card")) return;

  var MAX_TILT = 11; // degrees
  var ticking = false;
  var last = null;

  function apply() {
    ticking = false;
    if (!last) return;
    var r = card.getBoundingClientRect();
    if (!r.width || !r.height) return;
    var x = (last.clientX - r.left) / r.width;
    var y = (last.clientY - r.top) / r.height;
    x = x < 0 ? 0 : x > 1 ? 1 : x;
    y = y < 0 ? 0 : y > 1 ? 1 : y;
    // tilt the card toward the pointer
    card.style.setProperty("--holo-ry", ((x - 0.5) * 2 * MAX_TILT).toFixed(2) + "deg");
    card.style.setProperty("--holo-rx", ((0.5 - y) * 2 * MAX_TILT).toFixed(2) + "deg");
    card.style.setProperty("--holo-mx", (x * 100).toFixed(1) + "%");
    card.style.setProperty("--holo-my", (y * 100).toFixed(1) + "%");
    card.style.setProperty("--holo-op", "1");
  }

  card.addEventListener("pointermove", function (e) {
    last = e;
    card.classList.add("is-interacting");
    if (!ticking) {
      ticking = true;
      requestAnimationFrame(apply);
    }
  });

  card.addEventListener("pointerleave", function () {
    card.classList.remove("is-interacting");
    card.style.setProperty("--holo-rx", "0deg");
    card.style.setProperty("--holo-ry", "0deg");
    card.style.setProperty("--holo-mx", "50%");
    card.style.setProperty("--holo-my", "50%");
    card.style.setProperty("--holo-op", "0");
  });
})();

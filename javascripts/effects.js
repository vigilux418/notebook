/*
 * 装饰性粒子连线背景（lines.js）的加载器。
 * - 尊重用户的 prefers-reduced-motion：偏好减少动效时不加载，节省 CPU / 电量。
 * - instant navigation 友好：extra_javascript 中的脚本会在每次软导航后被重放，
 *   故用 window 级守卫保证外部 lines.js「整站仅注入一次」——它生成的 canvas 是
 *   position:fixed，本就跨页存活，无需（也不应）重复注入，否则 canvas 与 rAF 循环层层叠加。
 */
(function () {
  if (window.__linesInjected) return;

  var reduce =
    window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduce) return;

  window.__linesInjected = true;

  var s = document.createElement("script");
  s.src =
    "https://cdn.jsdelivr.net/gh/vigilux418/downloads@main/special_effects/lines.js";
  s.defer = true;
  (document.body || document.documentElement).appendChild(s);
})();

/*
 * 装饰性粒子连线背景（lines.js）的加载器。
 * - 尊重用户的 prefers-reduced-motion：偏好减少动效时不加载，节省 CPU / 电量。
 * - instant navigation 友好：extra_javascript 中的脚本会在每次软导航后被重放，
 *   故用 window 级守卫保证站点内 lines.js「整站仅注入一次」——它生成的 canvas 是
 *   position:fixed，本就跨页存活，无需（也不应）重复注入，否则 canvas 与 rAF 循环层层叠加。
 */
(function () {
  if (window.__linesInjected) return;

  var reduce =
    window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduce) return;

  window.__linesInjected = true;

  // lines.js 已收编进本仓库（docs/javascripts/lines.js，2026-07-21 起自维护）。
  // 由本脚本自身的 src 推导同目录 URL——无论当前页嵌套多深，MkDocs 都会为本脚本
  // 生成正确的相对路径，据此解析永远指向站点内的 lines.js，彻底摆脱 CDN 依赖。
  var self = document.currentScript;
  if (!self || !self.src) return;
  var s = document.createElement("script");
  s.src = new URL("lines.js", self.src).href;
  s.defer = true;
  (document.body || document.documentElement).appendChild(s);
})();

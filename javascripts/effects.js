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

  // 钉死在 downloads 仓库的 commit（bbc578d = 2025-09-04 main HEAD），
  // 避免 @main 浮动分支内容变化导致站点行为不可复现；升级 lines.js 时同步更新此 sha。
  var s = document.createElement("script");
  s.src =
    "https://cdn.jsdelivr.net/gh/vigilux418/downloads@bbc578d5146d3cfd206705fb8c8443a6756d39c1/special_effects/lines.js";
  s.defer = true;
  (document.body || document.documentElement).appendChild(s);
})();

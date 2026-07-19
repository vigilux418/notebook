/*
 * 装饰性粒子连线背景（lines.js）的加载器。
 * - 尊重用户的 prefers-reduced-motion：偏好减少动效时不加载，节省 CPU / 电量。
 * - 延迟(defer)注入，避免阻塞首屏渲染。
 * lines.js 会读取“最后一个 <script>”上的可选属性(zIndex/opacity/color/count)，
 * 此处不设自定义属性，沿用其默认值（与原全站直挂时一致）。
 */
(function () {
  var reduce =
    window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduce) return;

  var s = document.createElement("script");
  s.src =
    "https://cdn.jsdelivr.net/gh/vigilux418/downloads@main/special_effects/lines.js";
  s.defer = true;
  (document.body || document.documentElement).appendChild(s);
})();

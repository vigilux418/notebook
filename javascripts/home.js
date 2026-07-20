/*
 * 首页专属交互：打字标语(typed.js) + 站点运行时长 + 统计面板开关。
 *
 * 原先这些是 index.md 内联 <script>：先引外部 typed.js 再立刻 new Typed()。硬加载时
 * 外部脚本会阻塞后续内联脚本故正常；但 navigation.instant 软导航会重建脚本、外部脚本
 * 异步加载，内联抢跑 → "Typed is not defined"。且内联 setInterval 在离开首页后仍空转报错。
 *
 * 现改为：全局加载 + 订阅 document$，仅在首页(存在 #typed-des-zh)激活，幂等，切页回收。
 * typed.js 仍懒加载（只有首页才拉），保留原省流量意图。
 */

// —— 统计面板开关：被 index.md 的 [..](javascript:toggle_statistics();) 调用，全局仅定义一次 ——
window.toggle_statistics = function () {
  const el = document.getElementById("statistics");
  if (!el) return;
  const hidden = el.style.opacity === "0" || el.style.opacity === "";
  el.style.opacity = hidden ? "1" : "0";
};

// —— 懒加载 typed.js（整站仅注入一次，返回 Typed 构造器）——
// typed.js 已收编进本仓库（docs/javascripts/typed.umd.js，MIT © Matt Boldt）。
// import.meta.url 即本模块 URL，同目录解析——任意页面深度下都指向站点内文件。
let typedPromise = null;
function loadTyped() {
  if (window.Typed) return Promise.resolve(window.Typed);
  if (typedPromise) return typedPromise;
  typedPromise = new Promise((resolve, reject) => {
    const s = document.createElement("script");
    s.src = new URL("./typed.umd.js", import.meta.url).href;
    s.onload = () => resolve(window.Typed);
    s.onerror = () => { typedPromise = null; reject(new Error("typed.js load failed")); };
    document.body.appendChild(s);
  });
  return typedPromise;
}

// —— 打字标语：进首页初始化，离开则销毁；同一页重复 emit 幂等 ——
let typedInstance = null;
function manageTyping() {
  const el = document.getElementById("typed-des-zh");
  if (!el) {                       // 不在首页：回收旧实例
    if (typedInstance) { typedInstance.destroy(); typedInstance = null; }
    return;
  }
  if (typedInstance) return;       // 已初始化
  loadTyped().then((Typed) => {
    const target = document.getElementById("typed-des-zh");
    if (!target || typedInstance) return; // 加载期间可能已离开/已初始化
    typedInstance = new Typed(target, {
      strings: ["欢迎来到Vigilux的个人笔记本！(｡･∀･)ﾉﾞ"],
      typeSpeed: 50,
      backSpeed: 0,
      smartBackspace: true,
      loop: true,
    });
  }).catch(() => {});
}

// —— 站点运行时长：单一定时器，离开首页自动停止，避免空转报错 ——
const SITE_START = new Date("2025/08/30 00:00:00").getTime();
let clockTimer = null;
function renderClock() {
  const el = document.getElementById("web-time");
  if (!el) return false;
  let diff = Date.now() - SITE_START;
  const y = Math.floor(diff / (365 * 24 * 3600 * 1000)); diff -= y * 365 * 24 * 3600 * 1000;
  const d = Math.floor(diff / (24 * 3600 * 1000));
  const h = Math.floor((diff / (3600 * 1000)) % 24);
  const m = Math.floor((diff / (60 * 1000)) % 60);
  const sp = '<span class="heti-spacing"> </span>';
  const tail = d + sp + "天" + sp + h + sp + "小时" + sp + m + sp + "分钟";
  el.innerHTML = (y === 0 ? "" : y + sp + "年" + sp) + tail;
  return true;
}
function manageClock() {
  if (clockTimer) { clearInterval(clockTimer); clockTimer = null; }
  if (!renderClock()) return;      // 不在首页则不启动
  clockTimer = setInterval(() => {
    if (!renderClock()) { clearInterval(clockTimer); clockTimer = null; }
  }, 60000);
}

// —— 每次（软）导航后驱动 ——
function onDoc() { manageTyping(); manageClock(); }
if (window.document$ && typeof window.document$.subscribe === "function") {
  window.document$.subscribe(onDoc);
} else if (document.readyState !== "loading") {
  onDoc();
} else {
  document.addEventListener("DOMContentLoaded", onDoc);
}

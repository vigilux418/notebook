/*
 * 重型引擎（MathJax）运行时懒加载器。
 *
 * 背景：站点曾用 Jinja `{% if 本页含公式 %}` 在构建期按页注入引擎，以免无公式/
 * 无图表的页面白拉整套引擎。但该做法与 navigation.instant 冲突——软导航是 XHR 换
 * <body> 局部，不会重新执行新页 <head>/<script> 里的条件注入，故换页后引擎不加载。
 *
 * 解法：把「要不要加载」的判断从构建期搬到运行期。订阅 document$（每次软导航都触发），
 * 检测当前页是否真的含 .arithmatex，需要时才注入引擎，且整站仅注入一次。
 * 既保留原有省流量优化，又兼容 instant navigation。
 *
 * Mermaid 另由 mermaid.mjs 处理（Material 内置 loader 硬加载 → mermaid.mjs 软导航重渲染）。
 */

const scriptCache = new Map();
function loadScript(src, attrs = {}) {
  if (scriptCache.has(src)) return scriptCache.get(src);
  const p = new Promise((resolve, reject) => {
    const s = document.createElement("script");
    s.src = src;
    for (const [k, v] of Object.entries(attrs)) s.setAttribute(k, v);
    s.onload = () => resolve();
    s.onerror = () => reject(new Error("failed to load " + src));
    document.body.appendChild(s);
  });
  scriptCache.set(src, p);
  return p;
}

let mathjaxRequested = false;

function ensureEngines() {
  if (!mathjaxRequested && document.querySelector(".arithmatex")) {
    mathjaxRequested = true;
    loadScript("https://unpkg.com/mathjax@3/es5/tex-mml-chtml.js").catch(() => {
      mathjaxRequested = false;
    });
  }
}

if (window.document$ && typeof window.document$.subscribe === "function") {
  window.document$.subscribe(ensureEngines);
} else if (document.readyState !== "loading") {
  ensureEngines();
} else {
  document.addEventListener("DOMContentLoaded", ensureEngines);
}

/*
 * Mermaid 图表渲染器——软导航兼容版。
 *
 * 正常流程：Material 内置 loader（custom_fence）在硬加载 mermaid 页面时从 unpkg 注入
 * mermaid 并渲染。本脚本只负责补刀——若 Material 尚未加载（软导航首次遇见 mermaid），
 * 则自行用经典 <script> 注入；每次软导航后调用 window.mermaid.run() 对当前页重渲染。
 */

const MERMAID_SRC = "https://unpkg.com/mermaid@11/dist/mermaid.min.js";
let loading = null;

function ensureMermaid() {
  if (window.mermaid) return Promise.resolve(window.mermaid);
  if (loading) return loading;
  loading = new Promise((resolve, reject) => {
    const s = document.createElement("script");
    s.src = MERMAID_SRC;
    s.onload = () => {
      if (window.mermaid && typeof window.mermaid.initialize === "function")
        window.mermaid.initialize({ startOnLoad: false, securityLevel: "loose" });
      resolve(window.mermaid);
    };
    s.onerror = () => { loading = null; reject(new Error("mermaid load failed")); };
    document.body.appendChild(s);
  });
  return loading;
}

function renderMermaid() {
  ensureMermaid()
    .then(() => {
      if (window.mermaid && typeof window.mermaid.run === "function") {
        const run = () => {
          try {
            window.mermaid.run({ querySelector: "pre.mermaid, .mermaid", suppressErrors: true });
          } catch (e) { /* suppressErrors 吞单图错误 */ }
        };
        run();
        setTimeout(run, 250);
      }
    })
    .catch(() => {});
}

if (window.document$ && typeof window.document$.subscribe === "function")
  window.document$.subscribe(renderMermaid);
if (document.readyState === "complete") renderMermaid();
else window.addEventListener("load", renderMermaid);

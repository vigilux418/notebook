import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
import elkLayouts from 'https://cdn.jsdelivr.net/npm/@mermaid-js/layout-elk@0/dist/mermaid-layout-elk.esm.min.mjs';

mermaid.registerLayoutLoaders(elkLayouts);
mermaid.initialize({
  startOnLoad: false,
  securityLevel: "loose",
  layout: "elk",
});

// Important: necessary to make it visible to Material for MkDocs
window.mermaid = mermaid;

// 实际触发渲染：把 <pre class="mermaid"> 代码块渲染为 SVG。
// （此前只 initialize、从不 run，导致全站图表根本不渲染——这是被本次修复的既有 bug。）
// mermaid.run() 是幂等的（已渲染节点带 data-processed 会被跳过），故多次触发安全。
// suppressErrors 让个别语法有误的图不影响其余图正常渲染。
const renderMermaid = () => {
  try {
    mermaid.run({ querySelector: "pre.mermaid, .mermaid", suppressErrors: true });
  } catch (e) {
    /* 逐图错误已由 suppressErrors 吞掉，这里兜底忽略偶发异常 */
  }
};

// 1) Material 的 document$：会重放当前文档给后订阅者，并在（未来若启用）instant
//    navigation 切页时重新触发——覆盖软导航场景。
if (window.document$ && typeof window.document$.subscribe === "function") {
  window.document$.subscribe(renderMermaid);
}
// 2) 首屏兜底：不依赖 document$ 的时序，用 window load 保证首次一定渲染。
if (document.readyState === "complete") {
  renderMermaid();
} else {
  window.addEventListener("load", renderMermaid);
}
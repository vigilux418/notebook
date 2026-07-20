// 一次性守卫：本脚本经 extra_javascript 全局加载；若 instant navigation 重放它，
// 顶层的 window.MathJax = {...} 会用「纯配置对象」覆盖已加载的引擎实例、并重复订阅。
// 故所有初始化只做一次；跨页重排交给 document$ 订阅（其本身对每次导航都会触发）。
if (!window.__mathjaxInit) {
  window.__mathjaxInit = true;

  window.MathJax = {
    tex: {
      inlineMath: [["\\(", "\\)"]],
      displayMath: [["\\[", "\\]"]],
      processEscapes: true,
      processEnvironments: true
    },
    options: {
      ignoreHtmlClass: ".*|",
      processHtmlClass: "arithmatex"
    }
  };

  // 每次（含 instant navigation 软导航）文档就绪后，对当前页公式重新排版。
  // 就绪守卫：引擎（tex-mml-chtml.js）是懒加载的，首个公式页由引擎自身首屏自动排版；
  // 此订阅只在引擎已就绪时才重排，避免早期 emit 时 MathJax.startup 未定义而报错。
  document$.subscribe(() => {
    if (!window.MathJax || typeof MathJax.typesetPromise !== "function") return;
    if (MathJax.startup && MathJax.startup.output) MathJax.startup.output.clearCache();
    MathJax.typesetClear();
    MathJax.texReset();
    MathJax.typesetPromise();
  });
}

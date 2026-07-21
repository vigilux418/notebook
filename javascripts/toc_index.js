/*
 * 分区索引目录（{{ BEGIN_TOC }} 生成的 .index-item-wrapper）的交互脚本。
 *
 * 逻辑改编自 TonyCrane/note 的模板内联脚本 (CC BY 4.0)，见 hooks/toc.py 顶部署名。
 * 本仓库开启 navigation.instant：内容区 <script> 每次软导航都会被重建重跑，若沿用
 * 原版“把时间戳 innerHTML 直接改写成 x days ago”的做法，重放时会把已渲染的文本
 * (“3 days ago”) 再当成时间戳解析 → 显示 56 years ago。故这里改为：
 *   1) 时间戳存放在 .item-actions[data-ts]（unix 秒），渲染永远从 data-ts 读，幂等；
 *   2) 折叠用事件委托挂到常驻 document 上，window 级守卫保证只挂一次，不累积监听器；
 *   3) 订阅 document$，每次（软）导航后对当前页所有目录重新渲染时间。
 * 与本仓库既有 toc.js / home.js 的写法保持一致。
 */

// —— 折叠：点击标题按钮，切换其后紧邻的 .content-item-wrapper 显隐 ——
function toggleFold(btn) {
  const titleWrapper = btn.closest(".title-wrapper");
  if (!titleWrapper) return;
  const content = titleWrapper.nextElementSibling;
  if (!content || !content.classList.contains("content-item-wrapper")) return;
  const caret = btn.querySelector(".toc-fold-caret");
  const collapsed = content.classList.toggle("toc-collapsed");
  if (caret) caret.style.transform = collapsed ? "rotate(-90deg)" : "rotate(0deg)";
}

// —— 相对时间：始终从 data-ts 读取，渲染到文本；重复调用结果一致（幂等）——
function renderRelativeTimes(root) {
  const now = Date.now();
  const nodes = (root || document).querySelectorAll(".item-actions[data-ts]");
  nodes.forEach((el) => {
    const ts = parseInt(el.getAttribute("data-ts"), 10);
    if (!ts) { el.textContent = ""; return; }
    const diff = now - ts * 1000;
    const mins = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    const months = Math.floor(diff / (30 * 86400000));
    const years = Math.floor(diff / (365 * 86400000));
    let text;
    if (years > 0) text = years + (years === 1 ? " year ago" : " years ago");
    else if (months > 0) text = months + (months === 1 ? " month ago" : " months ago");
    else if (days > 0) text = days + (days === 1 ? " day ago" : " days ago");
    else if (hours > 0) text = hours + (hours === 1 ? " hour ago" : " hours ago");
    else if (mins > 0) text = mins + (mins === 1 ? " minute ago" : " minutes ago");
    else text = "just now";
    el.textContent = text;
  });
}

// 每次（软）导航后：渲染当前页所有分区目录的相对时间。折叠是委托的、常驻的，无需重挂。
function onDoc() {
  renderRelativeTimes(document);
}

// —— 折叠事件委托：全局仅挂一次（软导航到的新页天然生效）——
if (!window.__tocIndexFoldHooked) {
  window.__tocIndexFoldHooked = true;
  document.addEventListener("click", (e) => {
    const btn = e.target.closest && e.target.closest(".toc-fold-btn");
    if (btn) toggleFold(btn);
  });
}

// —— 驱动：订阅 document$（全局仅订阅一次），无则退化到 DOMContentLoaded ——
if (window.document$ && typeof window.document$.subscribe === "function") {
  if (!window.__tocIndexSubscribed) {
    window.__tocIndexSubscribed = true;
    window.document$.subscribe(onDoc);
  }
} else if (document.readyState !== "loading") {
  onDoc();
} else {
  document.addEventListener("DOMContentLoaded", onDoc);
}

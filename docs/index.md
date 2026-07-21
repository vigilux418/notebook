---
hide: 
  - date
  - footer
  - feedback
  - navigation
  - toc
home: true
template: home.html
statistics: true
---

# <span class="brand-en">Vigilux</span><span class="brand-cn">的笔记本</span>
<!-- 打字标语由 docs/javascripts/home.js 驱动（全局加载 + 订阅 document$，兼容 instant navigation） -->
<span id="typed-des-zh"></span>

[:material-bulletin-board: 笔记思想](spirit.md) | 
[:material-chart-line: 站点统计](javascript:toggle_statistics();) | 
[:octicons-link-16: 友链](links.md)

<div id="statistics" style="opacity: 0">
<div class="stat-line"><span class="stat-k">页面总数</span><span class="stat-v">{{pages}}</span></div>
<div class="stat-line"><span class="stat-k">总字数</span><span class="stat-v">{{words}}</span></div>
<div class="stat-line"><span class="stat-k">代码块行数</span><span class="stat-v">{{codes}}</span></div>
<div class="stat-line"><span class="stat-k">网站运行时间</span><span class="stat-v" id="web-time"></span></div>
</div>

<!-- 运行时长与 toggle_statistics() 由 docs/javascripts/home.js 提供（幂等、切页回收定时器） -->
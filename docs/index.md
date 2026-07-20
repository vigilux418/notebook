---
hide: 
  - date
  - footer
  - feedback
  - navigation
  - toc
home: true
template: home.html
---

# Vigilux的笔记本
<!-- 打字标语由 docs/javascripts/home.js 驱动（全局加载 + 订阅 document$，兼容 instant navigation） -->
<span id="typed-des-zh"></span>

[:material-bulletin-board: 笔记思想](spirit.md) | 
[:material-chart-line: 站点统计](javascript:toggle_statistics();) | 
[:octicons-link-16: 友链](links.md)

<div id="statistics" style="max-width: 27em; border-color: #e3e3e3; opacity: 0; font-size: 75%">
页面总数：{{pages}} </br>
总字数：{{words}} </br>
代码块行数：{{codes}} <br>
网站运行时间：<span id="web-time"></span>
</div>

<!-- 运行时长与 toggle_statistics() 由 docs/javascripts/home.js 提供（幂等、切页回收定时器） -->
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

# Vigilux的笔记本
<script src="https://unpkg.com/typed.js@2.1.0/dist/typed.umd.js"></script>
<span id="typed-des-zh"></span>
<script>
  var typed = new Typed('#typed-des-zh', {
    strings: ['欢迎来到Vigilux的个人笔记本！(｡･∀･)ﾉﾞ'],
    typeSpeed: 50,
    backSpeed: 0,
    // cursorChar: '_',
    smartBackspace: true, // this is a default
    // fadeOut: true,
    // shuffle: true,
    loop: true
  });
</script>
[:material-bulletin-board: 笔记思想](spirit.md) | 
[:material-chart-line: 站点统计](javascript:toggle_statistics();) | 
[:octicons-link-16: 友链](links.md)

<div id="statistics" style="width: 27em; border-color: #e3e3e3; opacity: 0; font-size: 75%">
页面总数：{{pages}} </br>
总字数：{{words}} </br>
代码块行数：{{codes}} <br>
网站运行时间：<span id="web-time"></span>
</div>

<script>
function updateTime() {
    var date = new Date();
    var now = date.getTime();
    var startDate = new Date("2025/08/30 00:00:00");
    var start = startDate.getTime();
    var diff = now - start;
    var y, d, h, m;
    y = Math.floor(diff / (365 * 24 * 3600 * 1000));
    diff -= y * 365 * 24 * 3600 * 1000;
    d = Math.floor(diff / (24 * 3600 * 1000));
    h = Math.floor(diff / (3600 * 1000) % 24);
    m = Math.floor(diff / (60 * 1000) % 60);
    if (y == 0) {
        document.getElementById("web-time").innerHTML = d + "<span class=\"heti-spacing\"> </span>天<span class=\"heti-spacing\"> </span>" + h + "<span class=\"heti-spacing\"> </span>小时<span class=\"heti-spacing\"> </span>" + m + "<span class=\"heti-spacing\"> </span>分钟";
    } else {
        document.getElementById("web-time").innerHTML = y + "<span class=\"heti-spacing\"> </span>年<span class=\"heti-spacing\"> </span>" + d + "<span class=\"heti-spacing\"> </span>天<span class=\"heti-spacing\"> </span>" + h + "<span class=\"heti-spacing\"> </span>小时<span class=\"heti-spacing\"> </span>" + m + "<span class=\"heti-spacing\"> </span>分钟";
    }
    setTimeout(updateTime, 1000 * 60);
}
updateTime();
function toggle_statistics() {
    var statistics = document.getElementById("statistics");
    if (statistics.style.opacity == 0) {
        statistics.style.opacity = 1;
    } else {
        statistics.style.opacity = 0;
    }
}
</script>
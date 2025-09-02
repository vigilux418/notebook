---
comments: true
---

# MkDocs主题美化

## 添加友链

> 参考资料：[如何给MKdocs添加友链](https://wcowin.work/Mkdocs-Wcowin/blog/Mkdocs/linktech.html)

复制后在需要添加友链的.md 文件页面粘贴即可。
??? note "代码"
    === "页面"

        ```html hl_lines="82-90"
        <div class="post-body">
        <div id="links">
        <style>
        /* 友链容器样式 */
        .link-navigation {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
                gap: 1rem;
            max-width: 100%;
        }
        /* 通用卡片样式 */
        .card {
            width: 100%;
            max-width: 320px;
            height: 90px;
            font-size: 1rem;
            padding: 10px 20px;
            border-radius: 25px;
            transition: transform 0.15s, box-shadow 0.15s, background 0.15s;
            display: flex;
                align-items: center;
            color: #333;
            justify-self: center;
        }
        .card:hover {
            transform: translateY(0px) scale(1.05);
            background-color: rgba(68, 138, 255, 0.1);
            color: #040000;
        }
        .card a {
            border: none;
        }
        .card .ava {
            width: 3rem !important;
            height: 3rem !important;
            margin: 0 !important;
            margin-right: 1em !important;
            border-radius: 50%;
        }
        .card .card-header {
            font-style: italic;
            overflow: hidden;
            width: auto;
        }
        .card .card-header a {
            font-style: normal;
            color: #608DBD;
            font-weight: bold;
            text-decoration: none;
        }
        .card .card-header a:hover {
            color: #d480aa;
            text-decoration: none;
        }
        .card .card-header .info {
            font-style: normal;
            color: #706f6f;
            font-size: 14px;
            min-width: 0;
            overflow: visible;
            white-space: normal;
        }
        /* 小屏优化 */
        @media (max-width: 768px) {
            .link-navigation {
                grid-template-columns: 1fr;
                gap: 0.8rem;
            }
            .card {
                width: 100%;
                max-width: 100%;
                height: auto;
                min-height: 80px;
            }
            .card:hover {
                background-color: rgba(68, 138, 255, 0.1);
            }
        }
        </style>
        <div class="links-content">
        <div class="link-navigation">
            <div class="card">
                <img class="ava" src="https://avatars.githubusercontent.com/jaywhj" />
                <div class="card-header">
                    <div>
                        <a href="https://jaywhj.netlify.app/" target="_blank">极简主义</a>
                    </div>
                    <div class="info">文档即产品</div>
                </div>
            </div>
        </div>
        </div>
        </div>
        </div>
        ```
    
    === "卡片"
    
        ```html
        <div class="card">
          <img class="ava" src="{avatarurl}" />
          <div class="card-header">
            <div>
              <a href="{link}" target="_blank">{name}</a>
            </div>
            <div class="info">{description}</div>
          </div>
        </div>
        ```

## 网页圆角化设计

> 参考资料：[网页圆角化设计 - Mkdocs中文教程](https://wcowin.work/Mkdocs-Wcowin/blog/websitebeauty/yuanjiaohua.html)

利用覆盖样式表，在`mkdocs.yml`中引入`css`。
??? note "代码"

    ```css
        :root {
      --admonition-border-left-width: 0.2rem;
      --base-border-radius: 1rem;
      /* --card-hover-shadow: 0 0 0.2rem #ffffff40; */
    }
    
    /* 卡片圆角与悬浮阴影 */
    .md-typeset .grid.cards > ul > li,
    .md-typeset .md-button,
    .md-typeset table:not([class]) {
      border-radius: var(--base-border-radius);
    }
    .md-typeset .grid.cards > ul > li:hover {
      box-shadow: var(--card-hover-shadow);
    }
    
    /* 页脚社交图标高度 */
    .md-social__link svg {
      max-height: 1rem;
    }
    
    /* 搜索框及下拉结果圆角 */
    .md-search__form {
      border-radius: var(--base-border-radius);
    }
    
    [data-md-toggle="search"]:checked ~ .md-header .md-search__form {
      border-top-right-radius: var(--base-border-radius);
      border-top-left-radius: var(--base-border-radius);
    }
    
    [dir="ltr"] .md-search__output {
      border-bottom-right-radius: var(--base-border-radius);
      border-bottom-left-radius: var(--base-border-radius);
    }
    
    /* 可选：如需恢复代码块、警告框等样式，取消注释即可 */
    /*
    .highlight span.filename {
      border-bottom: none;
      border-radius: var(--base-border-radius);
      display: inline;
      font-family: var(--md-code-font-family);
      border-bottom-left-radius: 0;
      border-bottom-right-radius: 0;
      margin-bottom: 5px;
      text-align: center;
    }
    .highlight span.filename + pre > code,
    .md-typeset pre > code {
      border-radius: var(--base-border-radius);
      border-top-left-radius: 0;
    }
    .md-typeset .admonition {
      border-width: 0px;
      border-left-width: var(--admonition-border-left-width);
    }
    [dir="ltr"] .md-typeset blockquote {
      border-radius: 0.2rem;
      border-left-width: var(--admonition-border-left-width);
    }
    */
    
    /* 可选：博客相关样式，按需启用 */
    
    /* .md-post--excerpt {
      background-color: rgba(68,138,255,.1);
      box-shadow: 0 0 0 1rem rgba(68,138,255,.1);
      border-radius: var(--base-border-radius);
    }
    .md-post--excerpt .md-post__header {
      justify-content: left;
    }
    .md-post--excerpt .md-post__content > h2,
    .md-post__action {
      text-align: left;
    } */
    
    /* 让所有admonition（包括!!! tip）圆角化且更自然 */
    .md-typeset .admonition,
    .md-typeset details {
      border-radius: 1.5em;
      box-shadow: 0 2px 12px 0 rgba(60,60,60,0.07);
      transition: border-radius 0.4s cubic-bezier(.4,2,.6,1), box-shadow     0.3s;
      overflow: hidden;
    }
    ```

### 图片圆角化

在覆盖样式表中写入：

```css
img.img1 {
border-radius: 25px;
}
```

在`md`文件中使用：

```markdown
![image.png](https://s2.loli.net/2024/04/26/Czi9uAQhmbBlkfG.png){.img1}
```

### 按钮圆角化

```markdown
[Send Email :fontawesome-solid-paper-plane:](mailto:a3205767798@outlook.com){.md-button}
```

## 背景特效

> 参考资料：[背景特效](https://wcowin.work/Mkdocs-Wcowin/blog/websitebeauty/backgroud.html)

!!! note

    以下代码均在`docs/javascripts/extra.js`下复制粘贴

??? note "代码"

    === "雪花"
    
        ``` javascript
        const fps = 30;
        const mspf = Math.floor(1000 / fps) ; 
        
        let width = window.innerWidth ||                                 document.documentElement.clientWidth;
        let height = window.innerHeight || document.documentElement.clientHeight;
        let canvas;
        window.addEventListener('resize', () => {
          width = window.innerWidth || document.documentElement.clientWidth;
          height = window.innerHeight || document.documentElement.clientHeight;
          if (canvas) {
            canvas.width = width;
            canvas.height = height;
          }
        });
        
        let particles = [];
        let wind = [0, 0];
        let cursor = [0, 0];
        
        function velocity(r) {
          return 70 / r + 30;
        }
        
        function sine_component(h, a) {
          return [2 * Math.PI / h, Math.random() * a, Math.random() * 2 * Math.PI]; // [frequency, amplitude, phase]
        }
        
        function calc_sine(components, x) {
          let sum = 0;
          for (let i = 0; i < components.length; i++) {
            const [f, a, p] = components[i];
            sum += Math.sin(x * f + p) * a;
          }
          return sum;
        }
        
        function gen_particle() {
          let r = Math.random() * 4 + 1;
          return {
                    radius: r,
            x: Math.random() * width,
            y: -r,
            opacity: Math.random(),
            sine_components: [sine_component(height, 3), sine_component(height / 2, 2), sine_component(height / 5, 1), sine_component(height / 10, 0.5)],
          };
        }
        
        function update_pos(dt) {
          const n = particles.length;
          for (let i = 0; i < n; i++) {
            const v = velocity(particles[i].radius);
            particles[i].x += calc_sine(particles[i].sine_components, particles[i].y) * v / 5 * dt;
            particles[i].y += v * dt;
        
            // const dist = Math.hypot(particles[i].x - cursor[0], particles[i].y - cursor[1]) + 1;
            // particles[i].x += wind[0] * dt / dist
            // particles[i].y += wind[1] * dt / dist;
        
            if (particles[i].y - particles[i].radius > height) {
              particles[i] = gen_particle();  
            }
          }
        }
        
        let context_cache;
        function get_context() {
          if (context_cache)
            return context_cache;
        
          canvas = document.createElement('canvas');
          canvas.id = 'snow-canvas';
          canvas.width = width;
          canvas.height = height;
          canvas.style = 'position: fixed; top: 0; left: 0; overflow: hidden; pointer-events: none; z-index: 256;';
          if ((document.documentElement.dataset.darkreaderMode || "").startsWith('filter'))
            canvas.style.filter = 'invert(1)';
          document.body.appendChild(canvas);
        
          context_cache = canvas.getContext('2d');
          return context_cache;
        }
        
        function draw() {
          const ctx = get_context();
        
          ctx.clearRect(0, 0, width, height);
        
          const n = particles.length;
          for (let i = 0; i < n; i++) {
            const p = particles[i];
            ctx.fillStyle = `rgba(255, 255, 255, ${p.opacity})`;
            ctx.shadowColor = '#80EDF7';
            ctx.shadowBlur = 7;
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.radius, 0, 2*Math.PI);
            ctx.fill();
          }
        }
        
        let focused = true;
        let disabled = false;
        let lastTime = performance.now();
        const requestFrame = () => setTimeout(loop, mspf);
        function loop() {
          const dt = (performance.now() - lastTime) / 1000;
        
          if (particles.length < 120 && Math.random() < 0.1) {
            particles.push(gen_particle());
          }
        
          update_pos(dt);
          draw();
        
          lastTime = performance.now();
          if (focused && !disabled)
            requestFrame();
        }
        
        window.addEventListener('focus', () => {
          console.log('snow start');
          focused = true;
          lastTime = performance.now();
          requestFrame();
        });
        
        window.addEventListener('blur', () => {
          console.log('snow stop');
          focused = false;
        });
        
        window.addEventListener('keydown', e => {
          if (e.ctrlKey && e.key == 's') {
            e.preventDefault();
            disabled = !disabled;
            if (disabled) {
              canvas.style.display = 'none';
            } else {
              canvas.style.display = 'block';
              lastTime = performance.now();
              requestFrame();
            }
          }
        });
        
        requestFrame();
        ```
        
    === "线条"
    
        ```javascript
        !function() {
            function o(w, v, i) {
                return w.getAttribute(v) || i
            }
            function j(i) {
                return document.getElementsByTagName(i)
            }
            function l() {
                var i = j("script"),
                w = i.length,
                v = i[w - 1];
                return {
                    l: w,
                    z: o(v, "zIndex", -1),
                    o: o(v, "opacity", 0.5),
                            c: o(v, "color", "0,0,0"),
                    n: o(v, "count", 99)
                }
            }
            function k() {
                r = u.width = window.innerWidth ||         document.documentElement.clientWidth || document.body.clientWidth,
                n = u.height = window.innerHeight ||         document.documentElement.clientHeight || document.body.clientHeight
                    }
            function b() {
                e.clearRect(0, 0, r, n);
                var w = [f].concat(t);
                var x, v, A, B, z, y;
                t.forEach(function(i) {
                    i.x += i.xa,
                    i.y += i.ya,
                    i.xa *= i.x > r || i.x < 0 ? -1 : 1,
                    i.ya *= i.y > n || i.y < 0 ? -1 : 1,
                    e.fillRect(i.x - 0.5, i.y - 0.5, 1, 1);
                    for (v = 0; v < w.length; v++) {
                        x = w[v];
                        if (i !== x && null !== x.x && null !== x.y) {
                            B = i.x - x.x,
                            z = i.y - x.y,
                            y = B * B + z * z;
                            y < x.max && (x === f && y >= x.max / 2 && (i.x -= 0.03 * B, i.y -= 0.03 * z), A = (x.max - y) / x.max, e.beginPath(), e.lineWidth = A / 2, e.strokeStyle = "rgba(" + s.c + "," + (A + 0.2) + ")", e.moveTo(i.x, i.y), e.lineTo(x.x, x.y), e.stroke())
                        }
                    }
                    w.splice(w.indexOf(i), 1)
                }),
                m(b)
            }
            var u = document.createElement("canvas"),
            s = l(),
            c = "c_n" + s.l,
            e = u.getContext("2d"),
            r,
            n,
            m = window.requestAnimationFrame || window.webkitRequestAnimationFrame || window.mozRequestAnimationFrame || window.oRequestAnimationFrame || window.msRequestAnimationFrame ||
            function(i) {
                window.setTimeout(i, 1000 / 45)
            },
            a = Math.random,
            f = {
                x: null,
                y: null,
                max: 20000
            };
            u.id = c;
            u.style.cssText = "position:fixed;top:0;left:0;z-index:" + s.z + ";opacity:" + s.o;
            j("body")[0].appendChild(u);
            k(),
            window.onresize = k;
            window.onmousemove = function(i) {
                i = i || window.event,
                f.x = i.clientX,
                f.y = i.clientY
            },
            window.onmouseout = function() {
                f.x = null,
                f.y = null
            };
            for (var t = [], p = 0; s.n > p; p++) {
                var h = a() * r,
                g = a() * n,
                q = 2 * a() - 1,
                d = 2 * a() - 1;
                t.push({
                    x: h,
                    y: g,
                    xa: q,
                    ya: d,
                    max: 6000
                })
            }
            setTimeout(function() {
                b()
            },
            100)
        } ();
        ```
    === "粒子"
    
        ```javascript
        window.onload = function () {
            //定义body的margin由默认值8px->0px
            document.body.style.margin = "0";
            document.body.style.background = "255,255,255";
            //创建canvas画布
            document.body.appendChild(document.createElement('canvas'));
            var canvas = document.querySelector('canvas'),
                ctx = canvas.getContext('2d') //ctx返回一个在canvas上画图的api/dom
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
            canvas.style.position = 'fixed';
            ctx.lineWidth = .3;
            ctx.strokeStyle = (new Color(150)).style;
            //定义鼠标覆盖范围
            var mousePosition = {
                x: 30 * canvas.width / 100,
                y: 30 * canvas.height / 100
            };
            var dots = {
                nb: 1000,//Dot的总数
                distance: 50,
                                d_radius: 100,
                        array: []
            };
            //创建颜色类，Color类返回字符串型rgba（*,*,*,.8）
            function mixComponents(comp1, weight1, comp2, weight2) {
                return (comp1 * weight1 + comp2 * weight2) / (weight1 + weight2);
            }
            function averageColorStyles(dot1, dot2) {
                var color1 = dot1.color,
                    color2 = dot2.color;
        
                var r = mixComponents(color1.r, dot1.radius, color2.r, dot2.radius),
                    g = mixComponents(color1.g, dot1.radius, color2.g, dot2.radius),
                    b = mixComponents(color1.b, dot1.radius, color2.b, dot2.radius);
                return createColorStyle(Math.floor(r), Math.floor(g), Math.floor(b));
            }
            function colorValue(min) {
                return Math.floor(Math.random() * 255 + min);
            }
            function createColorStyle(r, g, b) {
                return 'rgba(' + r + ',' + g + ',' + b + ', 0.8)';
            }
            function Color(min) {
                min = min || 0;
                this.r = colorValue(min);
                this.g = colorValue(min);
                this.b = colorValue(min);
                this.style = createColorStyle(this.r, this.g, this.b);
            }
            //创建Dot类以及一系列方法
            function Dot() {
                this.x = Math.random() * canvas.width;
                this.y = Math.random() * canvas.height;
        
                this.vx = -.5 + Math.random();
                this.vy = -.5 + Math.random();
        
                this.radius = Math.random() * 2;
        
                this.color = new Color();
            }
        
            Dot.prototype = {
                draw: function () {
                    ctx.beginPath();
                    ctx.fillStyle = this.color.style;
                    ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2, false);
                    ctx.fill();
                }
            };
            function moveDots() {//Dot对象的移动
                for (i = 0; i < dots.nb; i++) {
        
                    var dot = dots.array[i];
        
                    if (dot.y < 0 || dot.y > canvas.height) {
                        dot.vx = dot.vx;
                        dot.vy = - dot.vy;
                    }
                    else if (dot.x < 0 || dot.x > canvas.width) {
                        dot.vx = - dot.vx;
                        dot.vy = dot.vy;
                    }
                    dot.x += dot.vx;
                    dot.y += dot.vy;
                }
            }
            function connectDots() {//DOt对象的连接
                for (i = 0; i < dots.nb; i++) {
                    for (j = i; j < dots.nb; j++) {
                        i_dot = dots.array[i];
                        j_dot = dots.array[j];
        
                        if ((i_dot.x - j_dot.x) < dots.distance && (i_dot.y - j_dot.y) < dots.distance && (i_dot.x - j_dot.x) > - dots.distance && (i_dot.y - j_dot.y) > - dots.distance) {
                            if ((i_dot.x - mousePosition.x) < dots.d_radius && (i_dot.y - mousePosition.y) < dots.d_radius && (i_dot.x - mousePosition.x) > - dots.d_radius && (i_dot.y - mousePosition.y) > - dots.d_radius) {
                                ctx.beginPath();
                                ctx.strokeStyle = averageColorStyles(i_dot, j_dot);
                                ctx.moveTo(i_dot.x, i_dot.y);
                                ctx.lineTo(j_dot.x, j_dot.y);
                                ctx.stroke();//绘制定义的路线
                                ctx.closePath();//创建从当前点回到起始点的路径
                            }
                        }
                    }
                }
            }
            function createDots() {//创建nb个Dot对象
                for (i = 0; i < dots.nb; i++) {
                    dots.array.push(new Dot());
                }
            }
            function drawDots() {//引用Dot原型链，使用draw方法，在canvas上画出Dot对象
                for (i = 0; i < dots.nb; i++) {
                    var dot = dots.array[i];
                    dot.draw();
                }
            }
            function animateDots() {
                ctx.clearRect(0, 0, canvas.width, canvas.height);//清除画布，否则线条会连在一起
                moveDots();
                connectDots();
                drawDots();
                requestAnimationFrame(animateDots);
            }
            createDots();//使用创建Dot类函数
            requestAnimationFrame(animateDots);//使用canvas独有的60Hz刷新屏幕画布的方法
        
            document.querySelector('canvas').addEventListener('mousemove', function (e) {
                mousePosition.x = e.pageX;
                mousePosition.y = e.pageY;
            })
        
            document.querySelector('canvas').addEventListener('mouseleave', function (e) {//鼠标离开时，连接自动返回到画布中心
                mousePosition.x = canvas.width / 2;
                mousePosition.y = canvas.height / 2;
            })
        
        }
        ```

## 嵌入pdf

> 参考资料：
>
> [咸鱼暄的代码空间](https://xuan-insr.github.io/杂项/博客搭建记录/#嵌入-pdf)
>
> [Mkdocs中文教程](https://wcowin.work/Mkdocs-Wcowin/blog/websitebeauty/mkpdf.html)
>
> [CC98论坛](https://www.cc98.org/topic/6002312)

安装`extension`

```cmd
$ pip install pymdown-extensions
```

随后修改`mkdocs.yml`文件，需要在`markdown_extensions`部分加上这个插件并包含它的配置：

```yaml
markdown_extensions: 
  - abbr
  - pymdownx.pathconverter:
      base_path: '' # default: ''
      relative_path: '' # default ''
      absolute: false # default: false
      tags: 'a script img link object embed'
```

在`markdown`中加上：

```html
<iframe src="Path2YourFile" width="100%" height="600px" style="border: none;">
This browser does not support PDFs
</iframe>
```

   假如`markdown`文件在`docs/markdown/test.md`，而想要插的文件在`docs/files/insert.pdf`，就在`src`写`../files/insert.pdf`。

??? note "可能的完整代码"

    === "Mkdocs中文教程"
        ```html
        <div class="grid cards" markdown>
        -   :octicons-bookmark-16:{ .lg .middle } 
        ---
        <iframe src="Path2YourFile.pdf" width="100%" height="800px" style="border: 1px solid #ccc; overflow: auto;">
        </iframe>
        </div>
        ```
    
    === "咸鱼暄の代码"
        ```html
        <object data="path" type="application/pdf" width="100%" height="800">
            <embed src="path" type="application/pdf" />
        </object>
        ```

> 该“可能的完整代码”教程没有提到`extension`插件，可能是另一种可行的方法。

## 消除公式纵向滚动条

> 来源资料：[咸鱼暄的代码空间](https://xuan-insr.github.io/%E6%9D%82%E9%A1%B9/%E5%8D%9A%E5%AE%A2%E6%90%AD%E5%BB%BA%E8%AE%B0%E5%BD%95/#%E8%A7%A3%E5%86%B3%E5%85%AC%E5%BC%8F%E5%B8%A6%E7%BA%B5%E5%90%91%E6%BB%9A%E5%8A%A8%E6%9D%A1%E7%9A%84%E9%97%AE%E9%A2%98)

在`mkdocs.yml`里引入`extra.css`（覆盖样式表）

然后在在 extra.css 里增加这样的东西：

```css
.md-typeset div.arithmatex {
  overflow-y: hidden;
}
```

## Status小方块

> 来源资料：[咸鱼暄的代码空间](https://xuan-insr.github.io/%E6%9D%82%E9%A1%B9/%E5%8D%9A%E5%AE%A2%E6%90%AD%E5%BB%BA%E8%AE%B0%E5%BD%95/#status-%E5%B0%8F%E6%96%B9%E5%9D%97)
>
> [蒋炎岩老师的网站](https://jyywiki.cn/OS/2022/)

<span class="box box-blue">blue</span>
<span class="box box-green">green</span>
<span class="box box-red">red</span>
<span class="box box-yellow">yellow</span>
<span class="box box-gray">gray</span>

??? note "代码"
    === "status.css"

        ```css
        .box {
            border-radius: 3px; padding: 1px 4px;
            font-family: 'Lato', 'SimHei', 'STHeiti', 'SimHei', 'Serif';
            font-size: 90%;
        }
        .box-blue,  .badge-primary  { background-color: rgba(66, 139, 202, 0.5); color: #1d4ed8; }
        .box-green, .badge-success  { background-color: rgba(92, 184, 92, 0.5);  color: #15803d; }
        .box-red,   .badge-danger   { background-color: rgba(217, 83, 79, 0.5);  color: #b91c1c; }
        .box-yellow,.badge-warning  { background-color: rgba(240, 173, 78, 0.5); color: #a16207; }
        .box-gray   { background-color: #a0a0a0; }
        ```


使用方法：

```html
<span class="box box-blue">blue</span>
<span class="box box-green">green</span>
<span class="box box-red">red</span>
<span class="box box-yellow">yellow</span>
<span class="box box-gray">gray</span>
```

## 加粗标题

> 来源资料：[NoughtQ的笔记本](https://note.noughtq.top/)

??? note "代码"

    === "custom.css"
        ```css
        .md-typeset h1,
        .md-typeset h2,
        .md-typeset h3,
        .md-typeset h4,
        .md-typeset h5 {
          font-weight: 600;
        }
        .md-header__topic {
          font-weight: 700;
        }
        .md-typeset h3 {
          margin: .8em 0 .8em
        }
        ```
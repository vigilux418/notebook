---
comments: true
---

# Material主题设置

> 全文主要参考资料：
>
> [**Material for MkDocs官方文档**](https://squidfunk.github.io/mkdocs-material/)

##  更改颜色

### 配色方案

`Material for Mkdocs`支持两种配色方案：浅色模式`default`以及深色模式`slate`。配色方案在`mkdocs.yml`中如下设置：

```yaml
theme: 
  palette: 
    scheme: default
```

还可以根据用户偏好设置配色方案，该偏好利用媒体查询，方案是将`mkdocs.yml`中的`theme/palette/scheme`的值改为`preference`。

### 原色

原色用于标题、侧边栏、文本链接和其他几个组件。

```yaml
theme: 
  palette: 
    primary: indigo
```

> 有效的原色名称有：`red` `pink` `purple` `deep purple` `indigo` `blue` `light blue` `cyan` `teal` `green` `light green` `lime yellow` `amber` `orange` `deep orange` `brown` ` grey` `blue grey` `black` `white` 

### 强调色

强调色用于表示可以与之交互的元素，例如悬停链接、按钮和滚动条。

```yaml
theme: 
  palette: 
    accent: indigo
```

> 有效的强调色名称有：`red` `pink` `purple` `deep purple` `indigo` `blue` `light blue` `cyan` `teal` `green` `light green` `lime` `yellow` `amber` `orange` `deep orange`

### 调色板切换

提供**明暗**色调的配色方案，让您的文档在一天中的不同时间都能轻松阅读，方便用户做出相应的选择。将以下几行添加到`mkdocs.yml`：

```yaml
theme:
  palette:

    - media: "(prefers-color-scheme)"
      toggle:
        icon: material/brightness-auto
        name: Switch to light mode

    - media: "(prefers-color-scheme: light)"
      scheme: default 
      toggle:
        icon: material/brightness-7
        name: Switch to dark mode

    - media: "(prefers-color-scheme: dark)"
      scheme: slate
      toggle:
        icon: material/brightness-4
        name: Switch to system preference
```

`icon`

此配置将在搜索栏旁边呈现一个调色板切换按钮。请注意，您也可以为每个调色板定义单独的`primary`设置`accent`。

`name`

此属性用作切换按钮的`title`属性 (attribute)，应设置为可识别的名称以提高可访问性。

- 通过使用媒体查询，每个调色板都可以与用户系统对明暗外观的偏好设置关联。只需在 `mkdocs.yml` 中的 `scheme` 定义旁边添加一个 `media` 属性即可。

  当用户首次访问你的网站时，媒体查询会按照其定义的顺序进行评估。第一个匹配的媒体查询将选择默认调色板。

- 较新的操作系统允许在白天和夜晚自动切换明暗外观。`Material for MkDocs`增加了对自动明暗模式的支持，将调色板选择委托给用户的操作系统。

  现在，每次操作系统在明暗外观之间切换时，`MkDocs`的材料都会更改调色板，即使用户没有重新加载网站。

### 自定义颜色

> 参考资料：
>
> [**鹤翔万里的笔记本**](https://note.tonycrane.cc/)
>
> [**NoughtQ的笔记本**](https://note.noughtq.top/)
>
> [**Ronald Luo的Blog**](https://ronaldln.github.io/MyPamphlet-Blog/)

`Material for MkDocs`使用**CSS 变量**（自定义属性）来实现颜色。如果您想要自定义调色板以外的颜色（例如，使用您品牌特定的颜色），您可以添加**额外的样式表**并调整 CSS 变量的值。

首先，将 `mkdocs.yml` 中的 `primary`或 `accent` 值设置为 `custom` ，以向主题发出信号，表示您想要定义自定义颜色，例如，当您想要覆盖 `primary` 时：

```yaml
theme:
  palette:
    primary: custom
```

假设您是 **YouTube** ，并且想要将主色设置为您品牌的调色板。只需添加：

```css
/* docs/stylesheets/extra.css */
:root  > * {
  --md-primary-fg-color:        #EE0F0F;
  --md-primary-fg-color--light: #ECB7B7;
  --md-primary-fg-color--dark:  #90030C;
}
```

```yaml
extra_css:
  - stylesheets/extra.css
```

例如，我的设置如下：

```css
:root {
  --md-primary-fg-color: #000000;
  --md-primary-fg-color--light: #000000;
  --md-primary-fg-color--dark:  #000000;
}
/* docs/stylesheets/extra.css */
[data-md-color-scheme="default"] {
  --md-typeset-a-color: #555555;
  --md-footer-fg-color: #ffffff;
  --md-footer-bg-color: #0d0d0d;
  --md-footer-bg-color--dark: #0d0d0d;
  --md-footer-fg-color--light: #fff;
  --md-footer-fg-color--lighter: #fff;
}
[data-md-color-scheme="slate"] {
  --md-default-bg-color: #151515;
  --md-default-bg-color--light: #151515;
  --md-default-bg-color--lighter: #151515;
  --md-default-bg-color--lightest: #151515;
  --md-default-fg-color: rgb(255, 255, 255);
  --md-default-fg-color--light: rgba(255, 255, 255);
  --md-default-fg-color--lighter: rgb(255, 255, 255,0.8);
  --md-default-fg-color--lightest: rgba(255, 255, 255, 0.6);
  --md-footer-fg-color: #fff;
  --md-footer-bg-color: #0d0d0d;
  --md-footer-bg-color--dark: #0d0d0d;
  --md-footer-fg-color--light: #fff;
  --md-footer-fg-color--lighter: #fff;
  --md-accent-fg-color:  #93d2ce;
  --md-typeset-a-color: #555555;
  background-attachment: fixed;
  background-repeat: no-repeat;
}
```

## 更改字体

### 常规字体

常规字体用于所有正文、标题以及基本上所有不需要等宽的内容。它可以设置为任何有效的**Google 字体**。

```yaml
theme: 
  font: 
    text: Roboto
```

### 等宽字体

等宽字体用于代码块，可以单独配置。

```yaml
theme:
  font:
    code: Roboto Mono
```

### 禁用字体加载

如果您想防止从 Google Fonts 加载字体并回退到系统字体：

```yaml
theme: 
  font: false
```

### 附加字体

> 参考资料：
>
> [**鹤翔万里的笔记本**](https://note.tonycrane.cc/)
>
> [**NoughtQ的笔记本**](https://note.noughtq.top/)
>
> [**Ronald Luo的Blog**](https://ronaldln.github.io/MyPamphlet-Blog/)

如果您想从另一个目标加载（附加）字体或覆盖系统字体，则可以使用**附加样式表**来添加相应的 `@font-face` 定义：

```css
/* docs/stylesheets/extra.css */
@font-face {
  font-family: "<font>";
  src: "...";
}
```

```yaml
extra_css:
  - stylesheets/extra.css
```

然后可以将字体应用于特定元素（例如，仅标题）。

```css
/* 常规字体 */
:root {
  --md-text-font: "<font>"; 
}
/* 等宽字体 */
:root {
  --md-code-font: "<font>";
}
```

例如，我的设置如下：

```css
/* docs/stylesheets/extra.css */
:root {
  --md-text-font: "JetBrains Mono", "LXGW WenKai Screen"; 
  --md-code-font: "JetBrains Mono";  
}
```

```yaml
extra_css: 
    - stylesheets/extra.css
    - https://gcore.jsdelivr.net/npm/lxgw-wenkai-screen-webfont@1.1.0/style.css
    - https://gcore.jsdelivr.net/npm/lxgw-wenkai-webfont@1.1.0/style.css
    - https://fonts.googleapis.com/css2?family=JetBrains+Mono:ital,wght@0,100..800;1,100..800&display=swap
```

## 更改语言

```yaml
theme: 
  language: en
```

## 更改徽标和图标

### 配置

有两种方法可以指定**徽标**：它必须是与**主题捆绑在一起的任何图标**的有效路径，或者指向位于文件夹中的**用户提供的图像**的有效路径。

```yaml
theme: 
 icon: 
   logo: material/library #图标
---
theme: 
  logo: assets/logo.png #图像
```

### 网站图标

网站图标可以更改为指向用户提供的图像的路径，该图像必须位于`docs`文件夹中。

```yaml
theme:
  favicon: images/favicon.png
```

## 设置导航

### 即时加载

启用**即时加载**后，所有内部链接的点击将被拦截并通过 [XHR](https://developer.mozilla.org/en-US/docs/Web/API/XMLHttpRequest) 发送，而无需完全重新加载页面。

```yaml
theme:
  features:
    - navigation.instant
```

### 锚点跟踪

启用**锚点跟踪**后，地址栏中的 URL 会自动更新为目录中突出显示的活动锚点。

```yaml
theme:
  features:
    - navigation.tracking
```

### 进度指示器

为了在网络速度较慢时提供更好的用户体验，您可以启用进度指示器。它会显示在页面顶部，并在页面完全加载后隐藏。

```yaml
theme:
  features:
    - navigation.instant.progress
```

仅当页面在 400 毫秒后仍未完成加载时，进度指示器才会显示，因此快速连接永远不会显示它以获得更好的即时体验。

### 粘性导航选项卡

启用**选项卡**后，顶级部分将呈现在上面视口的标题下方的菜单层中，但在移动设备上保持原样。

启用**粘性选项卡**后，导航选项卡将锁定在标题下方，并且在向下滚动时始终保持可见。

```yaml
theme:
  features:
    - navigation.tabs
    - navigation.tabs.sticky
```

### 导航部分

启用**分区**后，顶级分区将在上述视口的侧边栏中呈现为组，但在移动设备上保持原样。

```yaml
theme:
  features:
    - navigation.sections
```

### 导航扩展

启用**扩展**后，左侧边栏将默认展开所有可折叠的子部分，因此用户不必手动打开子部分。

```yaml
theme:
  features:
    - navigation.expand
```

### 导航修剪

启用修剪后，渲染的 HTML 中仅包含可见的导航项， **从而将构建的站点的大小减少 33% 或更多** 。

```yaml
theme:
  features:
    - navigation.prune
```

此功能标记对于页面数量超过 100 甚至 1,000 的文档网站尤其有用，因为导航占据了 HTML 的很大一部分。导航修剪会将所有可扩展部分替换为指向该部分首页（或部分索引页）的链接。

### 章节索引页

启用**章节索引页**后，可以将文档直接附加到章节，这对于提供概览页特别有用。

```yaml
theme:
  features:
    - navigation.indexes
```

要将页面链接到某个部分，请在相应文件夹中创建一个具有该名称的新文档，并将其添加到导航部分的开头：

```yaml
nav:
  - Section:
    - section/index.md
    - Page 1: section/page-1.md
    ...
    - Page n: section/page-n.md
```

> 此功能标志可以与所有其他功能标志结合使用，目录导航集成除外。

## 目录

`permalink`

- 此选项在每个标题的末尾添加一个包含段落符号或其他自定义符号的锚链接。

```yaml
markdown_extensions:
  - toc:
      permalink: ⚓︎
```

### 锚点跟随

当启用目录的锚点跟随功能时，侧边栏会自动滚动，以便活动锚点始终可见。

```yaml
theme:
  features:
    - toc.follow
```

`toc_depth`

- 定义要包含在目录中的级别范围。这对于具有深度结构标题的项目文档可能很有用，可以减少目录的长度，或完全删除目录

```yaml
markdown_extensions:
  - toc:
      toc_depth: 3
```

### 返回顶部按钮

当用户向下滚动后再次向上滚动时，可以显示返回顶部按钮。该按钮将呈现在标题下方的正中央。

```yaml
theme:
  features:
    - navigation.top
```

## 设置中文搜索

### 内置搜索

默认情况下，**内置的搜索插件**处于启用状态，但当使用其他插件时，必须重新添加。

```yaml
plugins:
  - search
```

支持以下选项：

`lang`

```yaml
plugins:
  - search:
      lang:
        - en
        - zh
```

`MkDocs`的`Material`版中文支持由`jieba`提供。`jieba`是一个优秀的中文文本分词库。如果安装了 `jieba`，内置的搜索插件会自动检测中文字符并进行分词。

```cmd
$ pip install jieba
```

文本使用零宽度空格字符进行分段，因此在搜索模式中呈现的效果完全相同。调整 `mkdocs.yml` 以使 `separator`包含 `\u200b` 字符：

```yaml
plugins:
  - search:
      separator: '[\s\u200b\-]'
```

### 搜索突出显示

启用搜索高亮显示后，当用户点击搜索结果时，Material for MkDocs 会在点击链接后高亮显示所有匹配结果。

```yaml
theme:
  features:
    - search.highlight
```

### 搜索共享

激活搜索共享后，重置按钮旁边会呈现一个共享按钮，用于深度链接到当前搜索查询和结果。

```yaml
theme:
  features:
    - search.share
```

当用户点击分享按钮时，URL 会自动复制到剪贴板。

## 设置站点分析

`Material for MkDocs`与`Google Analytics 4`原生集成。如果您已经设置了`Google Analytics`并拥有媒体资源，请通过向 `mkdocs.yml` 添加以下几行来启用它。

```yaml
extra:
  analytics:
    provider: google
    property: G-XXXXXXXXXX
```

### 此页面有帮助吗？

每个页面底部可以添加一个简单的反馈小部件，鼓励用户即时反馈页面是否有帮助。

```yaml
extra:
  analytics: 
    feedback:
      title: Was this page helpful?
      ratings:
        - icon: material/emoticon-happy-outline
          name: This page was helpful
          data: 1
          note: >-
            Thanks for your feedback!
        - icon: material/emoticon-sad-outline
          name: This page could be improved
          data: 0
          note: >- 
            Thanks for your feedback! Help us improve this page by
            using our <a href="..." target="_blank" rel="noopener">feedback form</a>.
```

## 设置标题

### 自动隐藏

启用**自动隐藏**后，当用户滚动超过某个阈值时，标头会自动隐藏，从而为内容留出更多空间。

```yaml
theme: 
  features: 
    - header.autohide
```

## 设置页脚

### 导航

页脚可以包含当前页面的上一页和下一页的链接。

```yaml
theme:
  features:
    - navigation.footer
```

### 社交链接

所有**社交链接**都作为项目文档页脚的一部分呈现在版权信息旁边。

```yaml
extra:
    social: 
        - icon: fontawesome/brands/github
          link: https://github.com/vigilux418
        - icon: fontawesome/brands/docker
          link: https://app.docker.com/accounts/vigilux
```

> - `icon`
>
>   默认值：*无* · 必需 – 此字段必须指向引用与[主题捆绑在一起的任何图标](https://github.com/squidfunk/mkdocs-material/tree/master/material/.icons)的有效图标路径，否则生成将不会成功。一些流行的选择：
>
>   - `-fontawesome/brands/behance`
>
>   - `fontawesome/brands/docker`
>
>   - `fontawesome/brands/github`
>
>   - `fontawesome/brands/instagram`
>
>   - `fontawesome/brands/linkedin`
>
>   - `fontawesome/brands/medium`
>
>   - `fontawesome/brands/pied-piper-alt`
>
>   - `fontawesome/brands/product-hunt`
>
>   - `fontawesome/brands/slack`
>
>   - `fontawesome/brands/twitter`

- `link`
  必需 – 此字段必须包含有效的相对或绝对 URL，包括 URI 方案。支持所有 URI 方案

  ```yaml
  extra:
    social:
      - icon: fontawesome/solid/paper-plane
        link: mailto:<email-address>
  ```

- `name`

  此字段用作链接的属性，可以设置为可识别的名称以提高可访问性。

  ```yaml
  extra:
    social:
      - icon: fontawesome/brands/twitter
        link: https://twitter.com/squidfunk
        name: squidfunk on Twitter
  ```

### 版权声明

自定义**版权横幅**可以呈现为页脚的一部分，该页脚显示在社交链接旁边。它可以定义为：

```yaml
copyright: Copyright &copy; 2016 - 2020 Martin Donath
```

## 添加Git存储库

为了在文档中显示项目存储库的链接，请将 [`repo_url`](https://www.mkdocs.org/user-guide/configuration/#repo_url) 设置为存储库的公共 URL，例如

```yaml
repo_url: https://github.com/vigilux418/mkdocs
```

### 存储库名称

```yaml
repo_name: Vigilux's Notebook
```

### 存储库图标

虽然默认*存储库图标*是通用的 git 图标，但可以通过引用 中的有效图标路径将其设置为与**主题捆绑在一起的任何图标**。

```yaml
theme:
  icon:
    repo: fontawesome/brands/git-alt
```

### 编辑按钮

如果存储库 URL 指向`GitHub`、`GitLab`或`Bitbucket`存储库，则每个文档的顶部都会显示一个**编辑按钮**。

如果您的默认分支名为 `main` ，则将设置更改为：

```yaml
edit_uri: edit/main/docs/
```

确保 `edit_uri` 配置正确后，即可添加代码操作按钮。支持两种类型的代码操作： `edit` 和 `view` （仅限 GitHub）

```yaml
theme:
  features:
    - content.action.edit #编辑此页面
    - content.action.view #查看此页面的源代码
```

可以使用以下几行更改编辑和查看按钮的图标：

```yaml
theme:
  icon:
    edit: material/pencil 
    view: material/eye
```

### 修订日期本地化

[**git-revision-date-localized**](https://github.com/timvink/mkdocs-git-revision-date-localized-plugin) 插件添加了对在每个页面底部添加本地化的**上次更新**日期的支持。

```cmd
$ pip install mkdocs-git-revision-date-localized-plugin
```

```yaml
plugins:
  - git-revision-date-localized:
      enable_creation_date: true
      type: date
      fallback_to_build_date: true
```

`type`选项允许更改要显示的日期的格式：`date` `datetime` `iso_date` `iso_datetime` `timeago`

`fallback_to_build_date`选项指定在 git 存储库不可用时是否应将执行时间用作回退。

## 添加评论系统

### `Giscus`集成

在使用 [Giscus](https://giscus.app/) 之前，您需要完成以下步骤：

1. **安装 [Giscus GitHub App](https://github.com/apps/giscus)** ，并授予将评论托管为 GitHub 讨论的仓库的访问权限。

2. **访问 [Giscus](https://giscus.app/) ，并通过其配置工具生成代码片段**以加载评论系统。复制该代码片段以进行下一步操作。生成的代码片段应类似于以下内容：

   ```html
   <script
     src="https://giscus.app/client.js"
     data-repo="<username>/<repository>"
     data-repo-id="..."
     data-category="..."
     data-category-id="..."
     data-mapping="pathname"
     data-reactions-enabled="1"
     data-emit-metadata="1"
     data-theme="light"
     data-lang="en"
     crossorigin="anonymous"
     async
   >
   </script>
   ```

`comments.html`部分（默认为空）是添加 [Giscus](https://giscus.app/) 生成的代码片段的最佳位置。

使用命令覆盖`comment.html`部分，仍需以下步骤：

1. 新建`overrides`文件夹、`partials`文件夹、`comments.html`文件，使得文件呈现如下结构：

   ```txt
   .
   ├─ overrides/
   │  └─ partials/
   │     └─ comments.html
   └─ mkdocs.yml
   ```

2. 使用以下代码覆盖`comments.html`部分：
   ```html
   {% if page.meta.comments %}
     <h2 id="__comments">{{ lang.t("meta.comments") }}</h2>
     <!-- Insert generated snippet here -->
   
     <!-- Synchronize Giscus theme with palette -->
     <script>
       var giscus = document.querySelector("script[src*=giscus]")
   
       // Set palette on initial load
       var palette = __md_get("__palette")
       if (palette && typeof palette.color === "object") {
         var theme = palette.color.scheme === "slate"
           ? "transparent_dark"
           : "light"
   
         // Instruct Giscus to set theme
         giscus.setAttribute("data-theme", theme) 
       }
   
       // Register event handlers after documented loaded
       document.addEventListener("DOMContentLoaded", function() {
         var ref = document.querySelector("[data-md-component=palette]")
         ref.addEventListener("change", function() {
           var palette = __md_get("__palette")
           if (palette && typeof palette.color === "object") {
             var theme = palette.color.scheme === "slate"
               ? "transparent_dark"
               : "light"
   
             // Instruct Giscus to change theme
             var frame = document.querySelector(".giscus-frame")
             frame.contentWindow.postMessage(
               { giscus: { setConfig: { theme } } },
               "https://giscus.app"
             )
           }
         })
       })
     </script>
   {% endif %}
   ```
   
3. 将第`3`行替换为你在上一步中使用 [Giscus](https://giscus.app/) 配置工具生成的代码片段。如果您从上面复制了该代码片段，则可以通过将 `comments` front matter 属性设置为 `true` 来在页面上启用评论：

   ```markdown
   ---
   comments: true
   ---
   
   Page title
   ...
   ```

> 如果您希望为整个文件夹启用评论，您可以使用内置元插件。

## 元数据

元数据扩展是标准 Markdown 库的一部分，它添加了向文档添加前言的功能。

```yaml
markdown_extensions:
  - meta
```

## 网站优化

在某些情况下，你可能希望在所有项目之间共享用户级设置，例如所选调色板或 Cookie 同意。为此，请将以下几行添加到 `mkdocs.yml` 中：

```yaml
extra:
  scope: /
```

> **工作原理：**
>
> 假设您有以下站点结构：
>
> ```txt
> .
> └── /
>  ├── subsite-a/
>  ├── subsite-b/
>  └── subsite-c/
> ```
>
> 默认情况下，每个站点都有自己的作用域 ( `/subsite-a/` 、 `/subsite-b/` 、 `/subsite-c/` )。要修改此行为，请在 `mkdocs.yml` 中添加以下几行：
>
> ```yaml
> extra:
> scope: /
> ```
>
> 通过将其设置为 `/` ，它应该允许您在主站点和所有子站点之间共享以下首选项：
>
> - `Cookie`同意
> - 内容标签的链接，即活动标签
> - 调色板
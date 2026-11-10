# Zensical 迁移记录

> 迁移日期：2026-11-10（Asia/Shanghai）
> 源提交：`2ed78f95c728b9acc317e392b273dbe5e415a56d`
> 目标引擎：Zensical **0.1.0**（UI 0.0.41，classic 变体）
> 依据：2026-11-10 的《Zensical 迁移调研与执行报告》（仓库外调研文档）
> 本文件记录实际执行结果、已知差异与回退方法，后续维护请先读本文件。

## 1. 结论

笔记源 `docs/`（65 页）、目录结构、URL、锚点、统计口径、Git 日期、分区索引目录、
评论映射、灯箱与既有前端优化均完成迁移；构建与发布切换到 Zensical，同时保留
Material for MkDocs 回退构建能力。

Zensical 0.1.0 **不执行 MkDocs 插件与 hooks**，因此迁移采用“构建预处理 + 原生兼容插件”路线：

```text
docs/（唯一人工编辑源）
        │  python tools/notebook_build.py prepare
        ├─ hooks/toc.py 的分区索引目录（8 组 27 条）
        ├─ mkdocs-statistics-plugin 0.1.5 的整站/页面统计（65/63119/2056、20 页）
        ├─ mkdocs-git-revision-date-localized 1.4.7 的创建/更新日期（64 页）
        └─ 友链头像路径精确适配（links.md 单点）
        │
   .migration/docs/（自动生成，不提交、不人工编辑）
        │  zensical build --clean --strict（mkdocs.zensical.yml）
        │
   site-zensical/ → 验收 → ghp-import → gh-pages
```

## 2. 变更清单

### 2.1 新增文件

| 文件 | 作用 |
| --- | --- |
| `mkdocs.zensical.yml` | 目标配置：`INHERIT: mkdocs.yml`、`docs_dir: .migration/docs`、`site_dir: site-zensical`、`hooks: []`、`theme.variant: classic`、保留 macros/meta/search/glightbox 兼容插件；完整保留父配置的 `extra_css` 并追加 `zensical.css`；`extra.build_engine: zensical` 供模板区分构建器 |
| `tools/notebook_build.py` | 构建入口：`prepare` / `build` / `serve`。等价实现目录、统计、Git 日期、头像适配；`serve` 监听原始 docs/includes/Hook 模板并增量重建暂存内容 |
| `requirements-zensical.txt` | 固定版本：`zensical==0.1.0`（UI 0.0.41）、`Jinja2==3.1.6`、`PyYAML==6.0.3`、`Babel==2.18.0`、`tzdata==2026.6`、`ghp-import==2.1.0`，并锁定 2026-11-10 干净环境解析出的全部传递依赖 |
| `requirements-dev.txt` | 本地验收工具依赖（BeautifulSoup/Playwright，不参与构建） |
| `tools/verify_migration.py`、`tools/verify_runtime.py` | 可复跑的迁移验收脚本：Material 基线 vs Zensical 产物的静态对照与浏览器运行时探针 |
| `docs/stylesheets/zensical.css` | 仅 Zensical 加载的兼容样式：恢复 `scrollbar-gutter`、对齐搜索触发器尺寸/圆角、保留 GLightbox 深色主题补丁 |
| `docs/javascripts/vendor/glightbox.min.js`、`docs/stylesheets/vendor/glightbox.min.css`、`LICENSE.glightbox` | 本地化 GLightbox（MIT）：Zensical 本会运行时从 unpkg 拉取，这里改为仓库自维护，保持“小型前端资源本地化”原则 |
| `MIGRATION.md` | 本文件 |

### 2.2 修改文件

| 文件 | 变更 |
| --- | --- |
| `overrides/main.html` | 新增 `libs` 块：仅在 `config.extra.build_engine == "zensical"` 时预加载本地 GLightbox，使 Zensical bundle 跳过 CDN；Material 回退构建不加载 |
| `overrides/partials/copyright.html` | 生成器署名按构建器区分：Zensical 构建显示 “Made with Zensical”，Material 回退仍显示 “Material for MkDocs”，作者与参考来源致谢不变 |
| `.github/workflows/deploy.yml` | 改为 `pip install -r requirements-zensical.txt` → `python tools/notebook_build.py build` → `ghp-import` 发布 `gh-pages`；保留 Python 3.13、`fetch-depth: 0`（Git 日期需要完整历史）与 `contents: write`；加 `concurrency` 组避免并发发布；发布前设置 git 身份 |
| `.gitignore` | 忽略 `/.migration/`、`/site-zensical/`、`/.venv-zensical/` |
| `README.md` | 更新构建器说明、本地构建/预览命令、回退构建与发布/回退方法、GLightbox 致谢 |

### 2.3 未改动

- `docs/` 下所有原有笔记与资源**字节未变**（仅新增上述 3 个适配资产 + 1 个仅 Zensical 加载的 CSS）；
- `mkdocs.yml`、`requirements.txt`、`hooks/toc.py`、`hooks/templates/toc.html`、`includes/`、其余 7 个全局 CSS 与 8 个前端脚本均未改动，Material 回退构建可用；
- `.gitignore` 已覆盖全部生成目录，构建产物与暂存内容不入库。

## 3. 构建与发布

### 3.1 本地

```powershell
# Zensical（当前生产构建器）
python -m venv .venv-zensical
.venv-zensical\Scripts\pip install -r requirements-zensical.txt
python tools/notebook_build.py serve     # 预览 http://127.0.0.1:8001/
python tools/notebook_build.py build     # 严格构建到 site-zensical/
python tools/notebook_build.py prepare   # 只生成 .migration/docs 并打印统计

# Material 回退构建
pip install -r requirements.txt
mkdocs serve
mkdocs build
```

`serve` 会监听 `docs/`、`includes/`、`hooks/toc.py`、`hooks/templates/toc.html`，
变化后增量重新 prepare（保留暂存目录本身，避免目标引擎监听目录消失）。

### 3.2 CI 发布

`main` 分支 push 后，GitHub Actions：

1. `actions/checkout@v7`（`fetch-depth: 0`）；
2. `actions/setup-python@v7`（Python 3.13）；
3. `pip install -r requirements-zensical.txt`；
4. `python tools/notebook_build.py build`（`--strict`，任何警告使构建失败）；
5. `ghp-import -n -p -f -r origin -b gh-pages site-zensical` 发布到 `gh-pages`。

Pages 来源保持 `legacy` + `gh-pages` 分支，未改动域名与 Pages 配置。

## 4. 能力等价实现

| 能力 | 原实现 | 迁移后 |
| --- | --- | --- |
| 分区索引目录 | `hooks/toc.py` | `tools/notebook_build.py` 复刻其纯逻辑（模板仍用 `hooks/templates/toc.html`），输出 8 组 27 条、`.index-item-wrapper` / `.item-actions[data-ts]` 等约定不变 |
| 整站统计 | statistics 0.1.5 `on_files` | 复刻其算法（忽略 mermaid/math 围栏、图片正则等）→ 首页 65 页 / 63119 字 / 2056 行代码（图片 35） |
| 页面统计 | statistics 0.1.5 `on_page_markdown` | 复刻其口径与插入位置（首个 H1 之后），20 个 `comments: true` 页面逐字一致 |
| Git 创建/更新日期 | git-revision-date-localized 1.4.7 | 复刻作者时间 `%at`、`--diff-filter=Ar --follow` 创建、普通 `git log -n1` 更新、Asia/Shanghai、Babel zh long datetime、首页排除；64 页文本与 `title` 逐字一致 |
| 友链头像 | MkDocs 相对路径处理 | 仅对 `links.md` 的 `../images/lemoon1206.jpg` 做单点适配，最终输出与 Material 一致 |
| 评论 / Giscus | overrides/partials/comments.html | 原样保留，`data-mapping="pathname"` 与 `/notebook/` 前缀不变，20 页 loader 一致 |
| 灯箱 | mkdocs-glightbox 本地资产 | Zensical 内建兼容；GLightbox 资产本地化，Material 时代补丁样式保留 |
| 搜索 | Material/Lunr | Zensical 原生搜索（见 §5 已知差异） |

## 5. 已知差异（已评估、可接受）

以下差异由 Zensical 0.1.0 上游实现决定，未用侵入式补丁强行复刻；后续升级 Zensical 时应重新评估。

1. **搜索弹层**：Zensical 使用独立 Shadow DOM 弹层（输入框 placeholder/提示为英文 `Search`），
   不支持原 Material 的 `search.share` / `search.suggest` 交互；触发器已通过 `zensical.css`
   对齐 Material 的尺寸（234×36、1rem 圆角）并隐藏 `Ctrl+K` 角标，按钮文案为 Zensical 中文
   语言包的“查找”（无法在不改写 Shadow DOM 的前提下改成“搜索”）。
2. **侧栏展开箭头**：上游 `nav-item.html` 不再为“仅含 index 的 section”绘制空箭头，也不再输出
   空嵌套 `<nav>`；真实可展开节点行为不变。
3. **GA 搜索事件**：Zensical 搜索不再使用 `form[name=search]`，旧 Analytics 的 `search` 事件
   绑定不再触发；`page_path` 与 feedback 事件正常。
4. **滚动条槽**：已在 `zensical.css` 恢复 Material 的 `scrollbar-gutter: auto`；短/长页面切换
   （有无滚动条）时居中内容会有与 Material 相同的 7.5px 水平位移。
5. **生成器资源**：GLightbox 已本地化；MathJax 与 Mermaid 引擎仍按原有策略从 CDN 加载
   （迁移前即如此）。
6. **canonical/`site_url`**：本轮保持不变（仍为 `https://vigilux418.github.io/notebook/`），
   与实际访问域名 `https://vigilux.top/notebook/` 的统一留作独立变更，避免与生成器迁移混在一起。
7. **Zensical 版本**：0.1.0 为官方 beta 版本；本项目固定精确版本，升级前需重跑本文件 §6 的
   验收脚本（`tools/verify_migration.py`、`tools/verify_runtime.py`）。

## 6. 验收结果（A01–A18，2026-11-10）

| 编号 | 项目 | 结果 | 证据 |
| --- | --- | --- | --- |
| A01 | 笔记与资源 | 通过 | 原有文件字节未变；新增文件在 §2.1 明确列出；无 tracked 删除 |
| A02 | 页面集合 | 通过 | 65 页 + 404；无缺失/多余；sitemap 65 条；无暂存目录 URL 泄漏；canonical 与基线一致 |
| A03 | 内容与锚点 | 通过 | 65 页标题 id/层级、代码块、表格、公式源文本与 Material 逐字节一致 |
| A04 | 链接与图片 | 通过 | 本地引用 0 缺失；头像 naturalWidth>0；输出 `../images/lemoon1206.jpg` 与基线一致 |
| A05 | 分区目录 | 通过 | 8 组 27 条标题/链接/字数/代码行/阅读时长/data-ts/排序逐字一致 |
| A06 | 全站统计 | 通过 | 65 / 63119 / 2056，无占位符泄漏 |
| A07 | 页面统计 | 通过 | 20 页数字、文本、位置（H1 后）与基线一致 |
| A08 | Git 日期 | 通过 | 64 页创建/更新文本与 `title` 逐字一致；index 排除 |
| A09 | MathJax | 通过 | 全站 337 个包装块（逐页等于基线）；267 个公式页公式硬/软导航渲染；主引擎单次加载 |
| A10 | Mermaid | 通过 | 11 页 105 块全部渲染；软导航下一页 2 图；无残留待处理块 |
| A11 | 首页与动效 | 通过 | 卡片、打字、统计开关、明暗切换、实例/计时器回收正常 |
| A12 | 导航与目录 | 通过 | tabs、前进/后退保持软导航、hash、侧栏高亮、返回顶部正常 |
| A13 | 搜索 | 通过（含已知差异） | 中英文/代码查询可用；键盘打开、结果跳转正常；share/suggest 与弹层英文文案见 §5 |
| A14 | 评论与反馈 | 通过（含口径变化） | 20 页 Giscus loader/属性一致，主题同步与软导航重建正常；GA search 事件见 §5 |
| A15 | 灯箱 | 通过 | 本地 GLightbox 资产加载；打开/Escape 关闭/主题正常；无 unpkg glightbox 请求 |
| A16 | 响应式与视觉 | 通过（含已知差异） | 390/768/960/1440/1920 无横向溢出；首页几何与基线一致；差异见 §5 |
| A17 | 构建和写作 | 通过 | 固定依赖干净环境构建通过（与正式产物逐字节一致）；`serve` 监听原始源并增量刷新 |
| A18 | 部署与回退 | 配置通过，发布结果见 §9 | 单 workflow 单发布者；`gh-pages` 发布与回退产物/步骤见 §7、§9 |

完整机器可读结果：`tools/verify_migration.py` / `tools/verify_runtime.py` 的输出（本地 `.migration/verify/`）。

## 7. 回退

迁移前的 Material 产物、`gh-pages` 归档与详细步骤保存在仓库外
`D:\Workplace\zensical-migration-rollback\`（见其中 `ROLLBACK.md`）。摘要：

```powershell
pip install ghp-import==2.1.0
ghp-import -n -p -f -r origin -b gh-pages D:\Workplace\zensical-migration-rollback\material-site
```

回退只恢复发布内容，不回滚笔记历史；`main` 上的笔记文件保持完整。CI 构建失败时不会更新
`gh-pages`，生产站会自动停留在上一版本。

## 8. 后续建议

1. Zensical 升级（0.1.x → 稳定版）前重跑 `tools/verify_migration.py` 与 `tools/verify_runtime.py`，
   并核对 §5 已知差异是否被上游修复（尤其是搜索 share/suggest、英文文案、nav 图标）。
2. 单独变更统一 canonical/`site_url` 到 `https://vigilux.top/notebook/`，同时检查 sitemap、
   分享链接与 Analytics（与本次生成器迁移解耦）。
3. 若上游提供本地化搜索弹层的正式接口，可移除本文件 §5.1 的记录并调整 `zensical.css`。
4. 新增笔记无需任何迁移专用语法；`python tools/notebook_build.py build` 会自动纳入。

## 9. 发布记录（2026-11-10）

| 项目 | 值 |
| --- | --- |
| 迁移代码提交 | `f203d6b87ca1b8bf2c59229581c47c5bb936eff0`（`feat(build): 迁移站点生成器 …`） |
| 切换前 `gh-pages` | `3354aec7d685eec9dfd603a9373f1b8cdabff3e7`（已归档，见 §7） |
| CI 运行 | [42806468762](https://github.com/vigilux418/notebook/actions/runs/42806468762) — success（安装依赖 18s：build + ghp-import 均通过） |
| 迁移后首次 `gh-pages` | `7de9618c94063334bf99b10ffc1dfbcb449b73a1`（126 文件，含 `.nojekyll`；Pages build `legacy` 状态 built） |
| 线上复核（https://vigilux.top/notebook/） | 通过：`meta generator=zensical-0.1.0`；首页统计 65/63119/2056、卡片/打字/页脚 “Made with Zensical”；`/math/`、`/tools/` 分区目录与 64 页日期正常；公式页 267/267 渲染；`/general/csci/4/` Mermaid 26/26；友链头像 naturalWidth=460、Giscus iframe 正常；搜索“基尔霍夫”返回结果；无未处理 JS 异常；canonical 仍为 `https://vigilux418.github.io/notebook/` |

> 说明：本文件自身的后续文档提交会再次触发 CI，重建内容与首次迁移发布一致（仅 `MIGRATION.md` 变化）。
> 后续若要核对“当前线上发布对应的提交”，以 `gh-pages` 最新提交或其 CI 运行为准。


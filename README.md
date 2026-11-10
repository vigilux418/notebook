# Vigilux 的笔记本 · Vigilux's Notebook

个人学习笔记，当前基于 [Zensical](https://zensical.org/)（Material for MkDocs 团队的继任静态站点生成器）构建；
仓库保留了完整的 Material for MkDocs 回退构建能力，迁移决策与验收标准见调研报告。

在线阅读 / Live site: <https://vigilux.top/notebook/>
（镜像 / mirror: <https://vigilux418.github.io/notebook/>）

## 构建器与版本

| 用途 | 生成器 | 依赖 | 配置 |
| --- | --- | --- | --- |
| 生产（当前） | Zensical 0.1.0（UI 0.0.41） | `requirements-zensical.txt` | `mkdocs.zensical.yml` |
| 回退 | MkDocs 1.6.1 + Material for MkDocs 9.7.7 | `requirements.txt` | `mkdocs.yml` |

Zensical 不会执行 MkDocs 插件与 Hook。原站点依赖的分区索引目录（`hooks/toc.py`）、
整站/页面统计（`mkdocs-statistics-plugin` 0.1.5）与 Git 创建/更新日期
（`mkdocs-git-revision-date-localized-plugin` 1.4.7）由构建预处理层
`tools/notebook_build.py` 按原口径复刻：它先生成暂存内容 `.migration/docs`，
再交给 Zensical 构建。**`docs/` 仍是唯一人工编辑的笔记源**，原始笔记内容不因迁移而改动。

## 本地构建 / Build（Zensical）

构建脚本会用**创建虚拟环境时的同一个解释器**启动 Zensical（`sys.executable -m zensical`），
所以下面的命令必须显式使用 `.venv-zensical` 内的 Python（或先激活环境），不要改用全局 `python`。

```powershell
# Windows PowerShell
python -m venv .venv-zensical
.venv-zensical\Scripts\python.exe -m pip install -r requirements-zensical.txt

.venv-zensical\Scripts\python.exe tools\notebook_build.py serve    # 预览 http://127.0.0.1:8001/
.venv-zensical\Scripts\python.exe tools\notebook_build.py build    # 严格构建 + 产物完整性门禁
.venv-zensical\Scripts\python.exe tools\notebook_build.py prepare  # 只生成 .migration/docs 暂存内容
```

```shell
# Linux / macOS
python -m venv .venv-zensical
.venv-zensical/bin/python -m pip install -r requirements-zensical.txt
.venv-zensical/bin/python tools/notebook_build.py serve
.venv-zensical/bin/python tools/notebook_build.py build
.venv-zensical/bin/python tools/notebook_build.py prepare
```

也可以先激活环境再使用 `python`：Windows `.venv-zensical\Scripts\Activate.ps1`，
Linux/macOS `source .venv-zensical/bin/activate`。

`serve` 会在原始 `docs/`、`includes/`、`hooks/templates/toc.html` 变化**以及 Git HEAD 变化**后
自动重新 prepare（提交后日期与目录时间会刷新），再由 Zensical 刷新预览；生成的
`.migration/`、`site-zensical/`、`.venv-zensical/` 均不入库。

回归测试（front matter 兼容性、持续预览日期刷新、构建产物完整性门禁与重试）：

```shell
.venv-zensical\Scripts\python.exe tools\test_notebook_build.py   # Windows
.venv-zensical/bin/python tools/test_notebook_build.py           # Linux/macOS
```

## 回退构建 / Fallback（Material for MkDocs）

```shell
pip install -r requirements.txt
mkdocs serve      # http://127.0.0.1:8001/notebook/
mkdocs build      # 生成静态站点到 site/
```

## 部署 / Deploy

推送到 `main` 后由 GitHub Actions 自动执行 `python tools/notebook_build.py build`，
随后用 `ghp-import` 把 `site-zensical/` 发布到 `gh-pages` 分支（Pages 仍为 legacy + `gh-pages`）。

回退发布：先暂停自动发布，确认没有进行中/排队的 Deploy Docs 运行，再发布已知良好的 Material 产物；
否则运行中的 workflow 或回退后的 `main` push 会重新用 Zensical 覆盖 `gh-pages`。

```shell
# 1) 暂停自动发布者（GitHub CLI）
gh workflow disable "Deploy Docs"
gh run list --workflow "Deploy Docs" --limit 20   # 确认没有 in_progress / queued
# 如有进行中/排队运行：gh run cancel <run-id>，再复查一次

# 2) 发布 Material 产物
pip install -r requirements.txt ghp-import==2.1.0
mkdocs build -d site-rollback
ghp-import -n -p -f -r origin -b gh-pages site-rollback

# 3) 稳定后若要继续用 Zensical，再重新启用自动发布
gh workflow enable "Deploy Docs"
```

完整回退 runbook（含归档产物位置与重新启用条件）见 [`MIGRATION.md`](./MIGRATION.md) §7。

## Acknowledgement / 致谢

- 首页的全息展示卡片（the holographic homepage card）改编自
  [simeydotme/pokemon-cards-css](https://github.com/simeydotme/pokemon-cards-css/)，
  并经由 [TonyCrane/note-homepage-cards](https://github.com/TonyCrane/note-homepage-cards/) 适配到 MkDocs。
- 主题与样式定制参考了 [@TonyCrane](https://github.com/TonyCrane/) 与 [@NoughtQ](https://github.com/noughtq)。
- 分区索引目录的原始实现来自 [TonyCrane/note](https://github.com/TonyCrane/note)（CC BY 4.0），
  本仓库在其基础上加固并适配 `navigation.instant`；迁移后由 `tools/notebook_build.py` 复用同一算法。
- 灯箱使用 [GLightbox](https://github.com/biati-digital/glightbox)（MIT，© 2018 Biati Digital）。
  Zensical 构建原先会在运行时从 unpkg CDN 拉取该库，本仓库将 MIT 许可的 `glightbox.min.js/.css`
  收编到 `docs/javascripts/vendor/` 与 `docs/stylesheets/vendor/` 自维护（许可原文见
  [`LICENSE.glightbox`](./LICENSE.glightbox)）。

## License / 许可

- 首页卡片相关的代码与样式（`docs/javascripts/card.js`、`docs/stylesheets/cards/*`）
  沿用上游 [pokemon-cards-css](https://github.com/simeydotme/pokemon-cards-css/) 的
  **GPL-3.0** 许可，完整许可文本见
  [`LICENSE.pokemon-cards-css`](./LICENSE.pokemon-cards-css)（© 2022 Simon Goellner, [@simeydotme](https://github.com/simeydotme/)）。
- 除上述卡片组件外，本仓库中的笔记内容为作者原创，版权归 Vigilux 所有。

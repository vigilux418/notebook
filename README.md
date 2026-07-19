# Vigilux 的笔记本 · Vigilux's Notebook

个人学习笔记，基于 [MkDocs](https://www.mkdocs.org/) + [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) 构建。

在线阅读 / Live site: <https://vigilux.top/notebook/>
（镜像 / mirror: <https://vigilux418.github.io/notebook/>）

## 本地构建 / Build

```shell
pip install -r requirements.txt
mkdocs serve      # 本地预览 http://127.0.0.1:8001/notebook/
mkdocs build      # 生成静态站点到 site/
```

推送到 `main` 后由 GitHub Actions 自动 `mkdocs gh-deploy` 部署到 `gh-pages`。

## Acknowledgement / 致谢

- 首页的全息展示卡片（the holographic homepage card）改编自
  [simeydotme/pokemon-cards-css](https://github.com/simeydotme/pokemon-cards-css/)，
  并经由 [TonyCrane/note-homepage-cards](https://github.com/TonyCrane/note-homepage-cards/) 适配到 MkDocs。
- 主题与样式定制参考了 [@TonyCrane](https://github.com/TonyCrane/) 与 [@NoughtQ](https://github.com/noughtq)。

## License / 许可

- 首页卡片相关的代码与样式（`docs/javascripts/card.js`、`docs/stylesheets/cards/*`）
  沿用上游 [pokemon-cards-css](https://github.com/simeydotme/pokemon-cards-css/) 的
  **GPL-3.0** 许可，完整许可文本见
  [`LICENSE.pokemon-cards-css`](./LICENSE.pokemon-cards-css)（© 2022 Simon Goellner, [@simeydotme](https://github.com/simeydotme/)）。
- 除上述卡片组件外，本仓库中的笔记内容为作者原创，版权归 Vigilux 所有。

---
comments: true
---

# MkDocs建站指南

> 全文主要参考资料：
>
> [**Material for MkDocs官方文档**](https://squidfunk.github.io/mkdocs-material/)
>
> [**MkDocs中文文档**](https://hellowac.github.io/mkdocs-docs-zh/)

> 作为一名电脑小白，如何打造自己的线上笔记本呢？
>
> 在这个流程中，我们将学会`Mkdocs`建站的基本流程，即使是电脑小白也能轻易上手！

<font color=red>**[MkDocs](https://markdown-docs-zh.readthedocs.io/zh-cn/latest/)为`Mkdocs`的中文官方文档**</font>

## 为什么选择`Mkdocs`?

**核心优势**：

- **任意托管**：`Mkdocs`可以构建完全的静态`HTML`站点，可以将它托管到`GitHub pages`等任意地方。

- **大量主题**：默认包含大量美观的主题。
- **即时预览**：内建的开发服务器使你在撰写文档的时候就即时预览。它甚至能在保存更改时自动载入，只需刷新浏览器就可以查看更改。
- **易于配置**：可以配置文档主题。
- **交叉索引**：使用`MkDocs`链接语法创建交叉索引。

`MkDocs`是一个用于创建项目文档的 **快速**，**简单**，**完美华丽**的静态站点生成器。文档源码使用 `Markdown`来撰写，用一个`YAML`文件作为配置文档。

## 环境准备

需要`Python`和`Python package manager pip`来安装`MkDocs`。

可以通过以下命令查看是否安装了上述依赖：

```cmd
$ python --version
Python 3.13.5
$ pip --version
pip 25.2
```

使用`pip`安装`mkdocs`：

```cmd
$ pip install mkdocs
```

运行`mkdocs -h`以检查是否正确安装。

```cmd
$ mkdocs -h
Usage: mkdocs [OPTIONS] COMMAND [ARGS]...
  MkDocs - Project documentation with Markdown.
Options:...
Commands:...
```

## `Mkdocs`初始化（本地搭建）

### 开始

输入以下命令以开启一个新项目。

```cmd
$ mkdocs new 你的项目名
$ cd 你的项目名
```

`MkDocs`包含了一个内建的服务器以预览当前文档。控制台切换当前目录到 `mkdocs.yml` 配置文件相同文件夹，输入 `mkdocs serve` 命令以启动内建服务器：

```cmd
$ mkdocs serve
Running at: http://127.0.0.1:8001/ #以你的实际网址为准
```

在浏览器中打开 http://127.0.0.1:8001/ ，编辑 `docs/index.md` 文件并保存，刷新浏览器你将看到文档被同步更新。

#### 添加导航条

要为文档添加导航条, 只需在配置文件中添加导航条需要的标题和排序即可：

```yaml
pages:
- [index.md, Home]
- [about.md, About]
```

刷新浏览器即可看到`Home`和`About`导航栏目。

#### 站点生成

通过以下命令生成文档。

```cmd
$ mkdocs build
```

一段时间后，可能有文件被从源码中移除了，但是相关的文档仍残留在 `site` 目录中。在构建命令中添加 `--clean` 参数即可移除这些文档。

```cmd
$ mkdocs build --clean
```

#### 发布

`MkDocs`生成的文档只包含静态文件，因此你可以将文档部署到任意地方。

### Material主题搭建

#### 安装

通过`pip`安装`Material`：

```cmd
$ pip install mkdocs-material
```

#### 配置

只需在`mkdocs.yml`中添加以下行即可**启用主题**。

```yaml
theme: 
  name: material
```

## 发布网站

### 手动部署项目文档

```cmd
$ mkdocs gh-deploy --force
```

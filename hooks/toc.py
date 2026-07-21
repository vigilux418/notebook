# -*- coding: utf-8 -*-
"""
自定义「分区索引目录」MkDocs hook。

在任意 Markdown 页面里写一段被 {{ BEGIN_TOC }} / {{ END_TOC }} 包裹的 YAML：

    {{ BEGIN_TOC }}
    - 分区标题:
        - index: some/dir/           # 可选，给该分区标题本身加一个跳转链接
        - 子条目名: some/dir/child/    # 链接写页面 URL（相对“当前页所在目录”）
        - 子条目名[note]: other/       # [note] -> “课程笔记”标签
        - 子条目名[lab]:  lab/         # [lab]  -> “实验报告”标签
    {{ END_TOC }}

hook 会把它渲染成带「字数 / 代码行数 / 阅读时长 / 最近更新时间」的可折叠卡片目录。
折叠交互与“x days ago”相对时间由全局脚本 docs/javascripts/toc_index.js 负责
（订阅 document$，兼容 navigation.instant），本文件只产出静态 HTML。

──────────────────────────────────────────────────────────────────────────────
署名（CC BY 4.0）：本 hook 及其配套模板/统计逻辑改编自
    TonyCrane/note —— https://github.com/TonyCrane/note  (hooks/toc.py, hooks/utils/toc.py)
    Copyright (c) 2022-2025 TonyCrane (鹤翔万里)
    Licensed under Creative Commons Attribution 4.0 International (CC BY 4.0)
    https://creativecommons.org/licenses/by/4.0/
本文件为「修改版」：已合并原 utils/toc.py 为单文件、加固 .ignored-commits 缺失场景、
适配本仓库的 navigation.instant（交互逻辑外移到全局 JS）。—— Vigilux, 2026
──────────────────────────────────────────────────────────────────────────────
"""
import os
import re
import time
import logging

import yaml
from jinja2 import Template

from mkdocs.config.defaults import MkDocsConfig
from mkdocs.structure.pages import Page
from mkdocs.structure.files import Files

try:
    from git import Repo
    _HAS_GIT = True
except Exception:  # GitPython 缺失或无 git 可执行文件时优雅降级
    _HAS_GIT = False

# 可用环境变量 TOC=0 关闭（例如极速预览时）。默认开启。
enabled = os.getenv("TOC", "1") == "1"
logger = logging.getLogger("mkdocs.hooks.toc")

HOOKS_DIR = os.path.dirname(os.path.realpath(__file__))
TEMPLATE_PATH = os.path.join(HOOKS_DIR, "templates", "toc.html")
IGNORE_PATH = os.path.join(HOOKS_DIR, "..", ".ignored-commits")

with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
    TEMPLATE = f.read()

# 加固：本仓库通常没有 .ignored-commits。原版无条件 open() 会 FileNotFoundError
# 直接让整个 build 崩溃 —— 这里改为“存在才读”。
if os.path.exists(IGNORE_PATH):
    with open(IGNORE_PATH, "r", encoding="utf-8") as f:
        IGNORE_COMMITS = [
            ln.strip() for ln in f if ln.strip() and not ln.startswith("#")
        ]
else:
    IGNORE_COMMITS = []

logger.info(
    "hook - toc (分区索引目录) %s%s",
    "已启用" if enabled else "已禁用",
    "" if _HAS_GIT else "（未检测到 GitPython，更新时间将回退为构建时刻）",
)


# ── 字数 / 代码行数 / 阅读时长 ────────────────────────────────────────────────
def _clean_markdown(markdown: str):
    codes = re.findall(r"```[^\n].*?```", markdown, re.S)
    markdown = re.sub(r"```[^\n].*?```", "", markdown, flags=re.DOTALL | re.MULTILINE)
    markdown = re.sub(r"<!--.*?-->", "", markdown, flags=re.DOTALL | re.MULTILINE)
    markdown = markdown.replace("\t", "    ")
    markdown = re.sub(r"[ ]{2,}", "    ", markdown)
    markdown = re.sub(r"^\[[^]]*\][^(].*", "", markdown, flags=re.MULTILINE)
    markdown = re.sub(r"{#.*}", "", markdown)
    markdown = markdown.replace("\n", " ")
    markdown = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", markdown)
    markdown = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", markdown)
    markdown = re.sub(r"</?[^>]*>", "", markdown)
    markdown = re.sub(r"[#*`~\-–^=<>+|/:]", "", markdown)
    markdown = re.sub(r"\[[0-9]*\]", "", markdown)
    markdown = re.sub(r"[0-9#]*\.", "", markdown)
    return markdown, codes


def _words_count(markdown: str):
    md, codes = _clean_markdown(markdown)
    chinese = "".join(re.findall(r"[一-龥]", md))
    english = " ".join(re.findall(r"[a-zA-Z0-9]*?(?![a-zA-Z0-9])", md))
    words = len(chinese) + len(english.split())
    code_lines = sum(max(len(c.splitlines()) - 2, 0) for c in codes)
    read_time = round(words / 300 + code_lines / 80)
    return words, code_lines, read_time


def _resolve(path, base):
    """把 TOC 里写的 URL（相对当前页目录）映射回 docs 下的 .md 文件或目录。"""
    return os.path.join(base, path)


def get_statistics(path, base):
    words = codes = read_time = 0
    p = _resolve(path, base)
    if os.path.isdir(p):
        for root, _dirs, files in os.walk(p):
            for file in files:
                if file.endswith(".md"):
                    with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                        w, c, r = _words_count(f.read())
                        words += w
                        codes += c
                        read_time += r
    else:
        file = (p[:-1] if p.endswith("/") or p.endswith(os.sep) else p) + ".md"
        if os.path.exists(file):
            with open(file, "r", encoding="utf-8") as f:
                words, codes, read_time = _words_count(f.read())
    return words, codes, read_time


# ── 最近更新时间（git 最后一次提交）────────────────────────────────────────────
_repo_cache = {}


def _get_repo(path):
    d = path if os.path.isdir(path) else os.path.dirname(path)
    if d not in _repo_cache:
        _repo_cache[d] = Repo(d, search_parent_directories=True).git
    return _repo_cache[d]


def _check_ignore(sha, path, ignore_commits):
    for ignore in ignore_commits:
        if isinstance(ignore, str):
            if sha.startswith(ignore):
                return True
        else:  # dict: {filename: sha}
            filename = list(ignore.keys())[0]
            if path.endswith(filename) and sha.startswith(ignore[filename]):
                return True
    return False


def _latest_commit_ts(path, ignore_commits):
    if not _HAS_GIT:
        return int(time.time())
    try:
        realpath = os.path.realpath(path)
        repo = _get_repo(realpath)
        if ignore_commits:
            commits = repo.log(realpath, format="%H %at", follow=True)
            ts = ""
            for line in commits.splitlines():
                sha, t = line.split()
                if _check_ignore(sha, path, ignore_commits):
                    continue
                ts = t
                break
        else:
            ts = repo.log(realpath, format="%at", n=1)
        return int(ts) if ts else int(time.time())
    except Exception:
        # 文件未纳入 git、仓库异常等：回退到当前时刻，绝不让 build 崩。
        return int(time.time())


def get_update_time(path, base, ignore_commits):
    p = _resolve(path, base)
    if os.path.isdir(p):
        t = 0
        for root, _dirs, files in os.walk(p):
            for file in files:
                if len(files) != 1 and file == "index.md":
                    continue
                if file.endswith(".md"):
                    t = max(t, _latest_commit_ts(os.path.join(root, file), ignore_commits))
        return t
    file = (p[:-1] if p.endswith("/") or p.endswith(os.sep) else p) + ".md"
    if os.path.exists(file):
        return _latest_commit_ts(file, ignore_commits)
    return 0


# ── MkDocs hook 入口 ──────────────────────────────────────────────────────────
def on_page_markdown(
    markdown: str, page: Page, config: MkDocsConfig, files: Files, **kwargs
) -> str:
    if not enabled:
        return markdown
    if "{{ BEGIN_TOC }}" not in markdown or "{{ END_TOC }}" not in markdown:
        return markdown
    toc_yml = markdown.split("{{ BEGIN_TOC }}")[1].split("{{ END_TOC }}")[0]
    # safe_load：TOC 块只含 list/dict/str/num；不允许 !!python 等构造任意对象的标签。
    toc = yaml.safe_load(toc_yml)
    toc_items = _get_toc_items(toc, os.path.dirname(page.file.abs_src_path))
    toc_html = Template(TEMPLATE).render(items=toc_items)
    # 用函数替换，避免渲染结果里出现的 \g、\1 等被 re 当成反向引用而报错。
    return re.sub(
        r"\{\{ BEGIN_TOC \}\}.*\{\{ END_TOC \}\}",
        lambda _m: toc_html,
        markdown,
        flags=re.IGNORECASE | re.DOTALL,
    )


def _get_toc_items(toc, base):
    ret = []
    for i, part in enumerate(toc):
        item = {"n": i}
        title = list(part.keys())[0]
        item["note"] = "[note]" in title
        item["title"] = title.replace("[note]", "")
        details = []
        for d in part[list(part.keys())[0]]:
            key = list(d.keys())[0]
            value = d[key]
            if key == "index":
                item["link"] = value
                continue
            t = key
            detail = {"note": "[note]" in t, "lab": "[lab]" in t}
            t = t.replace("[note]", "").replace("[lab]", "")
            detail["title"] = t
            detail["link"] = value
            detail["words"], detail["codes"], detail["read_time"] = get_statistics(value, base)
            detail["update_time"] = get_update_time(value, base, IGNORE_COMMITS)
            detail["lock"] = "🔒" in t
            details.append(detail)
        details.sort(key=lambda x: x["update_time"], reverse=True)
        item["contents"] = details
        ret.append(item)
    return ret

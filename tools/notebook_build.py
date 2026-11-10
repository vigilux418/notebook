#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Vigilux 笔记站 Zensical 构建入口（迁移过渡层）。

背景
----
原站点基于 MkDocs + Material for MkDocs，依赖 4 个 MkDocs 插件与 1 个 MkDocs Hook：

* ``mkdocs-statistics-plugin`` 0.1.5 —— 全站统计与按页阅读统计；
* ``mkdocs-git-revision-date-localized-plugin`` 1.4.7 —— 页脚 Git 创建/更新日期；
* ``hooks/toc.py`` —— ``{{ BEGIN_TOC }}`` 分区索引目录；
* ``mkdocs-macros-plugin`` / ``meta`` / ``search`` / ``glightbox`` —— Zensical 0.1.0 有内建兼容实现，保留在配置中。

Zensical 0.1.0 不会执行 MkDocs 插件与 Hook（见迁移调研报告第 3、5 节）。因此本脚本在
``zensical build`` 之前生成一份**暂存内容** ``.migration/docs``：它把上述三项能力按原实现
的口径预先写入页面，原 ``docs/`` 仍是唯一人工编辑源，不注入迁移专用语法。

命令
----
``python tools/notebook_build.py prepare``
    重建暂存内容（目录 / 整站与页面统计 / Git 日期 / 友链头像路径适配）。
``python tools/notebook_build.py build [--no-strict]``
    prepare 后执行 ``zensical build --clean --strict``，产物在 ``site-zensical/``。
``python tools/notebook_build.py serve``
    prepare 后启动 ``zensical serve``，并监听原始 docs/includes/Hook 模板，变更时重新 prepare。

来源与许可
----------
* 目录逻辑与统计口径改编自 TonyCrane/note 的 ``hooks/toc.py``（CC BY 4.0，
  Copyright (c) 2022-2025 TonyCrane 鹤翔万里），并经本仓库加固（单文件、无 Hook API 依赖）。
  本文件保留其算法与 HTML 约定，只把 MkDocs Hook 入口替换为预处理函数。
* 统计逻辑复刻 ``mkdocs-statistics-plugin`` 0.1.5（MIT，Copyright (c) 2022 Zhou Yichao）。
* Git 日期逻辑复刻 ``mkdocs-git-revision-date-localized-plugin`` 1.4.7（MIT，
  Copyright (c) Tim Vink）；日期格式使用 Babel 的 zh long datetime 输出，与插件完全一致。
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote

import yaml
from babel.dates import format_date, get_timezone
from jinja2 import Template

# ---------------------------------------------------------------------------
# 路径与常量
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"
INCLUDES_DIR = ROOT / "includes"
STAGE_DIR = ROOT / ".migration" / "docs"
MIGRATION_DIR = ROOT / ".migration"
CONFIG_FILE = ROOT / "mkdocs.zensical.yml"
TOC_TEMPLATE_PATH = ROOT / "hooks" / "templates" / "toc.html"
IGNORED_COMMITS_PATH = ROOT / ".ignored-commits"

#: statistics 0.1.5 默认忽略的代码围栏语言（不计入代码行数，内容也不计入字数）
STATISTICS_IGNORE_LANGUAGES = ("mermaid", "math")
STATISTICS_WORDS_PER_MINUTE = 300
STATISTICS_CODELINES_PER_MINUTE = 80
PAGE_CHECK_METADATA = "comments"

#: git-revision-date-localized 配置（与原 mkdocs.yml 完全一致）
GIT_DATE_EXCLUDE = ("index.md",)
GIT_DATE_TIMEZONE = "Asia/Shanghai"
GIT_DATE_LOCALE = "zh"

#: 页面统计模板：逐字复刻 mkdocs-statistics-plugin 0.1.5 的内置模板。
PAGE_STATISTICS_TEMPLATE = (
    '<div markdown="1" style="margin-top: -30px; font-size: 0.75em; opacity: 0.7;">\n'
    ":material-circle-edit-outline: 约 {{ words }} 个字 "
    "{% if code_lines != 0 %}:fontawesome-solid-code: {{ code_lines }} 行代码 {% endif %}"
    "{% if page_images %}{% if images != 0 %}:material-image-multiple-outline: {{ images }} 张图片 {% endif %}{% endif %}"
    "{% if page_read_time %}:material-clock-time-two-outline: "
    "{% if read_time == 0 %}预计阅读时间不到 1 分钟{% else %}预计阅读时间 {{ read_time }} 分钟{% endif %}"
    "{% endif %}\n"
    "</div>"
)

#: 只对 links.md 生效的头像路径适配（报告 §5.5：不要全库替换）。
AVATAR_SOURCE_PATTERN = re.compile(
    r'(<img\s+class="ava"\s+src=")\.\./images/(lemoon1206\.jpg")'
)
AVATAR_REL_PATH = "links.md"

#: 构建产物完整性门禁：Zensical 0.1.0 必须产出的 4 个主题样式（classic/modern × main/palette）。
#: 复审曾在其 beta 构建中出现偶发漏写其中 1 个 CSS 且退出码为 0，因此构建后必须显式断言。
THEME_CSS_PATTERNS = (
    "assets/stylesheets/classic/main*.min.css",
    "assets/stylesheets/classic/palette*.min.css",
    "assets/stylesheets/modern/main*.min.css",
    "assets/stylesheets/modern/palette*.min.css",
)

#: 站点部署前缀（与 mkdocs.yml 的 site_url 路径一致）：根路径引用需以该前缀开头。
SITE_URL_PREFIX = "/notebook/"

#: 本地引用检查时跳过的 URL 前缀（外部/特殊协议/纯锚点）。
URL_SKIP_PREFIXES = (
    "#",
    "http://",
    "https://",
    "//",
    "mailto:",
    "javascript:",
    "data:",
    "tel:",
)

LOG = logging.getLogger("notebook_build")


# ---------------------------------------------------------------------------
# 通用工具
# ---------------------------------------------------------------------------


def rel_posix(path: Path) -> str:
    """返回相对 docs/ 的 POSIX 风格路径（与 MkDocs 的 src_path 一致）。"""
    return path.relative_to(DOCS_DIR).as_posix()


def read_text(path: Path) -> str:
    """按 MkDocs 读取页面的方式读取（utf-8-sig，universal newlines）。"""
    return path.read_text(encoding="utf-8-sig")


#: MkDocs 的 YAML front matter 正则：起始 ``---``，结束标记可以是 ``---`` 或 ``...``。
#: 与 ``mkdocs.utils.meta.YAML_RE`` 语义对齐（结束标记后必须换行，正文去掉开头空行）。
FRONT_MATTER_RE = re.compile(
    r"\A---[ \t]*\r?\n(.*?\r?\n)(?:\.{3}|-{3})[ \t]*\r?\n", re.UNICODE | re.DOTALL
)


def split_front_matter(text: str) -> tuple[dict, str, bool]:
    """拆分 YAML front matter 与正文。

    与 ``mkdocs.utils.meta.get_data`` 的 YAML 分支语义对齐：

    * 起始标记为 ``---``，结束标记同时接受 ``---`` 与合法的 ``...``；
    * 首个分隔行后的内容按 YAML 解析；非映射结果视为“无元数据”；
    * 若 YAML 解析失败，**保留完整原文**并返回 ``ok=False``，由调用方原样写出，
      避免静默剥掉用户的元数据块。

    返回值：``(meta, body, ok)``。无 front matter 时返回 ``({}, text, True)``。
    """
    match = FRONT_MATTER_RE.match(text)
    if not match:
        # MkDocs 还支持无分隔符的 MultiMarkdown 风格元数据；本项目笔记未使用该写法，
        # 这里保持正文原样，与历史行为一致（如需支持应补兼容实现）。
        return {}, text, True
    meta_text = match.group(1)
    body = text[match.end() :].lstrip("\n")
    try:
        meta = yaml.safe_load(meta_text)
    except yaml.YAMLError as exc:
        LOG.warning("front matter YAML 解析失败，按原样保留该页内容：%s", exc)
        return {}, text, False
    if not isinstance(meta, dict):
        LOG.warning("front matter 不是 YAML 映射，按原样保留该页内容")
        return {}, text, False
    return meta, body, True


def dump_front_matter(meta: dict, body: str) -> str:
    """把元数据与正文组合为页面文本（暂存内容允许重排 front matter）。

    MkDocs 允许 ``...`` 作为 front matter 结束标记，但 Zensical 0.1.0 的兼容解析
    只识别 ``---``；这里统一用 ``---`` 重新序列化，保证两种引擎对暂存内容的理解一致。
    """
    if meta:
        front = yaml.safe_dump(
            meta,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
            width=1000,
        )
        return f"---\n{front}---\n{body}"
    return body


# ---------------------------------------------------------------------------
# Git 查询（复刻 git-revision-date-localized 1.4.7 与 hooks/toc.py 的口径）
# ---------------------------------------------------------------------------


class GitError(RuntimeError):
    """git 命令执行失败。"""


_GIT_TIMESTAMP_CACHE: dict[tuple[str, bool], int] = {}
_TOC_TIME_CACHE: dict[str, int] = {}


def _git(args: list[str]) -> str:
    """在仓库根目录执行 git 命令并返回 stdout（去首尾空白）。"""
    proc = subprocess.run(
        ["git", *args],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        raise GitError(
            f"git {' '.join(args)} 失败（exit={proc.returncode}）：{proc.stderr.strip()}"
        )
    return proc.stdout.strip()


def _realpath(path: Path) -> str:
    return str(path.resolve())


def git_page_timestamps(path: Path) -> tuple[int, int]:
    """返回页面的 (创建时间, 最后更新时间)，单位 unix 秒。

    复刻 git-revision-date-localized 1.4.7 的实际生效口径：
    * 创建：``--diff-filter=Ar``（只选 Added，排除 rename），``--follow``，取最旧提交；
    * 更新：插件先以 ``-1 --diff-filter=r --follow --ignore-all-space
      --ignore-blank-lines`` 查询，但随后会用普通 ``git log -n1 --format="%H %at"``
      的返回值覆盖，因此**最终生效的是普通最后提交**（本项目无 ignored-commits，
      两条查询结果恰好一致，此处仍按插件语义实现）；
    * 取 Git **作者时间** ``%at``；
    * 查询失败或文件无历史时回退到构建时刻（``fallback_to_build_date: true``）。
    """
    real = _realpath(path)
    if (real, False) in _GIT_TIMESTAMP_CACHE:
        return _GIT_TIMESTAMP_CACHE[(real, False)], _GIT_TIMESTAMP_CACHE[(real, True)]
    try:
        created_raw = _git(
            [
                "log",
                "--format=%at",
                "--diff-filter=Ar",
                "--no-show-signature",
                "--follow",
                "--",
                real,
            ]
        )
        # 插件的第一条“最近更新”查询，其结果会被下面普通 log 覆盖，但保留以对齐异常路径。
        _git(
            [
                "log",
                "-1",
                "--format=%at",
                "--diff-filter=r",
                "--no-show-signature",
                "--follow",
                "--ignore-all-space",
                "--ignore-blank-lines",
                "--",
                real,
            ]
        )
        # 实际生效的“最后更新”：普通 git log -n1，格式 "%H %at"（无 follow/diff 过滤）
        latest_raw = _git(
            ["log", "-1", "--format=%H %at", "--no-show-signature", "--", real]
        )
    except GitError as exc:  # 仓库异常 / 非 git 环境：回退构建时刻
        LOG.warning("Git 日期查询失败，回退构建时刻：%s（%s）", path, exc)
        now = int(time.time())
        _GIT_TIMESTAMP_CACHE[(real, False)] = now
        _GIT_TIMESTAMP_CACHE[(real, True)] = now
        return now, now

    created = int(created_raw.split()[-1]) if created_raw else int(time.time())
    updated = int(time.time())
    if latest_raw:
        # 与插件一致：按倒序扫描，跳过 ignored-commits（本项目未配置，故取第一条）
        for line in latest_raw.splitlines():
            if not line:
                updated = int(time.time())
                break
            _sha, _, timestamp = line.partition(" ")
            updated = int(timestamp)
            break
    if not created_raw:
        LOG.warning("%s 没有创建提交记录，回退构建时刻", path)
    # 插件对 first > last 的异常历史做钳制（issues/111）
    if created > updated:
        LOG.warning("%s 的创建时间晚于更新时间，按插件行为钳制", path)
        created = updated
    _GIT_TIMESTAMP_CACHE[(real, False)] = created
    _GIT_TIMESTAMP_CACHE[(real, True)] = updated
    return created, updated


def format_git_datetime(timestamp: int) -> str:
    """复刻插件 ``type: datetime`` + ``add_spans=True`` 的 HTML 输出。"""
    utc = datetime.fromtimestamp(int(timestamp), tz=timezone.utc)
    local = utc.replace(tzinfo=get_timezone("UTC")).astimezone(
        get_timezone(GIT_DATE_TIMEZONE)
    )
    date_long = format_date(local, format="long", locale=GIT_DATE_LOCALE)
    datetime_text = " ".join([date_long, local.strftime("%H:%M:%S")])
    title_text = " ".join([date_long, local.strftime("%H:%M:%S %Z")])
    return (
        '<span class="git-revision-date-localized-plugin '
        'git-revision-date-localized-plugin-datetime" '
        f'title="{title_text}">{datetime_text}</span>'
    )


def _toc_latest_commit_ts(path: Path, ignore_commits: list) -> int:
    """复刻 hooks/toc.py 的 ``_latest_commit_ts``（不带 diff 过滤的 ``git log -1``）。"""
    cache_key = str(path)
    if cache_key in _TOC_TIME_CACHE:
        return _TOC_TIME_CACHE[cache_key]
    timestamp = int(time.time())
    try:
        real = _realpath(path)
        if ignore_commits:
            raw = _git(["log", "--format=%H %at", "--follow", "--", real])
            for line in raw.splitlines():
                sha, _, ts = line.partition(" ")
                if not _check_ignored_commit(sha, path, ignore_commits):
                    timestamp = int(ts)
                    break
        else:
            raw = _git(["log", "-1", "--format=%at", "--", real])
            if raw:
                timestamp = int(raw)
    except GitError:
        # 文件未纳入 git、仓库异常等：回退当前时刻，绝不让构建崩（与 Hook 一致）
        timestamp = int(time.time())
    _TOC_TIME_CACHE[cache_key] = timestamp
    return timestamp


def _check_ignored_commit(sha: str, path: Path, ignore_commits: list) -> bool:
    for ignore in ignore_commits:
        if isinstance(ignore, str):
            if sha.startswith(ignore):
                return True
        else:  # dict: {filename: sha}
            filename = list(ignore.keys())[0]
            if str(path).endswith(filename) and sha.startswith(ignore[filename]):
                return True
    return False


def load_ignored_commits() -> list:
    """读取仓库根的 ``.ignored-commits``（不存在时返回空表）。"""
    if not IGNORED_COMMITS_PATH.is_file():
        return []
    items = []
    for line in IGNORED_COMMITS_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            items.append(line)
    return items


# ---------------------------------------------------------------------------
# 分区索引目录（复刻 hooks/toc.py）
# ---------------------------------------------------------------------------


def _toc_clean_markdown(markdown: str) -> tuple[str, list[str]]:
    """复刻 hooks/toc.py 的 ``_clean_markdown``（与 statistics 口径不同）。"""
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


def _toc_words_count(markdown: str) -> tuple[int, int, int]:
    md, codes = _toc_clean_markdown(markdown)
    chinese = "".join(re.findall(r"[一-龥]", md))
    english = " ".join(re.findall(r"[a-zA-Z0-9]*?(?![a-zA-Z0-9])", md))
    words = len(chinese) + len(english.split())
    code_lines = sum(max(len(code.splitlines()) - 2, 0) for code in codes)
    read_time = round(words / 300 + code_lines / 80)
    return words, code_lines, read_time


def _toc_resolve(path: str, base: str) -> str:
    return os.path.join(base, path)


def _toc_statistics(path: str, base: str) -> tuple[int, int, int]:
    words = codes = read_time = 0
    resolved = _toc_resolve(path, base)
    if os.path.isdir(resolved):
        for root, _dirs, files in os.walk(resolved):
            for file in files:
                if file.endswith(".md"):
                    with open(os.path.join(root, file), "r", encoding="utf-8") as handle:
                        count_words, count_codes, count_read = _toc_words_count(
                            handle.read()
                        )
                        words += count_words
                        codes += count_codes
                        read_time += count_read
    else:
        file = (resolved[:-1] if resolved.endswith(("/", os.sep)) else resolved) + ".md"
        if os.path.exists(file):
            with open(file, "r", encoding="utf-8") as handle:
                words, codes, read_time = _toc_words_count(handle.read())
    return words, codes, read_time


def _toc_update_time(path: str, base: str, ignore_commits: list) -> int:
    resolved = _toc_resolve(path, base)
    if os.path.isdir(resolved):
        timestamp = 0
        for root, _dirs, files in os.walk(resolved):
            for file in files:
                if len(files) != 1 and file == "index.md":
                    continue
                if file.endswith(".md"):
                    timestamp = max(
                        timestamp,
                        _toc_latest_commit_ts(
                            Path(os.path.join(root, file)), ignore_commits
                        ),
                    )
        return timestamp
    file = (resolved[:-1] if resolved.endswith(("/", os.sep)) else resolved) + ".md"
    if os.path.exists(file):
        return _toc_latest_commit_ts(Path(file), ignore_commits)
    return 0


def build_toc_items(toc: list, base: str, ignore_commits: list) -> list[dict]:
    """复刻 hooks/toc.py 的 ``_get_toc_items``。"""
    result = []
    for index, part in enumerate(toc):
        item: dict = {"n": index}
        title = list(part.keys())[0]
        item["note"] = "[note]" in title
        item["title"] = title.replace("[note]", "")
        details = []
        for detail_source in part[list(part.keys())[0]]:
            key = list(detail_source.keys())[0]
            value = detail_source[key]
            if key == "index":
                item["link"] = value
                continue
            detail = {"note": "[note]" in key, "lab": "[lab]" in key}
            detail["title"] = key.replace("[note]", "").replace("[lab]", "")
            detail["link"] = value
            (
                detail["words"],
                detail["codes"],
                detail["read_time"],
            ) = _toc_statistics(value, base)
            detail["update_time"] = _toc_update_time(value, base, ignore_commits)
            detail["lock"] = "🔒" in key
            details.append(detail)
        details.sort(key=lambda entry: entry["update_time"], reverse=True)
        item["contents"] = details
        result.append(item)
    return result


def render_toc_block(body: str, page_src: Path, toc_template: Template, ignore_commits: list) -> str:
    """把页面中的 ``{{ BEGIN_TOC }}…{{ END_TOC }}`` 替换为卡片目录 HTML。"""
    if "{{ BEGIN_TOC }}" not in body or "{{ END_TOC }}" not in body:
        return body
    toc_yml = body.split("{{ BEGIN_TOC }}", 1)[1].split("{{ END_TOC }}", 1)[0]
    toc = yaml.safe_load(toc_yml)
    if not toc:
        LOG.warning("%s 的 TOC 块为空，保持原样", page_src)
        return body
    items = build_toc_items(toc, str(page_src.parent), ignore_commits)
    toc_html = toc_template.render(items=items)
    return re.sub(
        r"\{\{ BEGIN_TOC \}\}.*\{\{ END_TOC \}\}",
        lambda _match: toc_html,
        body,
        flags=re.IGNORECASE | re.DOTALL,
    )


# ---------------------------------------------------------------------------
# 统计（复刻 mkdocs-statistics-plugin 0.1.5）
# ---------------------------------------------------------------------------


def _statistics_split_markdown(markdown: str) -> tuple[str, list[str]]:
    """复刻 statistics 0.1.5 的 ``_clean_markdown`` + ``_filter_out_diagrams``。"""
    all_codes = re.findall(r"(~~~[^\n].*?~~~|```[^\n].*?```)", markdown, re.S)
    codes = []
    for code in all_codes:
        match = re.match(r"(`{3,}|~{3,})(?P<lang>\w*)", code.splitlines()[0])
        lang = match.group("lang") if match else ""
        if lang not in STATISTICS_IGNORE_LANGUAGES:
            codes.append(code)
    markdown = re.sub(
        r"(~~~[^\n].*?~~~|```[^\n].*?```)",
        "",
        markdown,
        flags=re.DOTALL | re.MULTILINE,
    )
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


def statistics_counts(markdown: str) -> tuple[int, int, int]:
    """返回 ``(words, code_lines, images)``，与插件 ``_words_count`` 逐字等价。"""
    images = len(re.findall("<img.*>", markdown)) + len(
        re.findall(r"!\[[^\]]*\]\([^)]*\)", markdown)
    )
    clean, codes = _statistics_split_markdown(markdown)
    chinese = "".join(re.findall(r"[\u4e00-\u9fa5]", clean))
    english = " ".join(re.findall(r"[a-zA-Z0-9]*?(?![a-zA-Z0-9])", clean))
    words = len(chinese) + len(english.split())
    code_lines = sum(len(code.splitlines()) - 2 for code in codes)
    return words, code_lines, images


def render_page_statistics(markdown: str) -> str:
    """在首个一级标题之后插入页面统计块（复刻插件 on_page_markdown 的插入方式）。"""
    words, code_lines, images = statistics_counts(markdown)
    read_time = round(
        words / STATISTICS_WORDS_PER_MINUTE
        + code_lines / STATISTICS_CODELINES_PER_MINUTE
    )
    content = Template(PAGE_STATISTICS_TEMPLATE).render(
        words=words,
        code_lines=code_lines,
        images=images,
        read_time=read_time,
        page_read_time=True,
        page_images=True,
    )
    lines = markdown.splitlines()
    h1 = -1
    for idx, line in enumerate(lines):
        if re.match(r"\s*# ", line):  # ATX
            h1 = idx
            break
        if re.match(r"=+\s*$", line) and idx > 0 and lines[idx - 1]:  # Setext
            h1 = idx
            break
    lines.insert(h1 + 1, content)
    return "\n".join(lines)


def replace_site_statistics_placeholders(body: str) -> str:
    """替换首页全站统计占位符（插件在 ``statistics: true`` 页面上执行）。"""
    replacements = {
        r"\{\{\s*pages\s*\}\}": str(GLOBAL_STATS["pages"]),
        r"\{\{\s*words\s*\}\}": str(GLOBAL_STATS["words"]),
        r"\{\{\s*codes\s*\}\}": str(GLOBAL_STATS["codes"]),
        r"\{\{\s*images\s*\}\}": str(GLOBAL_STATS["images"]),
    }
    for pattern, value in replacements.items():
        body = re.sub(pattern, value, body, flags=re.IGNORECASE)
    return body


def collect_site_statistics() -> dict:
    """复刻 statistics 0.1.5 ``on_files`` 的全站统计。"""
    pages = words = codes = images = 0
    for path in sorted(DOCS_DIR.rglob("*.md")):
        _meta, body, _ok = split_front_matter(read_text(path))
        page_words, page_codes, page_images = statistics_counts(body)
        pages += 1
        words += page_words
        codes += page_codes
        images += page_images
    return {"pages": pages, "words": words, "codes": codes, "images": images}


GLOBAL_STATS = {"pages": 0, "words": 0, "codes": 0, "images": 0}


# ---------------------------------------------------------------------------
# 暂存内容生成（prepare）
# ---------------------------------------------------------------------------


def _is_excluded_from_dates(src_path: str) -> bool:
    for glob in GIT_DATE_EXCLUDE:
        if fnmatch.fnmatchcase(src_path, glob):
            return True
        if os.sep != "/" and fnmatch.fnmatchcase(src_path.replace(os.sep, "/"), glob):
            return True
    return False


def _clean_stage_dir() -> None:
    """清空暂存目录；带路径安全检查，绝不删除 .migration 之外的内容。"""
    resolved = STAGE_DIR.resolve()
    migration_root = MIGRATION_DIR.resolve()
    if resolved == migration_root or migration_root not in resolved.parents:
        raise RuntimeError(f"暂存目录越界，拒绝清理：{resolved}")
    if resolved.name != "docs":
        raise RuntimeError(f"暂存目录名异常，拒绝清理：{resolved}")
    if resolved.exists():
        shutil.rmtree(resolved)
    resolved.mkdir(parents=True, exist_ok=True)


def _sync_stage_dir(expected: set[Path]) -> None:
    """增量模式：保留暂存根目录，只删除源中已不存在的文件。

    ``zensical serve`` 会监听暂存目录；预览期间若整体删除暂存目录，目标引擎
    的文件监听可能因目录消失而崩溃。因此 serve 的监听线程使用本函数同步删除，
    其余文件由后续写入覆盖。
    """
    STAGE_DIR.mkdir(parents=True, exist_ok=True)
    if not STAGE_DIR.exists():
        return
    for existing in sorted(STAGE_DIR.rglob("*"), reverse=True):
        if not existing.is_file():
            continue
        relative = existing.relative_to(STAGE_DIR)
        if relative not in expected:
            existing.unlink()
    # 清理空目录（自底向上）
    for existing in sorted(STAGE_DIR.rglob("*"), reverse=True):
        if existing.is_dir() and not any(existing.iterdir()):
            existing.rmdir()


def _process_page(
    source: Path, toc_template: Template, ignore_commits: list
) -> dict:
    """处理单个 Markdown 页面，返回待写入暂存的文本与统计标记（可在线程池中执行）。"""
    relative = source.relative_to(DOCS_DIR)
    src_path = rel_posix(source)
    source_text = read_text(source)
    meta, body, front_matter_ok = split_front_matter(source_text)
    meta = dict(meta)
    result = {
        "source": source,
        "relative": relative,
        "text": "",
        "toc_page": False,
        "toc_entries": 0,
        "page_stats": False,
        "dated": False,
    }

    if not front_matter_ok:
        # YAML 无法解析：保留完整原文（与 MkDocs get_data 一致），不注入统计/日期，
        # 避免静默丢失用户的元数据块或正文。
        result["text"] = source_text
        return result

    # 1) 页面统计（插件在 hooks/toc.py 之前执行，此处保持相同顺序）
    if not meta.get("nostatistics"):
        if meta.get("statistics"):
            body = replace_site_statistics_placeholders(body)
        hide = meta.get("hide") or []
        if (
            PAGE_CHECK_METADATA
            and meta.get(PAGE_CHECK_METADATA)
            and "statistics" not in hide
        ):
            body = render_page_statistics(body)
            result["page_stats"] = True

    # 2) 分区索引目录（hooks/toc.py 在全部插件之后执行）
    if "{{ BEGIN_TOC }}" in body:
        body = render_toc_block(body, source, toc_template, ignore_commits)
        result["toc_page"] = True
        result["toc_entries"] = body.count('<div class="item-primary">')

    # 3) 友链头像的精确路径适配（报告 §5.5：仅 links.md 一处）
    if src_path == AVATAR_REL_PATH:
        body, replacements = AVATAR_SOURCE_PATTERN.subn(r"\1images/\2", body)
        if replacements != 1:
            LOG.warning("links.md 头像路径适配预期 1 处，实际 %s 处", replacements)

    # 4) Git 日期写回 front matter（源路径查询，不查询暂存文件）
    if not _is_excluded_from_dates(src_path):
        created, updated = git_page_timestamps(source)
        meta["git_creation_date_localized"] = format_git_datetime(created)
        meta["git_revision_date_localized"] = format_git_datetime(updated)
        result["dated"] = True

    result["text"] = dump_front_matter(meta, body)
    return result


def prepare(incremental: bool = False) -> dict:
    """生成 ``.migration/docs`` 并返回构建摘要。

    ``incremental=True`` 供 ``serve`` 的监听线程使用：保留暂存根目录、只删除源中
    已不存在的文件，避免目标引擎监听目录时因目录被删除而崩溃。

    每轮 prepare 都会清空 Git 时间缓存；``serve`` 的监听快照还包含仓库 HEAD，
    因此新的提交会触发重新生成，日期与目录 ``data-ts`` 不会停留在旧值。
    """
    if not DOCS_DIR.is_dir():
        raise SystemExit(f"找不到源目录：{DOCS_DIR}")
    if not TOC_TEMPLATE_PATH.is_file():
        raise SystemExit(f"找不到目录模板：{TOC_TEMPLATE_PATH}")

    started = time.perf_counter()

    # Git 时间缓存只服务于单次 prepare：serve 会在同一进程内反复调用 prepare，
    # 若跨轮复用缓存，提交后的新日期/目录 data-ts 会停留在旧值。
    _GIT_TIMESTAMP_CACHE.clear()
    _TOC_TIME_CACHE.clear()

    global GLOBAL_STATS
    GLOBAL_STATS = collect_site_statistics()
    LOG.info(
        "全站统计：pages=%s words=%s codes=%s images=%s",
        GLOBAL_STATS["pages"],
        GLOBAL_STATS["words"],
        GLOBAL_STATS["codes"],
        GLOBAL_STATS["images"],
    )

    toc_template = Template(TOC_TEMPLATE_PATH.read_text(encoding="utf-8"))
    ignore_commits = load_ignored_commits()

    all_files = sorted(path for path in DOCS_DIR.rglob("*") if path.is_file())
    page_files = [path for path in all_files if path.suffix.lower() == ".md"]
    asset_files = [path for path in all_files if path.suffix.lower() != ".md"]

    if incremental:
        _sync_stage_dir({path.relative_to(DOCS_DIR) for path in all_files})
    else:
        _clean_stage_dir()

    # 静态资源按字节原样复制，保留子目录结构
    for source in asset_files:
        destination = STAGE_DIR / source.relative_to(DOCS_DIR)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)

    # Markdown 页面并行处理（Git 查询是主要耗时；页面之间互不依赖，顺序由排序保证）
    workers = max(1, min(8, os.cpu_count() or 1))
    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="prepare") as pool:
        rendered_pages = list(
            pool.map(lambda path: _process_page(path, toc_template, ignore_commits), page_files)
        )

    toc_pages = toc_entries = page_stats_pages = date_pages = 0
    for rendered in rendered_pages:
        destination = STAGE_DIR / rendered["relative"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(rendered["text"], encoding="utf-8", newline="\n")
        toc_pages += int(rendered["toc_page"])
        toc_entries += int(rendered["toc_entries"])
        page_stats_pages += int(rendered["page_stats"])
        date_pages += int(rendered["dated"])

    duration = time.perf_counter() - started
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generator": "tools/notebook_build.py prepare",
        "stage_dir": str(STAGE_DIR),
        "site_statistics": GLOBAL_STATS,
        "toc_pages": toc_pages,
        "toc_entries": toc_entries,
        "page_statistics_pages": page_stats_pages,
        "dated_pages": date_pages,
        "source_page_count": GLOBAL_STATS["pages"],
        "duration_seconds": round(duration, 3),
    }
    MIGRATION_DIR.mkdir(parents=True, exist_ok=True)
    (MIGRATION_DIR / "prepare-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    LOG.info(
        "暂存内容已生成：%s 页，目录 %s 组/约 %s 条，页面统计 %s 页，Git 日期 %s 页，耗时 %.2fs",
        GLOBAL_STATS["pages"],
        toc_pages,
        toc_entries,
        page_stats_pages,
        date_pages,
        duration,
    )
    return manifest


# ---------------------------------------------------------------------------
# 构建 / 预览
# ---------------------------------------------------------------------------


def _zensical_cli() -> list[str]:
    """优先使用当前解释器所在环境的 zensical 模块入口。"""
    return [sys.executable, "-m", "zensical"]


class _LocalRefParser(HTMLParser):
    """收集 HTML 起始标签中的 ``href`` / ``src`` 属性值。"""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.refs: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for name, value in attrs:
            if name.lower() in ("href", "src") and value:
                self.refs.append((name.lower(), value))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)


def _site_dir_from_config() -> Path:
    """从 ``mkdocs.zensical.yml`` 读取 site_dir；异常时回退默认目录。"""
    try:
        config = yaml.safe_load(CONFIG_FILE.read_text(encoding="utf-8")) or {}
        value = config.get("site_dir")
        if isinstance(value, str) and value:
            candidate = (ROOT / value).resolve()
            if candidate.is_relative_to(ROOT):
                return candidate
    except (OSError, yaml.YAMLError):
        pass
    return ROOT / "site-zensical"


def check_site_artifacts(site_dir: Path, expected_pages: int | None = None) -> list[str]:
    """检查构建产物完整性，返回问题清单（空列表表示通过）。

    复审建议（2026-11-10 第二轮）要求拦住“构建 exit 0 但产物缺失”的情况：

    1. classic/modern 变体的 main/palette 主题 CSS 均存在；
    2. 生成的页面数等于源 Markdown 页面数，且存在 404 页；
    3. 所有生成 HTML 的本地 ``href``/``src`` 都能解析到 site 目录内的实际文件
       （外部 URL、特殊协议与纯锚点跳过；根路径必须落在 ``/notebook/`` 前缀内）。
    """
    problems: list[str] = []
    if not site_dir.is_dir():
        return [f"站点目录不存在：{site_dir}"]
    root = site_dir.resolve()

    for pattern in THEME_CSS_PATTERNS:
        if not list(root.glob(pattern)):
            problems.append(f"缺少主题样式：{pattern}")

    pages = sorted(path for path in root.rglob("index.html"))
    if expected_pages is not None and len(pages) != expected_pages:
        problems.append(
            f"页面数量不符：生成 {len(pages)} 个 index.html，预期 {expected_pages} 个"
        )
    if not (root / "404.html").is_file():
        problems.append("缺少 404.html")

    missing: list[tuple[Path, str, str, str]] = []
    for page in sorted(root.rglob("*.html")):
        parser = _LocalRefParser()
        try:
            parser.feed(page.read_text(encoding="utf-8", errors="replace"))
        except (OSError, ValueError):
            problems.append(f"无法读取生成页：{page.relative_to(root).as_posix()}")
            continue
        for attr, raw in parser.refs:
            value = raw.strip()
            if not value or value.startswith(URL_SKIP_PREFIXES):
                continue
            path_part = value.split("#", 1)[0].split("?", 1)[0]
            if not path_part:
                continue
            path_part = unquote(path_part)
            if path_part.startswith("/"):
                if not path_part.startswith(SITE_URL_PREFIX):
                    missing.append(
                        (page, attr, raw, "根路径不在站点前缀内")
                    )
                    continue
                target = root / path_part[len(SITE_URL_PREFIX) :]
            else:
                target = page.parent / path_part
            target = target.resolve()
            if not target.is_relative_to(root):
                missing.append((page, attr, raw, "解析到站点目录之外"))
                continue
            if not (target.is_file() or (target / "index.html").is_file()):
                missing.append((page, attr, raw, "目标文件不存在"))

    for page, attr, raw, reason in missing[:20]:
        problems.append(
            f"本地引用缺失：{page.relative_to(root).as_posix()} "
            f'{attr}="{raw}"（{reason}）'
        )
    if len(missing) > 20:
        problems.append(f"…其余 {len(missing) - 20} 条本地引用缺失未逐条列出")
    return problems


def _log_artifact_problems(problems: list[str]) -> None:
    LOG.error("构建产物完整性检查失败（%d 项）：", len(problems))
    for problem in problems:
        LOG.error("  - %s", problem)


def run_build(strict: bool = True, verify_artifacts: bool = True) -> int:
    """prepare + 严格构建 + 产物完整性门禁。

    Zensical 0.1.0（beta）曾出现偶发漏写单个主题 CSS 且退出码为 0 的情况，因此
    构建成功后检查产物；若失败则重试一次干净构建，仍失败则返回非 0 阻止发布。
    """
    manifest = prepare()
    attempts = 2 if verify_artifacts else 1
    for attempt in range(1, attempts + 1):
        command = _zensical_cli() + ["build", "-f", str(CONFIG_FILE), "--clean"]
        if strict:
            command.append("--strict")
        LOG.info("执行构建（第 %d/%d 次）：%s", attempt, attempts, " ".join(command))
        code = subprocess.call(command, cwd=str(ROOT))
        if code != 0:
            return code
        if not verify_artifacts:
            return 0
        site_dir = _site_dir_from_config()
        problems = check_site_artifacts(
            site_dir, expected_pages=manifest.get("source_page_count")
        )
        if not problems:
            LOG.info(
                "构建产物完整性检查通过：%s 个站点文件，本地引用完整",
                sum(1 for path in site_dir.rglob("*") if path.is_file()),
            )
            return 0
        _log_artifact_problems(problems)
        if attempt < attempts:
            LOG.warning(
                "Zensical 0.1.0 存在偶发缺资产的已知风险，自动重试一次干净构建…"
            )
    return 1


def _git_head_signature() -> str:
    """无需启动子进程地读取当前 HEAD 提交（供 ``serve`` 监听提交变化）。

    返回 ``.git/HEAD`` 指向的分支引用内容（提交 SHA）；分离 HEAD 时返回 HEAD 本身。
    读取失败时返回空串（非 git 环境下降级，不影响 mtime 监听）。
    """
    git_dir = ROOT / ".git"
    try:
        head = (git_dir / "HEAD").read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return ""
    if head.startswith("ref: "):
        ref_path = git_dir / head[5:].strip()
        try:
            return ref_path.read_text(encoding="utf-8", errors="replace").strip()
        except OSError:
            return head
    return head


def _snapshot_sources() -> dict[str, object]:
    """记录需要监听的原始输入：文件 mtime + Git HEAD。

    单独提交（如 ``git commit -m docs``）不会改变工作区文件 mtime，但会改变 HEAD；
    日期与目录时间都来自 Git 历史，因此 HEAD 必须纳入快照才能让 ``serve`` 在提交后刷新。
    """
    snapshot: dict[str, object] = {}
    for directory in (DOCS_DIR, INCLUDES_DIR):
        if not directory.is_dir():
            continue
        for path in directory.rglob("*"):
            if path.is_file():
                snapshot[str(path)] = path.stat().st_mtime
    for extra in (TOC_TEMPLATE_PATH, ROOT / "hooks" / "toc.py", CONFIG_FILE):
        if extra.is_file():
            snapshot[str(extra)] = extra.stat().st_mtime
    snapshot["__git_head__"] = _git_head_signature()
    return snapshot


def _watch_sources(stop_event: threading.Event) -> None:
    """监听原始输入，变化后重新 prepare；由目标引擎监听暂存目录触发重建。"""
    previous = _snapshot_sources()
    while not stop_event.wait(1.0):
        current = _snapshot_sources()
        if current == previous:
            continue
        time.sleep(0.4)  # 合并编辑器连续写入
        previous = _snapshot_sources()
        try:
            LOG.info("检测到原始内容变化，重新生成暂存内容…")
            prepare(incremental=True)
        except Exception as exc:  # 预览服务不因一次预处理失败退出
            LOG.error("重新生成暂存内容失败：%s", exc)


def run_serve() -> int:
    prepare()
    command = _zensical_cli() + ["serve", "-f", str(CONFIG_FILE)]
    LOG.info("执行：%s", " ".join(command))
    stop_event = threading.Event()
    watcher = threading.Thread(
        target=_watch_sources, args=(stop_event,), name="notebook-prepare-watcher", daemon=True
    )
    watcher.start()
    process = subprocess.Popen(command, cwd=str(ROOT))
    try:
        return process.wait()
    except KeyboardInterrupt:
        LOG.info("收到中断，停止预览…")
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
        return 0
    finally:
        stop_event.set()
        watcher.join(timeout=2)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="notebook_build.py",
        description="Vigilux 笔记本的 Zensical 构建入口（prepare / build / serve）。",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("prepare", help="生成 .migration/docs 暂存内容")
    build_parser = subparsers.add_parser(
        "build", help="prepare 后执行 zensical build，并做产物完整性门禁"
    )
    build_parser.add_argument(
        "--no-strict", action="store_true", help="关闭 zensical --strict（默认开启）"
    )
    build_parser.add_argument(
        "--skip-artifact-check",
        action="store_true",
        help="跳过构建后产物完整性检查（仅用于排查问题，不建议在 CI 使用）",
    )
    subparsers.add_parser("serve", help="prepare 后启动 zensical serve 并监听源文件")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)-7s %(message)s"
    )

    if args.command == "prepare":
        prepare()
        return 0
    if args.command == "build":
        return run_build(
            strict=not args.no_strict,
            verify_artifacts=not args.skip_artifact_check,
        )
    if args.command == "serve":
        return run_serve()
    parser.error(f"未知命令：{args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""独立静态验收工具：Material 基线 vs Zensical 迁移构建。

用途
----
在 D:\\MkDocs 项目中，把 .migration/baseline-material（Material 9.7.7 基线，
作为对照 oracle）与 site-zensical（Zensical 0.1.0 迁移构建）逐页、逐项对照，
按《Zensical 迁移调研与执行报告》第 10 节 A01–A18 门槛中的静态可验证部分给出
通过/失败结论。

覆盖范围（静态）
----------------
- A02 页面集合 / 路由 / canonical / sitemap；无 .migration 暂存目录 URL 泄漏
- A03 页面标题、H1–H6 的 id/文本、代码块文本、表格文本、公式源文本
- A04 链接与图片解析：本地引用必须落在 /notebook/ 前缀内且目标存在；无新增缺失目标；
      友链头像必须解析到 /notebook/images/lemoon1206.jpg
- A05 分区目录：8 组 / 27 条，标题/链接/统计/阅读时长/data-ts/排序逐字一致
- A06 首页统计 65 / 63119 / 2056；无 {{pages}}/{{words}}/{{codes}} 泄漏
- A07 20 页页面统计文本与位置（首个 h1 之后）
- A08 64 页 Git 日期文本与 title 属性逐字一致（index.md 不出现）
- A09 公式源包装块数量（静态结构，运行时渲染由 verify_runtime.py 负责）
- A10 Mermaid 源块数量（静态结构，运行时渲染由 verify_runtime.py 负责）
- A14 Giscus loader 页数与属性
- A15 灯箱锚点（静态结构；行为由运行时探针负责）

不在本工具范围（由运行时探针 / Lead / reviewer 覆盖）：
A01 源文件字节、A11 首页动效、A12 导航交互、A13 搜索、A16 响应式视觉、
A17 干净构建、A18 真实 Pages 部署。

用法
----
    python tools/verify_migration.py
    python tools/verify_migration.py --baseline DIR --target DIR
    python tools/verify_migration.py --quiet --json-only     # 仅写文件

输出
----
- .migration/verify/static-report.json  （机器可读，含全部检查项与明细）
- .migration/verify/static-report.md    （人类可读摘要）
退出码：0 = 全部检查通过；1 = 存在失败项；2 = 运行环境/输入错误。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urldefrag, urljoin, urlparse

try:
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover
    print("ERROR: 需要 beautifulsoup4（请使用 work/venv-research 的 python）", file=sys.stderr)
    sys.exit(2)

import warnings

try:  # sitemap.xml 用 html.parser 解析会产生无害告警，这里静音
    from bs4 import XMLParsedAsHTMLWarning

    warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
except ImportError:  # pragma: no cover
    pass

SITE_PREFIX = "/notebook/"
SYNTHETIC_ORIGIN = "https://verify.local"
# 生产站点主机：绝对 URL 指向该主机且路径在前缀内时，进一步校验本地目标存在性。
PRODUCTION_HOST = "vigilux418.github.io"
# 其余外部主机（含 vigilux.top 等作者自有站点）一律视为合法外链。
SITE_HOSTS = {PRODUCTION_HOST}
STAT_KEYS = ("页面总数", "总字数", "代码块行数")
PLACEHOLDERS = ("{{pages}}", "{{words}}", "{{codes}}")
AVATAR_PATH = "/notebook/images/lemoon1206.jpg"
EXTERNAL_PREFIXES = ("http://", "https://", "//")
SKIP_SCHEMES = ("#", "javascript:", "mailto:", "tel:", "data:", "blob:", "about:")
REF_ATTRS = ("href", "src", "srcset", "data-src", "poster")
DATE_YEAR_RE = re.compile(r"\d{4}年")


# --------------------------------------------------------------------------------------
# 基础设施
# --------------------------------------------------------------------------------------
def norm(text: str | None) -> str:
    """HTML 文本归一化：折叠空白（含 nbsp）并去首尾。"""
    if text is None:
        return ""
    return re.sub(r"\s+", " ", text.replace("\u00a0", " ")).strip()


def read_soup(path: Path) -> BeautifulSoup:
    return BeautifulSoup(path.read_bytes(), "html.parser")


def route_of(rel: str) -> str:
    """相对输出路径 -> 站点路由。

    index.html -> ''；a/index.html -> 'a/'；404.html -> '404.html'。
    """
    if rel == "index.html":
        return ""
    if rel.endswith("/index.html"):
        return rel[: -len("index.html")]
    return rel


def page_url(rel: str) -> str:
    return SYNTHETIC_ORIGIN + SITE_PREFIX + route_of(rel)


def page_route_set(root: Path) -> dict[str, str]:
    out = {}
    for p in sorted(root.rglob("*.html")):
        rel = p.relative_to(root).as_posix()
        out[rel] = route_of(rel)
    return out


def content_root(soup: BeautifulSoup) -> BeautifulSoup:
    """提取页面主体内容树（含文章正文；去除左侧/右侧导航侧栏，保留正文孪生节点）。

    基线 Material 9.7.7 与目标 Zensical 0.1.0 classic 共享同一套 overrides 与
    Markdown 渲染链，正文主体结构一致；因此除侧栏导航外的 main 内容可以逐项比较。
    """
    main = (
        soup.select_one(".md-main")
        or soup.select_one("main.md-main")
        or soup.select_one("main")
        or soup.body
        or soup
    )
    frag = BeautifulSoup(str(main), "html.parser")
    for sel in (".md-sidebar", "nav.md-nav--primary", "nav.md-nav--secondary"):
        for el in frag.select(sel):
            el.decompose()
    return frag


def find_page_stat(root: BeautifulSoup) -> dict:
    """定位页面统计块：“约 N 个字 … 预计阅读时间 …”所在的最内层 p/div。

    返回 text（归一化文本）、stat_index（在正文元素序列中的下标）、h1_index（首个 h1
    的下标，无 h1 时为 -1）。两下标取自同一元素序列，可直接比较先后。
    """
    elements = root.find_all(True)
    candidates = []
    for idx, el in enumerate(elements):
        if el.name not in ("p", "div"):
            continue
        text = norm(el.get_text(" ", strip=True))
        if "个字" in text and "预计阅读时间" in text:
            candidates.append((len(text), idx, text, el))
    if not candidates:
        return {"text": None, "stat_index": -1, "h1_index": -1}
    candidates.sort(key=lambda c: (c[0], c[1]))
    text, stat_index = candidates[0][2], candidates[0][1]
    h1_index = -1
    for idx, el in enumerate(elements):
        if el.name == "h1":
            h1_index = idx
            break
    return {"text": text, "stat_index": stat_index, "h1_index": h1_index}


def heading_list(root: BeautifulSoup) -> list[dict]:
    out = []
    for el in root.select("h1, h2, h3, h4, h5, h6"):
        out.append({"tag": el.name, "id": el.get("id"), "text": norm(el.get_text(" ", strip=True))})
    return out


def pre_texts(root: BeautifulSoup) -> list[str]:
    return [pre.get_text() for pre in root.select("pre")]


def table_texts(root: BeautifulSoup) -> list[str]:
    return [norm(t.get_text(" ", strip=True)) for t in root.select("table")]


def math_sources(root: BeautifulSoup) -> list[str]:
    return [el.get_text() for el in root.select(".arithmatex")]


def extract_toc(root: BeautifulSoup) -> dict:
    groups = []
    for group in root.select(".index-item-wrapper"):
        btn = group.select_one(".toc-fold-btn")
        title = norm(btn.get_text(" ", strip=True)) if btn else None
        wrapper = group.select_one(".content-item-wrapper")
        items = []
        if wrapper is not None:
            for li in wrapper.find_all("li", recursive=False):
                anchor = li.select_one(".item-primary a")
                main_el = li.select_one(".item-main-content")
                status_el = li.select_one(".item-status")
                meta_el = li.select_one(".item-metadata")
                actions = li.select_one(".item-actions")
                note_tags = []
                if meta_el is not None:
                    note_tags = [norm(t.get_text(" ", strip=True)) for t in meta_el.select(".note-tag")]
                items.append(
                    {
                        "href": anchor.get("href") if anchor is not None else None,
                        "title": norm(anchor.get_text(" ", strip=True)) if anchor is not None else None,
                        "target": anchor.get("target") if anchor is not None else None,
                        "main": norm(main_el.get_text(" ", strip=True)) if main_el is not None else None,
                        "status": norm(status_el.get_text(" ", strip=True)) if status_el is not None else None,
                        "note_tags": note_tags,
                        "data_ts": actions.get("data-ts") if actions is not None else None,
                    }
                )
        groups.append({"title": title, "items": items})
    return {
        "groups": groups,
        "group_count": len(groups),
        "item_count": sum(len(g["items"]) for g in groups),
        "fold_buttons": len(root.select(".toc-fold-btn")),
    }


def extract_source_file(root: BeautifulSoup) -> list[dict]:
    sf = root.select_one(".md-source-file")
    if sf is None:
        return []
    facts = sf.select(".md-source-file__fact")
    if not facts:
        facts = [c for c in sf.find_all(recursive=False) if getattr(c, "name", None)]
    out = []
    for fact in facts:
        icon = fact.select_one(".md-icon")
        date_span = fact.select_one("[class*=git-revision-date]")
        if date_span is None:
            for cand in fact.select("[title]"):
                if DATE_YEAR_RE.search(cand.get("title") or ""):
                    date_span = cand
                    break
        out.append(
            {
                "icon_title": icon.get("title") if icon is not None else None,
                "text": norm(fact.get_text(" ", strip=True)),
                "date_text": norm(date_span.get_text(" ", strip=True)) if date_span is not None else None,
                "date_title": date_span.get("title") if date_span is not None else None,
            }
        )
    return out


def extract_giscus(soup: BeautifulSoup) -> list[dict]:
    attrs = (
        "src",
        "data-repo",
        "data-repo-id",
        "data-category",
        "data-category-id",
        "data-mapping",
        "data-lang",
    )
    out = []
    for script in soup.select("script[src*='giscus']"):
        out.append({k: script.get(k) for k in attrs})
    return out


def extract_canonical(soup: BeautifulSoup) -> str | None:
    link = soup.select_one("link[rel=canonical]")
    return link.get("href") if link is not None else None


def extract_home_statistics(soup: BeautifulSoup) -> dict:
    box = soup.select_one("#statistics")
    result = {"present": box is not None, "pairs": [], "text": None, "runtime_clock_id": None}
    if box is None:
        return result
    result["text"] = norm(box.get_text(" ", strip=True))
    for line in box.select(".stat-line"):
        key_el = line.select_one(".stat-k")
        val_el = line.select_one(".stat-v")
        if key_el is not None and val_el is not None:
            result["pairs"].append(
                {"key": norm(key_el.get_text()), "value": norm(val_el.get_text()), "id": val_el.get("id")}
            )
    clock = box.select_one("#web-time")
    result["runtime_clock_id"] = clock is not None
    return result


def refs_from_page(soup: BeautifulSoup) -> list[dict]:
    """收集页面中参与静态解析的 href/src 引用。"""
    out = []
    for el in soup.find_all(True):
        if el.name in ("base",):
            continue
        for attr in REF_ATTRS:
            value = el.get(attr)
            if not value:
                continue
            if attr == "srcset":
                for part in value.split(","):
                    part = part.strip()
                    if part:
                        out.append({"attr": attr, "raw": part.split(" ")[0], "tag": el.name})
                continue
            out.append({"attr": attr, "raw": value, "tag": el.name, "el_class": el.get("class")})
    return out


def classify_ref(raw: str, page_rel: str, target_root: Path) -> dict:
    """解析单个引用，返回分类与解析结果。

    分类口径（与验收门槛 A04 一致）：
    - 带 scheme 的绝对 URL（http/https/mailto/data/tel/协议相对 //）一律视为外部引用；
      其中指向生产站主机（vigilux418.github.io）的绝对 URL 额外记录路径是否在 /notebook/
      前缀内，仅作信息记录，不判失败（绝对 URL 是合法外链）。
    - 只有本地相对路径与以 / 开头的根路径才做 /notebook/ 前缀解析与文件存在性校验。

    category: skip / external / outside-prefix / local
    """
    raw = raw.strip()
    if not raw or raw.startswith(SKIP_SCHEMES):
        return {"category": "skip"}
    base = page_url(page_rel)
    if raw.startswith(("//",)):
        return {"category": "external", "raw": raw}
    if raw.startswith(("http://", "https://")):
        parsed = urlparse(raw)
        info = {"category": "external", "raw": raw}
        if (parsed.hostname or "").lower() == PRODUCTION_HOST:
            path = unquote(parsed.path)
            info["production_path"] = path
            info["production_prefix_ok"] = path == SITE_PREFIX.rstrip("/") or path.startswith(SITE_PREFIX)
        return info
    joined = urljoin(base, raw)
    parsed = urlparse(joined)
    path = unquote(parsed.path)
    if parsed.scheme not in ("http", "https"):
        return {"category": "skip", "raw": raw}
    if (parsed.hostname or "").lower() != urlparse(SYNTHETIC_ORIGIN).hostname:
        return {"category": "external", "raw": raw}
    if not path.startswith(SITE_PREFIX):
        return {"category": "outside-prefix", "raw": raw, "resolved": parsed.path}
    dest, exists = _path_to_dest(path, target_root)
    return {"category": "local", "raw": raw, "resolved": path, "dest": dest, "exists": exists}
    joined = urljoin(base, raw)
    parsed = urlparse(joined)
    path = unquote(parsed.path)
    if parsed.scheme not in ("http", "https"):
        return {"category": "skip", "raw": raw}
    if (parsed.hostname or "").lower() != urlparse(SYNTHETIC_ORIGIN).hostname:
        return {"category": "external", "raw": raw}
    if not path.startswith(SITE_PREFIX):
        return {"category": "outside-prefix", "raw": raw, "resolved": parsed.path}
    dest, exists = _path_to_dest(path, target_root)
    return {"category": "local", "raw": raw, "resolved": path, "dest": dest, "exists": exists}


def _dest_exists(path: str, root: Path) -> bool:
    return _path_to_dest(path, root)[1]


def _path_to_dest(path: str, root: Path) -> tuple[str, bool]:
    rel = path[len(SITE_PREFIX):]
    candidate = root / rel
    if candidate.is_file():
        return candidate.relative_to(root).as_posix(), True
    if candidate.is_dir() and (candidate / "index.html").is_file():
        return (candidate / "index.html").relative_to(root).as_posix(), True
    return rel, False


# --------------------------------------------------------------------------------------
# 报告容器
# --------------------------------------------------------------------------------------
class Report:
    def __init__(self) -> None:
        self.checks: list[dict] = []
        self._seq = 0

    def add(self, gate: str, subject: str, status: str, message: str, details=None) -> None:
        assert status in ("pass", "fail", "warn", "info", "skip")
        self._seq += 1
        item = {
            "seq": self._seq,
            "gate": gate,
            "subject": subject,
            "status": status,
            "message": message,
            "details": details if details is not None else [],
        }
        self.checks.append(item)
        if status not in ("pass", "info"):
            flag = "FAIL" if status == "fail" else status.upper()
            print(f"[{flag}] {gate} {subject}: {message}", flush=True)

    def gate_counts(self) -> dict:
        counts: dict[str, dict[str, int]] = {}
        for c in self.checks:
            counts.setdefault(c["gate"], {}).setdefault(c["status"], 0)
            counts[c["gate"]][c["status"]] += 1
        return counts

    def failures(self) -> list[dict]:
        return [c for c in self.checks if c["status"] == "fail"]

    def warnings(self) -> list[dict]:
        return [c for c in self.checks if c["status"] == "warn"]


# --------------------------------------------------------------------------------------
# 各验收门槛检查
# --------------------------------------------------------------------------------------
def check_routes(rep: Report, baseline: dict[str, str], target: dict[str, str]) -> None:
    bset, tset = set(baseline), set(target)
    missing = sorted(bset - tset)
    extra = sorted(tset - bset)
    rep.add(
        "A02",
        "页面路由集合",
        "pass" if not missing and not extra else "fail",
        f"基线 {len(bset)} 个 HTML 输出（含 404），目标 {len(tset)} 个；缺失 {len(missing)}，多余 {len(extra)}",
        {"missing": missing, "extra": extra},
    )


def check_staging_leak(rep: Report, target_root: Path, target_pages: dict[str, str]) -> None:
    hits = []
    needles = (".migration",)
    # 1) 构建输出目录内不得出现 .migration 路径
    for p in sorted(target_root.rglob("*")):
        rel = p.relative_to(target_root).as_posix()
        if any(n in rel for n in needles):
            hits.append({"file": rel, "where": "path"})
    # 2) HTML / sitemap / search 索引中不得出现暂存目录 URL
    extra_files = [target_root / "sitemap.xml", target_root / "search.json"]
    for rel in target_pages:
        extra_files.append(target_root / rel)
    for p in extra_files:
        if not p.is_file():
            continue
        raw = p.read_text(encoding="utf-8", errors="replace")
        for needle in needles:
            if needle in raw:
                idx = raw.find(needle)
                hits.append(
                    {
                        "file": p.relative_to(target_root).as_posix(),
                        "where": "content",
                        "snippet": raw[max(0, idx - 80): idx + 80].replace("\n", " "),
                    }
                )
                break
    rep.add(
        "A02",
        "暂存目录 URL 泄漏",
        "pass" if not hits else "fail",
        "构建输出中未发现 .migration 暂存目录路径/URL" if not hits else f"发现 {len(hits)} 处 .migration 泄漏",
        hits[:20],
    )


def check_canonical(rep: Report, base_root: Path, target_root: Path, pages: dict[str, str]) -> None:
    diffs = []
    for rel in pages:
        bp, tp = base_root / rel, target_root / rel
        if not (bp.is_file() and tp.is_file()):
            continue
        b = extract_canonical(read_soup(bp))
        t = extract_canonical(read_soup(tp))
        if b != t:
            diffs.append({"page": rel, "baseline": b, "target": t})
    rep.add(
        "A02",
        "canonical",
        "pass" if not diffs else "fail",
        f"{len(pages) - len(diffs)}/{len(pages)} 页 canonical 与基线一致"
        if not diffs
        else f"{len(diffs)} 页 canonical 与基线不一致",
        diffs[:20],
    )


def check_sitemap(rep: Report, base_root: Path, target_root: Path) -> None:
    bpath, tpath = base_root / "sitemap.xml", target_root / "sitemap.xml"
    if not bpath.is_file() or not tpath.is_file():
        rep.add("A02", "sitemap", "warn", "基线或目标缺少 sitemap.xml，跳过比较")
        return
    b = read_soup(bpath)
    t = read_soup(tpath)
    bset = {normalize_sitemap(u) for u in (loc.get_text() for loc in b.select("loc"))}
    tset = {normalize_sitemap(u) for u in (loc.get_text() for loc in t.select("loc"))}
    missing, extra = sorted(bset - tset), sorted(tset - bset)
    rep.add(
        "A02",
        "sitemap URL 集合",
        "pass" if not missing and not extra else "fail",
        f"基线 {len(bset)} 条，目标 {len(tset)} 条；缺失 {len(missing)}，多余 {len(extra)}",
        {"missing": missing[:20], "extra": extra[:20]},
    )


def normalize_sitemap(url: str) -> str:
    path = urlparse(url.strip()).path
    return unquote(path)


def compare_page_contents(rep: Report, base_root: Path, target_root: Path, pages: dict[str, str]) -> None:
    title_diffs, heading_diffs, code_diffs, table_diffs, math_diffs = [], [], [], [], []
    heading_missing_ids = []
    page_total = 0
    for rel in pages:
        bp, tp = base_root / rel, target_root / rel
        if not (bp.is_file() and tp.is_file()):
            continue
        page_total += 1
        bs, ts = read_soup(bp), read_soup(tp)
        bt = norm(bs.title.get_text()) if bs.title is not None else None
        tt = norm(ts.title.get_text()) if ts.title is not None else None
        if bt != tt:
            title_diffs.append({"page": rel, "baseline": bt, "target": tt})
        bc, tc = content_root(bs), content_root(ts)
        bh, th = heading_list(bc), heading_list(tc)
        if bh != th:
            bid = {h["id"] for h in bh}
            tid = {h["id"] for h in th}
            missing = sorted(x for x in bid - tid if x)
            extra = sorted(x for x in tid - bid if x)
            if missing:
                heading_missing_ids.append({"page": rel, "missing_ids": missing[:10]})
            heading_diffs.append(
                {
                    "page": rel,
                    "baseline_count": len(bh),
                    "target_count": len(th),
                    "missing_ids": missing[:10],
                    "extra_ids": extra[:10],
                    "first_diff": _first_seq_diff(bh, th),
                }
            )
        bpre, tpre = pre_texts(bc), pre_texts(tc)
        if bpre != tpre:
            code_diffs.append({"page": rel, "counts": [len(bpre), len(tpre)], "detail": _first_seq_diff(bpre, tpre)})
        btab, ttab = table_texts(bc), table_texts(tc)
        if btab != ttab:
            table_diffs.append({"page": rel, "counts": [len(btab), len(ttab)], "detail": _first_seq_diff(btab, ttab)})
        bmath, tmath = math_sources(bc), math_sources(tc)
        if bmath != tmath:
            math_diffs.append({"page": rel, "counts": [len(bmath), len(tmath)], "detail": _first_seq_diff(bmath, tmath)})

    rep.add(
        "A03",
        "页面标题",
        "pass" if not title_diffs else "fail",
        f"{page_total - len(title_diffs)}/{page_total} 页 <title> 一致" if not title_diffs else f"{len(title_diffs)} 页标题不一致",
        title_diffs[:20],
    )
    rep.add(
        "A03",
        "H1–H6 id/文本/顺序",
        "pass" if not heading_diffs else "fail",
        f"{page_total - len(heading_diffs)}/{page_total} 页标题层级完全一致"
        if not heading_diffs
        else f"{len(heading_diffs)} 页标题层级有差异；缺失锚点 id 的页面 {len(heading_missing_ids)} 个",
        {"diff_pages": heading_diffs[:20], "missing_ids": heading_missing_ids[:20]},
    )
    rep.add(
        "A03",
        "代码块文本",
        "pass" if not code_diffs else "fail",
        f"{page_total - len(code_diffs)}/{page_total} 页代码块文本一致" if not code_diffs else f"{len(code_diffs)} 页代码块文本不一致",
        code_diffs[:20],
    )
    rep.add(
        "A03",
        "表格文本",
        "pass" if not table_diffs else "fail",
        f"{page_total - len(table_diffs)}/{page_total} 页表格文本一致" if not table_diffs else f"{len(table_diffs)} 页表格文本不一致",
        table_diffs[:20],
    )
    rep.add(
        "A03",
        "公式源文本",
        "pass" if not math_diffs else "fail",
        f"{page_total - len(math_diffs)}/{page_total} 页公式源文本一致" if not math_diffs else f"{len(math_diffs)} 页公式源文本不一致",
        math_diffs[:20],
    )


def _first_seq_diff(a, b) -> dict | None:
    for i in range(min(len(a), len(b))):
        if a[i] != b[i]:
            return {
                "index": i,
                "baseline": _truncate(a[i]),
                "target": _truncate(b[i]),
            }
    if len(a) != len(b):
        return {"index": min(len(a), len(b)), "baseline": _truncate(a[min(len(a), len(b))] if a else None), "target": _truncate(b[min(len(a), len(b))] if b else None)}
    return None


def _truncate(value, limit: int = 240):
    if isinstance(value, str):
        return value[:limit]
    return value


def check_toc(rep: Report, base_root: Path, target_root: Path, pages: dict[str, str]) -> None:
    base_toc_pages, target_toc_pages = {}, {}
    total_groups = total_items = 0
    for rel in pages:
        bs, ts = read_soup(base_root / rel), read_soup(target_root / rel)
        b = extract_toc(content_root(bs))
        t = extract_toc(content_root(ts))
        if b["group_count"]:
            base_toc_pages[rel] = b
            total_groups += b["group_count"]
            total_items += b["item_count"]
        if t["group_count"]:
            target_toc_pages[rel] = t
    missing_pages = sorted(set(base_toc_pages) - set(target_toc_pages))
    extra_pages = sorted(set(target_toc_pages) - set(base_toc_pages))
    diffs = []
    for rel in sorted(set(base_toc_pages) & set(target_toc_pages)):
        if base_toc_pages[rel] != target_toc_pages[rel]:
            diffs.append(
                {
                    "page": rel,
                    "baseline": _toc_summary(base_toc_pages[rel]),
                    "target": _toc_summary(target_toc_pages[rel]),
                    "first_diff": _first_seq_diff(
                        [json.dumps(g, ensure_ascii=False, sort_keys=True) for g in base_toc_pages[rel]["groups"]],
                        [json.dumps(g, ensure_ascii=False, sort_keys=True) for g in target_toc_pages[rel]["groups"]],
                    ),
                }
            )
    target_groups = sum(t["group_count"] for t in target_toc_pages.values())
    target_items = sum(t["item_count"] for t in target_toc_pages.values())
    ok = not missing_pages and not extra_pages and not diffs and target_groups == total_groups and target_items == total_items
    rep.add(
        "A05",
        "分区目录结构/内容/排序",
        "pass" if ok else "fail",
        f"{len(base_toc_pages)} 页 {total_groups} 组 {total_items} 条逐字一致"
        if ok
        else f"目录不一致：缺失页 {len(missing_pages)}，多余页 {len(extra_pages)}，内容差异 {len(diffs)} 页；"
        f"基线 {total_groups} 组/{total_items} 条，目标 {target_groups} 组/{target_items} 条",
        {
            "missing_pages": missing_pages,
            "extra_pages": extra_pages,
            "diffs": diffs[:10],
        },
    )
    # 额外明细：各组条目数
    detail = {
        rel: {"group_count": t["group_count"], "item_count": t["item_count"]}
        for rel, t in sorted(target_toc_pages.items())
    }
    rep.add("A05", "分区目录计数明细", "info", "各组条目数（目标构建）", detail)


def _toc_summary(toc: dict) -> dict:
    return {
        "group_count": toc["group_count"],
        "item_count": toc["item_count"],
        "fold_buttons": toc["fold_buttons"],
        "groups": [
            {"title": g["title"], "items": [(i["href"], i["title"], i["main"], i["data_ts"]) for i in g["items"]]}
            for g in toc["groups"]
        ],
    }


def check_home_statistics(rep: Report, base_root: Path, target_root: Path) -> None:
    rel = "index.html"
    b = extract_home_statistics(read_soup(base_root / rel))
    t = extract_home_statistics(read_soup(target_root / rel))
    expected = {
        "页面总数": "65",
        "总字数": "63119",
        "代码块行数": "2056",
    }
    base_pairs = {p["key"]: p["value"] for p in b["pairs"]}
    target_pairs = {p["key"]: p["value"] for p in t["pairs"]}
    matches_expected = all(target_pairs.get(k) == v for k, v in expected.items())
    same_as_baseline = all(base_pairs.get(k) == target_pairs.get(k) for k in STAT_KEYS)
    ok = t["present"] and matches_expected and same_as_baseline and t["runtime_clock_id"]
    rep.add(
        "A06",
        "首页统计数值",
        "pass" if ok else "fail",
        "首页统计 = 65 / 63119 / 2056，与基线一致且保留 #web-time"
        if ok
        else f"首页统计不符：目标 {target_pairs}，基线 {base_pairs}，期望 {expected}，web-time={t['runtime_clock_id']}",
        {"baseline": base_pairs, "target": target_pairs, "expected": expected},
    )


def check_placeholders(rep: Report, target_root: Path, pages: dict[str, str]) -> None:
    hits = []
    scan_files = [target_root / "sitemap.xml", target_root / "search.json"]
    scan_files += [target_root / rel for rel in pages]
    for p in scan_files:
        if not p.is_file():
            continue
        raw = p.read_text(encoding="utf-8", errors="replace")
        for needle in PLACEHOLDERS:
            if needle in raw:
                idx = raw.find(needle)
                hits.append(
                    {
                        "file": p.relative_to(target_root).as_posix(),
                        "placeholder": needle,
                        "snippet": raw[max(0, idx - 60): idx + 60].replace("\n", " "),
                    }
                )
    rep.add(
        "A06",
        "统计占位符泄漏",
        "pass" if not hits else "fail",
        "未发现 {{pages}}/{{words}}/{{codes}} 占位符泄漏" if not hits else f"发现 {len(hits)} 处统计占位符泄漏",
        hits[:20],
    )


def check_page_statistics(rep: Report, base_root: Path, target_root: Path, pages: dict[str, str]) -> None:
    base_pages, target_pages = {}, {}
    for rel in pages:
        if rel == "index.html":
            continue
        bs, ts = read_soup(base_root / rel), read_soup(target_root / rel)
        bstat = find_page_stat(content_root(bs))
        if bstat["text"]:
            base_pages[rel] = bstat["text"]
        tstat = find_page_stat(content_root(ts))
        if tstat["text"]:
            target_pages[rel] = {
                "text": tstat["text"],
                "after_h1": tstat["stat_index"] > tstat["h1_index"] if tstat["h1_index"] >= 0 else False,
                "h1_index": tstat["h1_index"],
                "stat_index": tstat["stat_index"],
            }
    missing = sorted(set(base_pages) - set(target_pages))
    extra = sorted(set(target_pages) - set(base_pages))
    text_diffs = [
        {"page": rel, "baseline": base_pages[rel], "target": target_pages[rel]["text"]}
        for rel in sorted(set(base_pages) & set(target_pages))
        if base_pages[rel] != target_pages[rel]["text"]
    ]
    position_bad = [
        {"page": rel, "h1_index": target_pages[rel]["h1_index"], "stat_index": target_pages[rel]["stat_index"]}
        for rel in target_pages
        if not target_pages[rel]["after_h1"]
    ]
    ok = not missing and not extra and not text_diffs and not position_bad
    rep.add(
        "A07",
        "页面统计块（20 页）",
        "pass" if ok else "fail",
        f"{len(base_pages)} 页页面统计文本与位置均与基线一致"
        if ok
        else f"页面统计不符：缺失 {len(missing)} 页、多余 {len(extra)} 页、文本差异 {len(text_diffs)} 页、位置异常 {len(position_bad)} 页",
        {
            "baseline_pages": len(base_pages),
            "target_pages": len(target_pages),
            "missing": missing,
            "extra": extra,
            "text_diffs": text_diffs[:20],
            "position_bad": position_bad[:20],
        },
    )


def check_git_dates(rep: Report, base_root: Path, target_root: Path, pages: dict[str, str]) -> None:
    base_pages, target_pages = {}, {}
    for rel in pages:
        bs, ts = read_soup(base_root / rel), read_soup(target_root / rel)
        b = extract_source_file(content_root(bs))
        t = extract_source_file(content_root(ts))
        if b:
            base_pages[rel] = b
        if t:
            target_pages[rel] = t
    missing = sorted(set(base_pages) - set(target_pages))
    extra = sorted(set(target_pages) - set(base_pages))
    diffs = []
    for rel in sorted(set(base_pages) & set(target_pages)):
        b, t = base_pages[rel], target_pages[rel]
        # 严格比较日期文本 + title 属性 + fact 文本；icon_title 仅在有值时比较
        b_key = [(f["text"], f["date_text"], f["date_title"]) for f in b]
        t_key = [(f["text"], f["date_text"], f["date_title"]) for f in t]
        icon_b = [f["icon_title"] for f in b]
        icon_t = [f["icon_title"] for f in t]
        if b_key != t_key or (all(icon_t) and icon_b != icon_t):
            diffs.append(
                {
                    "page": rel,
                    "baseline": b_key,
                    "target": t_key,
                    "icon_mismatch": icon_b != icon_t,
                }
            )
    index_has_date = "index.html" in target_pages
    ok = not missing and not extra and not diffs and not index_has_date
    rep.add(
        "A08",
        "Git 创建/更新日期（64 页）",
        "pass" if ok else "fail",
        f"{len(base_pages)} 页日期文本与 title 属性逐字一致；index.html 未出现"
        if ok
        else f"Git 日期不符：缺失 {len(missing)} 页、多余 {len(extra)} 页、内容差异 {len(diffs)} 页，index.html 出现日期={index_has_date}",
        {
            "baseline_pages": len(base_pages),
            "target_pages": len(target_pages),
            "missing": missing,
            "extra": extra,
            "diffs": diffs[:20],
        },
    )


def check_resource_counts(rep: Report, base_root: Path, target_root: Path, pages: dict[str, str]) -> None:
    """A09/A10 静态结构计数：公式包装块、Mermaid 源块。

    判定口径：**按页逐页等于 Material 基线**，不以调研报告中的历史常量（331/100）为准。
    同时记录两种 selector 口径：
      - 全页正文口径：main 内（去除侧栏导航）全部 `.arithmatex` / `.mermaid`，
        包含 material 渲染异常地落在 <article> 之外的孪生内容（如 tools/mkdocs/3 的 tabs）；
      - .md-content 口径：Material 文章容器内（调研报告旧证据使用该口径，漏计 article 外内容）。
    两种口径均要求逐页与基线相等。
    """
    scope_math_b = {"page": 0, "md_content": 0}
    scope_math_t = {"page": 0, "md_content": 0}
    tag_counts_b = {"span": 0, "div": 0, "other": 0}
    tag_counts_t = {"span": 0, "div": 0, "other": 0}
    mermaid_pages_b, mermaid_pages_t = {}, {}
    mermaid_md_pages_b, mermaid_md_pages_t = {}, {}
    math_page_b = math_page_t = 0
    math_diffs, mermaid_diffs = [], []
    for rel in pages:
        bs, ts = read_soup(base_root / rel), read_soup(target_root / rel)
        bc, tc = content_root(bs), content_root(ts)
        b_math_all = bc.select(".arithmatex")
        t_math_all = tc.select(".arithmatex")
        b_math_md = len(bs.select(".md-content .arithmatex"))
        t_math_md = len(ts.select(".md-content .arithmatex"))
        scope_math_b["page"] += len(b_math_all)
        scope_math_t["page"] += len(t_math_all)
        scope_math_b["md_content"] += b_math_md
        scope_math_t["md_content"] += t_math_md
        for el in b_math_all:
            tag_counts_b[el.name if el.name in ("span", "div") else "other"] += 1
        for el in t_math_all:
            tag_counts_t[el.name if el.name in ("span", "div") else "other"] += 1
        if len(b_math_all) != len(t_math_all) or b_math_md != t_math_md:
            math_diffs.append(
                {
                    "page": rel,
                    "baseline": {"page_content": len(b_math_all), "md_content": b_math_md},
                    "target": {"page_content": len(t_math_all), "md_content": t_math_md},
                }
            )
        if rel == "tools/lay_lang/tex/math/index.html":
            math_page_b, math_page_t = len(b_math_all), len(t_math_all)
        b_m_all = len(bc.select(".mermaid"))
        t_m_all = len(tc.select(".mermaid"))
        b_m_md = len(bs.select(".md-content .mermaid"))
        t_m_md = len(ts.select(".md-content .mermaid"))
        if b_m_all:
            mermaid_pages_b[rel] = b_m_all
        if t_m_all:
            mermaid_pages_t[rel] = t_m_all
        if b_m_md:
            mermaid_md_pages_b[rel] = b_m_md
        if t_m_md:
            mermaid_md_pages_t[rel] = t_m_md
        if b_m_all != t_m_all or b_m_md != t_m_md:
            mermaid_diffs.append(
                {
                    "page": rel,
                    "baseline": {"page_content": b_m_all, "md_content": b_m_md},
                    "target": {"page_content": t_m_all, "md_content": t_m_md},
                }
            )
    # 基线内部两口径差异页（用于解释 331/337 与 100/105）
    math_scope_gap = {
        rel: {"page_content": len(content_root(read_soup(base_root / rel)).select(".arithmatex")),
              "md_content": len(read_soup(base_root / rel).select(".md-content .arithmatex"))}
        for rel in pages
        if len(content_root(read_soup(base_root / rel)).select(".arithmatex"))
        != len(read_soup(base_root / rel).select(".md-content .arithmatex"))
    }
    mermaid_scope_gap = {
        rel: {"page_content": len(content_root(read_soup(base_root / rel)).select(".mermaid")),
              "md_content": len(read_soup(base_root / rel).select(".md-content .mermaid"))}
        for rel in pages
        if len(content_root(read_soup(base_root / rel)).select(".mermaid"))
        != len(read_soup(base_root / rel).select(".md-content .mermaid"))
    }
    math_ok = not math_diffs and scope_math_b == scope_math_t
    rep.add(
        "A09",
        "公式包装块静态结构（逐页等于基线）",
        "pass" if math_ok else "fail",
        f"逐页与基线相等：全页正文口径 {scope_math_t['page']} 个（span {tag_counts_t['span']} + div {tag_counts_t['div']} + 其他 {tag_counts_t['other']}，基线 {scope_math_b['page']}）；"
        f".md-content 口径 {scope_math_t['md_content']} 个（基线 {scope_math_b['md_content']}）；公式页 {math_page_t} 个（基线 {math_page_b}）"
        if math_ok
        else f"公式包装块逐页不等：{len(math_diffs)} 页差异；目标合计 {scope_math_t}，基线合计 {scope_math_b}",
        {
            "criterion": "per-page equal to baseline in both scopes",
            "selectors": {
                "page_content": "main 内去除 .md-sidebar 后的全部 .arithmatex",
                "md_content": ".md-content .arithmatex（旧调研口径）",
            },
            "totals": {"baseline": scope_math_b, "target": scope_math_t},
            "tag_counts": {"baseline": tag_counts_b, "target": tag_counts_t},
            "math_page": {"baseline": math_page_b, "target": math_page_t},
            "scope_gap_pages": math_scope_gap,
            "diffs": math_diffs[:20],
        },
    )
    mermaid_total_b = sum(mermaid_pages_b.values())
    mermaid_total_t = sum(mermaid_pages_t.values())
    mermaid_md_total_b = sum(mermaid_md_pages_b.values())
    mermaid_md_total_t = sum(mermaid_md_pages_t.values())
    mermaid_ok = not mermaid_diffs and mermaid_pages_b == mermaid_pages_t
    rep.add(
        "A10",
        "Mermaid 源块静态结构（逐页等于基线）",
        "pass" if mermaid_ok else "fail",
        f"逐页与基线相等：全页正文口径 {len(mermaid_pages_t)} 页 {mermaid_total_t} 块（基线 {len(mermaid_pages_b)} 页 {mermaid_total_b}）；"
        f".md-content 口径 {len(mermaid_md_pages_t)} 页 {mermaid_md_total_t} 块（基线 {len(mermaid_md_pages_b)} 页 {mermaid_md_total_b}）"
        if mermaid_ok
        else f"Mermaid 源块逐页不等：{len(mermaid_diffs)} 页差异",
        {
            "criterion": "per-page equal to baseline in both scopes",
            "selectors": {
                "page_content": "main 内去除 .md-sidebar 后的全部 .mermaid",
                "md_content": ".md-content .mermaid（旧调研口径）",
            },
            "baseline_pages": mermaid_pages_b,
            "target_pages": mermaid_pages_t,
            "baseline_total": mermaid_total_b,
            "target_total": mermaid_total_t,
            "md_content": {
                "baseline_pages": mermaid_md_pages_b,
                "target_pages": mermaid_md_pages_t,
                "baseline_total": mermaid_md_total_b,
                "target_total": mermaid_md_total_t,
            },
            "scope_gap_pages": mermaid_scope_gap,
            "diffs": mermaid_diffs[:20],
        },
    )


def check_giscus(rep: Report, base_root: Path, target_root: Path, pages: dict[str, str]) -> None:
    base_pages, target_pages = {}, {}
    for rel in pages:
        b = extract_giscus(read_soup(base_root / rel))
        t = extract_giscus(read_soup(target_root / rel))
        if b:
            base_pages[rel] = b
        if t:
            target_pages[rel] = t
    missing = sorted(set(base_pages) - set(target_pages))
    extra = sorted(set(target_pages) - set(base_pages))
    diffs = []
    for rel in sorted(set(base_pages) & set(target_pages)):
        if base_pages[rel] != target_pages[rel]:
            diffs.append({"page": rel, "baseline": base_pages[rel], "target": target_pages[rel]})
    ok = not missing and not extra and not diffs
    rep.add(
        "A14",
        "Giscus loader（20 页）",
        "pass" if ok else "fail",
        f"{len(base_pages)} 页 Giscus loader 属性与基线一致"
        if ok
        else f"Giscus 不符：缺失 {len(missing)} 页、多余 {len(extra)} 页、属性差异 {len(diffs)} 页",
        {"baseline_pages": len(base_pages), "target_pages": len(target_pages), "missing": missing, "extra": extra, "diffs": diffs[:20]},
    )


def check_lightbox(rep: Report, base_root: Path, target_root: Path, pages: dict[str, str]) -> None:
    base_pages, target_pages = {}, {}
    for rel in pages:
        bs, ts = read_soup(base_root / rel), read_soup(target_root / rel)
        b = len(content_root(bs).select("a.glightbox"))
        t = len(content_root(ts).select("a.glightbox"))
        if b:
            base_pages[rel] = b
        if t:
            target_pages[rel] = t
    missing = sorted(set(base_pages) - set(target_pages))
    extra = sorted(set(target_pages) - set(base_pages))
    diffs = [
        {"page": rel, "baseline": base_pages[rel], "target": target_pages[rel]}
        for rel in sorted(set(base_pages) & set(target_pages))
        if base_pages[rel] != target_pages[rel]
    ]
    ok = not missing and not extra and not diffs
    rep.add(
        "A15",
        "灯箱锚点结构",
        "pass" if ok else "fail",
        f"{sum(base_pages.values())} 个 .glightbox 锚点分布于 {len(base_pages)} 页，与基线一致（行为由运行时探针验证）"
        if ok
        else f"灯箱锚点不符：缺失页 {len(missing)}、多余页 {len(extra)}、数量差异 {len(diffs)} 页",
        {"baseline": base_pages, "target": target_pages, "missing_pages": missing, "extra_pages": extra, "diffs": diffs[:20]},
    )


def check_links(rep: Report, base_root: Path, target_root: Path, pages: dict[str, str]) -> None:
    """A04：解析所有本地引用；本地目标必须落在前缀内且存在；无新增缺失目标；头像路径正确。

    绝对 URL（含 http/https/协议相对/mailto 等）一律按合法外链处理，不做前缀解析；
    只有本地相对路径与 / 开头的根路径参与 /notebook/ 前缀与存在性校验。
    """
    outside = []
    target_missing = {}
    baseline_missing = {}
    stats = {"refs": 0, "local": 0, "external": 0, "skip": 0, "outside_prefix": 0, "missing": 0}
    production_abs = []
    avatar_issues = []
    for rel in pages:
        bs, ts = read_soup(base_root / rel), read_soup(target_root / rel)
        for kind, soup, bucket in (("baseline", bs, baseline_missing), ("target", ts, target_missing)):
            broken = []
            for ref in refs_from_page(soup):
                info = classify_ref(ref["raw"], rel, target_root if kind == "target" else base_root)
                if kind == "target":
                    stats["refs"] += 1
                    if info["category"] == "local":
                        stats["local"] += 1
                    elif info["category"] == "external":
                        stats["external"] += 1
                        if info.get("production_path") is not None:
                            production_abs.append(
                                {
                                    "page": rel,
                                    "raw": ref["raw"],
                                    "path": info["production_path"],
                                    "prefix_ok": info["production_prefix_ok"],
                                }
                            )
                    elif info["category"] == "skip":
                        stats["skip"] += 1
                if info["category"] == "local" and not info.get("exists"):
                    broken.append(
                        {
                            "page": rel,
                            "tag": ref["tag"],
                            "attr": ref["attr"],
                            "raw": ref["raw"],
                            "resolved": info.get("resolved"),
                        }
                    )
                if kind == "target" and info["category"] == "outside-prefix":
                    outside.append(
                        {
                            "page": rel,
                            "tag": ref["tag"],
                            "attr": ref["attr"],
                            "raw": ref["raw"],
                            "resolved": info.get("resolved"),
                        }
                    )
            if broken:
                bucket[rel] = broken
        stats.setdefault("refs", 0)
        # 友链头像专项
        if rel == "links/index.html":
            avatar_issues = _check_avatar(target_root / rel)
    base_missing_set = {(k, v["raw"]) for k, items in baseline_missing.items() for v in items}
    new_missing = [
        item
        for rel, items in target_missing.items()
        for item in items
        if (rel, item["raw"]) not in base_missing_set
    ]
    stats["outside_prefix"] = len(outside)
    stats["missing"] = len(new_missing)
    ok = not outside and not new_missing and not avatar_issues
    rep.add(
        "A04",
        "本地引用前缀与缺失目标",
        "pass" if ok else "fail",
        f"扫描 {stats['refs']} 个引用：本地 {stats['local']}，合法外链 {stats['external']}，"
        f"越出 /notebook/ 前缀 {stats['outside_prefix']}，新增缺失目标 {len(new_missing)}"
        if ok
        else f"引用问题：越出前缀 {len(outside)} 处、新增缺失目标 {len(new_missing)} 处、头像问题 {len(avatar_issues)} 处",
        {
            "stats": stats,
            "outside_prefix": outside[:20],
            "new_missing": new_missing[:20],
            "avatar_issues": avatar_issues,
            "baseline_missing_count": sum(len(v) for v in baseline_missing.values()),
        },
    )
    bad_prod = [p for p in production_abs if not p["prefix_ok"]]
    rep.add(
        "A04",
        "生产站绝对 URL 前缀（信息）",
        "info",
        f"绝对 URL 指向生产站 {len(production_abs)} 处，路径不在 /notebook/ 前缀内 {len(bad_prod)} 处（绝对外链不判失败）",
        {"count": len(production_abs), "outside_prefix": bad_prod[:20]},
    )


def _check_avatar(page_path: Path) -> list[dict]:
    issues = []
    soup = read_soup(page_path)
    imgs = soup.select("img.ava")
    if not imgs:
        issues.append({"issue": "missing-avatar-img", "detail": "links 页未找到 img.ava"})
        return issues
    for img in imgs:
        raw = img.get("src") or ""
        joined = urljoin(page_url("links/index.html"), raw)
        path = unquote(urlparse(joined).path)
        if path != AVATAR_PATH:
            issues.append({"issue": "avatar-path", "raw": raw, "resolved": path, "expected": AVATAR_PATH})
        link = img.find_parent("a")
        if link is not None:
            hraw = link.get("href") or ""
            hpath = unquote(urlparse(urljoin(page_url("links/index.html"), hraw)).path)
            if hpath != AVATAR_PATH:
                issues.append({"issue": "avatar-lightbox-href", "raw": hraw, "resolved": hpath, "expected": AVATAR_PATH})
    return issues


# --------------------------------------------------------------------------------------
# 汇总与输出
# --------------------------------------------------------------------------------------
GATE_TITLES = {
    "A02": "页面集合、路由与 URL 前缀",
    "A03": "内容与锚点",
    "A04": "链接与图片",
    "A05": "分区目录",
    "A06": "全站统计",
    "A07": "页面统计",
    "A08": "Git 日期",
    "A09": "MathJax 静态结构",
    "A10": "Mermaid 静态结构",
    "A14": "评论 loader",
    "A15": "灯箱结构",
}


def dir_fingerprint(root: Path) -> dict:
    """构建目录指纹：用于证明验收读到的目标产物在运行期间稳定（未被并发重建）。"""
    files = [p for p in root.rglob("*") if p.is_file()]
    mtimes = [p.stat().st_mtime for p in files]
    return {
        "file_count": len(files),
        "total_bytes": sum(p.stat().st_size for p in files),
        "max_mtime": datetime.fromtimestamp(max(mtimes)).isoformat(timespec="seconds") if mtimes else None,
    }


def write_outputs(
    base_root: Path,
    target_root: Path,
    out_dir: Path,
    rep: Report,
    elapsed: float,
    fingerprint_before: dict,
    fingerprint_after: dict,
) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    failures = rep.failures()
    warnings = rep.warnings()
    gates = rep.gate_counts()
    summary = {
        "tool": "verify_migration.py",
        "version": 1,
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "cwd": str(Path.cwd()),
        "baseline": str(base_root),
        "target": str(target_root),
        "target_fingerprint_before": fingerprint_before,
        "target_fingerprint_after": fingerprint_after,
        "elapsed_seconds": round(elapsed, 2),
        "site_prefix": SITE_PREFIX,
        "result": "FAIL" if failures else "PASS",
        "gate_counts": gates,
        "counts": {
            "checks": len(rep.checks),
            "pass": sum(1 for c in rep.checks if c["status"] == "pass"),
            "fail": len(failures),
            "warn": len(warnings),
            "info": sum(1 for c in rep.checks if c["status"] == "info"),
            "skip": sum(1 for c in rep.checks if c["status"] == "skip"),
        },
        "failed_gates": sorted({c["gate"] for c in failures}),
        "checks": rep.checks,
        "out_of_scope": {
            "A01": "原始源文件字节/修改检查由 git 与人工评审覆盖",
            "A11": "首页卡片/打字/统计开关/动效 -> verify_runtime.py",
            "A12": "tabs/滚动恢复/hash/侧栏高亮 -> verify_runtime.py（部分）与人工",
            "A13": "搜索 -> verify_runtime.py",
            "A16": "响应式与视觉 -> verify_runtime.py（溢出）+ 人工视觉结论",
            "A17": "干净环境严格构建 -> CI/人工",
            "A18": "真实 Pages 部署 -> P4/P6 人工",
        },
    }
    json_path = out_dir / "static-report.json"
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = []
    lines.append("# Zensical 迁移静态验收报告")
    lines.append("")
    lines.append(f"- 生成时间：{summary['generated_at']}")
    lines.append(f"- 基线：`{base_root}`")
    lines.append(f"- 目标：`{target_root}`")
    lines.append(f"- 目标指纹：{fingerprint_after['file_count']} 个文件，max mtime `{fingerprint_after['max_mtime']}`（运行前后{'一致' if fingerprint_before == fingerprint_after else '不一致，可能被并发重建'}）")
    lines.append(f"- 站点前缀：`{SITE_PREFIX}`")
    lines.append(f"- 耗时：{summary['elapsed_seconds']} 秒")
    lines.append(f"- **结论：{'FAIL' if failures else 'PASS'}**（pass {summary['counts']['pass']} / fail {summary['counts']['fail']} / warn {summary['counts']['warn']} / info {summary['counts']['info']}）")
    lines.append("")
    lines.append("## 按 A 门槛汇总")
    lines.append("")
    lines.append("| 门槛 | 说明 | pass | fail | warn | info |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for gate in sorted(GATE_TITLES):
        counts = gates.get(gate, {})
        if not counts:
            continue
        lines.append(
            f"| {gate} | {GATE_TITLES[gate]} | {counts.get('pass', 0)} | {counts.get('fail', 0)} | {counts.get('warn', 0)} | {counts.get('info', 0)} |"
        )
    lines.append("")
    if failures:
        lines.append("## 失败项")
        lines.append("")
        for c in failures:
            lines.append(f"### [{c['gate']}] {c['subject']}")
            lines.append("")
            lines.append(c["message"])
            lines.append("")
            details = c.get("details")
            if details:
                text = json.dumps(details, ensure_ascii=False, indent=1)
                if len(text) > 6000:
                    text = text[:6000] + "\n…（完整明细见 static-report.json）"
                lines.append("```json")
                lines.append(text)
                lines.append("```")
                lines.append("")
    else:
        lines.append("## 失败项")
        lines.append("")
        lines.append("无。静态验收全部检查项通过。")
        lines.append("")
    if warnings:
        lines.append("## 警告项")
        lines.append("")
        for c in warnings:
            lines.append(f"- [{c['gate']}] {c['subject']}: {c['message']}")
        lines.append("")
    lines.append("## 检查项明细")
    lines.append("")
    lines.append("| # | 门槛 | 检查项 | 状态 | 说明 |")
    lines.append("| --- | --- | --- | --- | --- |")
    for c in rep.checks:
        msg = c["message"].replace("|", "\\|")
        lines.append(f"| {c['seq']} | {c['gate']} | {c['subject']} | {c['status']} | {msg} |")
    lines.append("")
    lines.append("> 注：A11/A12/A13/A16 的交互与视觉部分由 `tools/verify_runtime.py` 覆盖；A01/A17/A18 由 CI、git 与人工部署复核覆盖。")
    md_path = out_dir / "static-report.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path


def main(argv: list[str] | None = None) -> int:
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Material 基线 vs Zensical 迁移构建的静态验收")
    parser.add_argument("--baseline", default=str(project_root / ".migration" / "baseline-material"))
    parser.add_argument("--target", default=str(project_root / "site-zensical"))
    parser.add_argument("--out", default=str(project_root / ".migration" / "verify"))
    parser.add_argument("--quiet", action="store_true", help="仅打印最终摘要，不逐项打印失败")
    parser.add_argument("--json-only", action="store_true", help="不打印人类可读摘要")
    args = parser.parse_args(argv)

    base_root = Path(args.baseline)
    target_root = Path(args.target)
    out_dir = Path(args.out)
    for label, root in (("baseline", base_root), ("target", target_root)):
        if not root.is_dir():
            print(f"ERROR: {label} 目录不存在：{root}", file=sys.stderr)
            return 2
    if not any(target_root.rglob("*.html")):
        print(f"ERROR: target 目录中没有 HTML 输出：{target_root}", file=sys.stderr)
        return 2

    import time

    started = time.time()
    base_pages = page_route_set(base_root)
    target_pages = page_route_set(target_root)
    fingerprint_before = dir_fingerprint(target_root)
    if not args.quiet:
        print(f"基线 {len(base_pages)} 个 HTML，目标 {len(target_pages)} 个 HTML；开始静态验收…", flush=True)

    rep = Report()
    check_routes(rep, base_pages, target_pages)
    # 只比较两边都存在的页面做内容检查，缺失页面由 A02 报告
    common = {rel: target_pages[rel] for rel in base_pages if rel in target_pages}
    check_staging_leak(rep, target_root, target_pages)
    check_canonical(rep, base_root, target_root, common)
    check_sitemap(rep, base_root, target_root)
    compare_page_contents(rep, base_root, target_root, common)
    check_toc(rep, base_root, target_root, common)
    check_home_statistics(rep, base_root, target_root)
    check_placeholders(rep, target_root, target_pages)
    check_page_statistics(rep, base_root, target_root, common)
    check_git_dates(rep, base_root, target_root, common)
    check_resource_counts(rep, base_root, target_root, common)
    check_giscus(rep, base_root, target_root, common)
    check_lightbox(rep, base_root, target_root, common)
    check_links(rep, base_root, target_root, common)

    elapsed = time.time() - started
    fingerprint_after = dir_fingerprint(target_root)
    stable = fingerprint_before == fingerprint_after
    rep.add(
        "A02",
        "目标产物稳定性",
        "pass" if stable else "fail",
        f"验收期间目标产物未变化（{fingerprint_after['file_count']} 个文件，max mtime {fingerprint_after['max_mtime']}）"
        if stable
        else f"验收期间目标产物发生变化（可能被并发重建）：before={fingerprint_before} after={fingerprint_after}",
        {"before": fingerprint_before, "after": fingerprint_after},
    )
    json_path = write_outputs(base_root, target_root, out_dir, rep, elapsed, fingerprint_before, fingerprint_after)
    failures = rep.failures()
    warnings = rep.warnings()
    print("")
    print("=" * 78)
    if not args.json_only:
        if failures:
            print(f"静态验收：FAIL — {len(failures)} 项失败，{len(warnings)} 项警告；失败门槛：{', '.join(sorted({c['gate'] for c in failures}))}")
        else:
            print(f"静态验收：PASS — {len(rep.checks)} 项检查全部通过（警告 {len(warnings)} 项）")
        print(f"JSON 报告：{json_path}")
        print(f"摘要报告：{out_dir / 'static-report.md'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

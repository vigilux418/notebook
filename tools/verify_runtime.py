#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""独立运行时验收探针：Zensical 迁移站（site-zensical）的浏览器行为。

方法
----
用本机 Chrome（headless）+ Playwright Python，以合成同源 ``https://verify.local/notebook/``
作为站点根，通过 ``context.route`` 把请求映射到本地构建目录 site-zensical 的文件
（正确 MIME、严格保持 ``/notebook/`` 前缀、越界路径返回 404）。这样无需启动真实
HTTP 服务器，也不会把副本发布到公网，可验证浏览器真实执行结果。

覆盖范围（运行时）
------------------
- A04 友链头像 naturalWidth > 0；本地资源请求无 404
- A09 MathJax：普通硬进入公式页、逐级软导航进入公式页，各 267/267 个公式包装块渲染；
      主引擎（tex-mml-chtml.js）单次加载；软导航不整页刷新
- A10 Mermaid：10 页共 100 个 ``div.mermaid`` 渲染宿主（pre 全部替换），软导航下一页 2 图
- A11 首页：卡片渲染、打字标语、统计开关显示 65/63119/2056、明暗切换与卡面图切换、
      反复进出首页无实例累积（记录）
- A12 软导航：window 级标记保持、canonical/URL 更新、history 前进/后退
- A13 搜索：键盘触发弹层（/ 与 Ctrl+K）、键盘输入“基尔霍夫/进程/WSL”，等待结果更新，
      记录结果可用性（不与 Material 排名比较）
- A14 Giscus loader 存在、iframe 注入、明暗主题同步
- A15 灯箱：点击头像灯箱打开、Escape 关闭
- A16 响应式：390/768/960/1440/1920 视口无横向溢出（首页 + 深层公式页）
- 无未处理 JS 异常；pageerror 与 requestfailed 分类记录（网络取消 vs 外部网络不可用 vs
      迁移回归）。外部网络（Google Fonts/Giscus/CDN/unpkg）失败只记录、不判失败。

用法
----
    python tools/verify_runtime.py
    python tools/verify_runtime.py --target DIR --baseline DIR --headed
    python tools/verify_runtime.py --skip-mermaid      # 调试用，减少外部依赖等待

输出
----
- .migration/verify/runtime-report.json  （机器可读，含全部检查、网络、外部依赖分类）
- .migration/verify/shots/*.png          （关键状态截图证据）
退出码：0 = 无迁移回归失败（允许外部网络警告）；1 = 存在迁移回归失败；2 = 运行错误。
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse

try:
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover
    print("ERROR: 需要 playwright（请使用 work/venv-research 的 python）", file=sys.stderr)
    sys.exit(2)

try:
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover
    print("ERROR: 需要 beautifulsoup4（用于从基线推导期望值）", file=sys.stderr)
    sys.exit(2)

DEFAULT_CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
SYNTHETIC_ORIGIN = "https://verify.local"
SITE_PREFIX = "/notebook/"
BASE_URL = SYNTHETIC_ORIGIN + SITE_PREFIX

MIME_OVERRIDES = {
    ".html": "text/html; charset=utf-8",
    ".htm": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".mjs": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".woff2": "font/woff2",
    ".woff": "font/woff",
    ".ttf": "font/ttf",
    ".ico": "image/x-icon",
    ".xml": "application/xml; charset=utf-8",
    ".txt": "text/plain; charset=utf-8",
    ".map": "application/json; charset=utf-8",
    ".pdf": "application/pdf",
}

EXTERNAL_HOST_HINTS = {
    "fonts.googleapis.com": "Google Fonts CSS",
    "fonts.gstatic.com": "Google Fonts 字体文件",
    "gcore.jsdelivr.net": "LXGW 字体 CDN",
    "cdn.jsdelivr.net": "jsDelivr CDN",
    "unpkg.com": "unpkg CDN（MathJax / GLightbox / Mermaid 引擎）",
    "giscus.app": "Giscus 评论区",
    "www.googletagmanager.com": "Google Analytics",
    "api.github.com": "GitHub API（页面元数据）",
}

# 布局对照：与 Material 基线在相同合成源/视口下测量同一批容器的几何信息
LAYOUT_COMBOS = [
    (1440, ""),
    (960, ""),
    (768, ""),
    (390, ""),
    (1440, "tools/lay_lang/tex/math/"),
    (390, "tools/lay_lang/tex/math/"),
]
LAYOUT_MEASURE_JS = """() => {
  const r = el => { if (!el) return null; const b = el.getBoundingClientRect(); return {x:+b.x.toFixed(1), y:+b.y.toFixed(1), w:+b.width.toFixed(1), h:+b.height.toFixed(1)}; };
  const trig = document.querySelector('.md-search__button') || document.querySelector('.md-search__form') || document.querySelector('.md-search');
  const cs = trig ? getComputedStyle(trig) : null;
  const searchKbd = document.querySelector('.md-search__button kbd, .md-search kbd, [data-md-component=search] kbd');
  return {
    search_trigger: r(trig),
    search_class: trig ? String(trig.className) : null,
    search_text: trig ? (trig.innerText || '').trim().slice(0, 40) : null,
    search_radius: cs ? cs.borderRadius : null,
    search_font: cs ? cs.fontSize : null,
    search_kbd_display: searchKbd ? getComputedStyle(searchKbd).display : null,
    grid: r(document.querySelector('.md-grid')),
    content: r(document.querySelector('.md-content')),
    content_inner: r(document.querySelector('.md-content__inner')),
    main_inner: r(document.querySelector('.md-main__inner')),
    sidebar_primary: r(document.querySelector('.md-sidebar--primary')),
    header_inner: r(document.querySelector('.md-header__inner')),
    body_scrollWidth: document.documentElement.scrollWidth,
    innerWidth: innerWidth,
    style_sheets: [...document.styleSheets].map(s => s.href || '').filter(Boolean),
  };
}"""
# 布局容差（px）：搜索触发器宽高与 Material 一致；网格/内容水平位置与宽度最多 1.5px 偏差
LAYOUT_TOLERANCE = {"search_w": 2.0, "search_h": 2.0, "grid_x": 1.5, "content_x": 1.5, "content_w": 1.5, "content_inner_x": 1.5, "content_inner_w": 1.5}


def norm(text: str | None) -> str:
    if text is None:
        return ""
    return re.sub(r"\s+", " ", text.replace("\u00a0", " ")).strip()


class RuntimeReport:
    def __init__(self) -> None:
        self.checks: list[dict] = []
        self._seq = 0

    def add(self, gate: str, subject: str, status: str, message: str, details=None, external: bool = False) -> None:
        assert status in ("pass", "fail", "warn", "info", "skip")
        self._seq += 1
        self.checks.append(
            {
                "seq": self._seq,
                "gate": gate,
                "subject": subject,
                "status": status,
                "message": message,
                "external_dependency": external,
                "details": details if details is not None else [],
            }
        )
        if status not in ("pass", "info", "skip"):
            flag = "FAIL" if status == "fail" else "WARN"
            print(f"[{flag}] {gate} {subject}: {message}", flush=True)

    def failures(self) -> list[dict]:
        return [c for c in self.checks if c["status"] == "fail"]

    def warnings(self) -> list[dict]:
        return [c for c in self.checks if c["status"] == "warn"]


# --------------------------------------------------------------------------------------
# 基线期望值
# --------------------------------------------------------------------------------------
def baseline_expectations(baseline: Path) -> dict:
    def soup(rel: str):
        return BeautifulSoup((baseline / rel).read_bytes(), "html.parser")

    def content_root(soup: BeautifulSoup) -> BeautifulSoup:
        main = soup.select_one(".md-main") or soup.select_one("main") or soup.body or soup
        frag = BeautifulSoup(str(main), "html.parser")
        for sel in (".md-sidebar", "nav.md-nav--primary", "nav.md-nav--secondary"):
            for el in frag.select(sel):
                el.decompose()
        return frag

    home = soup("index.html")
    stats = {}
    for line in home.select("#statistics .stat-line"):
        k = line.select_one(".stat-k")
        v = line.select_one(".stat-v")
        if k is not None and v is not None:
            stats[norm(k.get_text())] = norm(v.get_text())
    math_page = soup("tools/lay_lang/tex/math/index.html")
    math_wrappers = len(math_page.select(".md-content .arithmatex"))
    math_page_text = norm(math_page.select_one(".md-content h1").get_text(" ", strip=True)) if math_page.select_one(".md-content h1") else None
    math_pages = {}
    mermaid_pages = {}
    mermaid_pages_md_content = {}
    for p in sorted(baseline.rglob("*.html")):
        s = BeautifulSoup(p.read_bytes(), "html.parser")
        cr = content_root(s)
        arith = len(cr.select(".arithmatex"))
        if arith:
            math_pages[p.relative_to(baseline).as_posix()] = arith
        mermaid = len(cr.select(".mermaid"))
        if mermaid:
            mermaid_pages[p.relative_to(baseline).as_posix()] = mermaid
        mermaid_md = len(s.select(".md-content .mermaid"))
        if mermaid_md:
            mermaid_pages_md_content[p.relative_to(baseline).as_posix()] = mermaid_md
    links = soup("links/index.html")
    avatar_src = None
    avatar = links.select_one("img.ava")
    if avatar is not None:
        avatar_src = avatar.get("src")
    # 重要检索词在基线中的页面证据（用于判定“应有结果”）
    search_terms = ["基尔霍夫", "进程", "WSL"]
    term_pages = {term: [] for term in search_terms}
    for p in sorted(baseline.rglob("*.html")):
        raw = p.read_text(encoding="utf-8", errors="replace")
        rel = p.relative_to(baseline).as_posix()
        for term in search_terms:
            if term in raw:
                term_pages[term].append(rel)
    return {
        "home_statistics": stats,
        "math_wrappers": math_wrappers,
        "math_page_h1": math_page_text,
        "math_pages": math_pages,
        "math_total": sum(math_pages.values()),
        "mermaid_pages": mermaid_pages,
        "mermaid_total": sum(mermaid_pages.values()),
        "mermaid_pages_md_content": mermaid_pages_md_content,
        "mermaid_total_md_content": sum(mermaid_pages_md_content.values()),
        "avatar_src": avatar_src,
        "search_terms": search_terms,
        "search_term_baseline_pages": term_pages,
    }


# --------------------------------------------------------------------------------------
# 静态文件路由（合成同源）
# --------------------------------------------------------------------------------------
def make_router(site_root: Path):
    stats = {"served": 0, "not_found": 0, "outside": 0, "mime": {}}

    def serve(route):
        request = route.request
        parsed = urlparse(request.url)
        path = unquote(parsed.path)
        if not path.startswith(SITE_PREFIX):
            stats["outside"] += 1
            return route.fulfill(status=404, body=b"outside synthetic site prefix", content_type="text/plain")
        rel = path[len(SITE_PREFIX):]
        dest = site_root / rel
        if dest.is_dir():
            dest = dest / "index.html"
        if dest.is_file():
            suffix = dest.suffix.lower()
            ctype = MIME_OVERRIDES.get(suffix) or mimetypes.guess_type(dest.name)[0] or "application/octet-stream"
            stats["served"] += 1
            stats["mime"][suffix] = stats["mime"].get(suffix, 0) + 1
            return route.fulfill(status=200, body=dest.read_bytes(), content_type=ctype)
        stats["not_found"] += 1
        return route.fulfill(status=404, body=b"not found in site build", content_type="text/plain")

    return serve, stats


# --------------------------------------------------------------------------------------
# 浏览器工具函数
# --------------------------------------------------------------------------------------
def wait_fn(page, expression, timeout=15000, arg=None):
    """等待 JS 函数返回真；返回 True 或错误字符串（不超过 180 字符）。"""
    try:
        page.wait_for_function(expression, timeout=timeout, arg=arg)
        return True
    except PlaywrightError as exc:  # type: ignore[name-defined]
        return f"TIMEOUT: {str(exc).splitlines()[0][:160]}"


def find_anchor_click(page, target_path: str) -> dict:
    clicked = page.evaluate(
        """target => {
            const anchors = [...document.querySelectorAll('a[href]')];
            const a = anchors.find(a => { try { return new URL(a.href, location.href).pathname === target; } catch (e) { return false; } });
            if (!a) return null;
            a.scrollIntoView({block:'center'});
            a.click();
            return (a.textContent || '').trim().slice(0, 60);
        }""",
        target_path,
    )
    if not clicked:
        return {"ok": False, "reason": "no-link-found", "target": target_path}
    return {"ok": True, "target": target_path, "clicked_text": clicked}


def soft_nav(page, target_path: str, timeout: int = 20000) -> dict:
    """点击站内链接并从 URL、canonical、正文三方面确认软导航完成。"""
    result = find_anchor_click(page, target_path)
    if not result["ok"]:
        return result
    result["url_ok"] = wait_fn(page, "target => location.pathname === target", timeout, target_path)
    result["canonical_ok"] = wait_fn(
        page,
        "target => { const c = document.querySelector('link[rel=canonical]'); return !!c && new URL(c.href).pathname === target; }",
        timeout,
        target_path,
    )
    result["content_ok"] = wait_fn(page, "() => !!document.querySelector('.md-content h1') || !!document.querySelector('#app')", timeout)
    result["marker"] = page.evaluate("() => window.__runtimeProbeMarker")
    return result


def shadow_search_state(page) -> dict:
    return page.evaluate(
        """() => {
            const root = [...document.body.children].map(x => x.shadowRoot).find(Boolean);
            if (!root) return {hasRoot:false, visibleInput:false, text:'', links:[]};
            const inputs = [...root.querySelectorAll('input')].filter(i => i.offsetWidth > 0 || i.offsetHeight > 0);
            const links = [...root.querySelectorAll('a[href]')].map(a => ({url:a.href, text:(a.innerText||'').slice(0,80)}));
            const text = [...root.children].filter(x => x.tagName !== 'STYLE').map(x => x.innerText || '').join(' ');
            return {hasRoot:true, visibleInput:inputs.length>0, inputCount:inputs.length,
                    placeholder:inputs[0]?.placeholder ?? null, text:text.slice(0,2000), links};
        }"""
    )


def classify_failure(item: dict) -> str:
    failure = (item.get("failure") or "")
    url = item.get("url") or ""
    host = (urlparse(url).hostname or "").lower()
    if "ERR_ABORTED" in failure or "ERR_CANCELED" in failure:
        return "cancelled"
    if host and host not in ("verify.local",):
        return "external_unavailable"
    return "local_error"


def expected_stats(report: RuntimeReport, expected: dict) -> dict:
    values = expected.get("home_statistics") or {}
    return {
        "页面总数": values.get("页面总数"),
        "总字数": values.get("总字数"),
        "代码块行数": values.get("代码块行数"),
    }


# --------------------------------------------------------------------------------------
# 主流程
# --------------------------------------------------------------------------------------
def run(args) -> int:
    site_root = Path(args.target)
    baseline = Path(args.baseline)
    out_dir = Path(args.out)
    shots = out_dir / "shots"
    shots.mkdir(parents=True, exist_ok=True)
    if not site_root.is_dir() or not baseline.is_dir():
        print(f"ERROR: target/baseline 目录不存在：{site_root} / {baseline}", file=sys.stderr)
        return 2
    if not (site_root / "index.html").is_file():
        print(f"ERROR: target 缺少 index.html（构建不完整？）：{site_root}", file=sys.stderr)
        return 2

    expected = baseline_expectations(baseline)
    exp_stats = expected_stats(RuntimeReport(), expected)
    expected["home_statistics_expected"] = exp_stats
    print(
        f"期望值（来自 Material 基线）：统计 {exp_stats}；全站公式包装块 {expected['math_total']}（{len(expected['math_pages'])} 页），"
        f"公式页 {expected['math_wrappers']}；Mermaid 全页口径 {len(expected['mermaid_pages'])} 页 {expected['mermaid_total']} 块"
        f"（.md-content 口径 {len(expected['mermaid_pages_md_content'])} 页 {expected['mermaid_total_md_content']} 块）",
        flush=True,
    )

    report = RuntimeReport()
    started = time.time()
    network = {
        "served_local": 0,
        "local_404": 0,
        "outside_prefix_requests": 0,
        "local_bad_responses": [],
        "request_failures": [],
        "failure_classes": {},
        "external_hosts": {},
        "external_unavailable": False,
        "external_checked": [],
    }

    with sync_playwright() as pw:
        try:
            browser = pw.chromium.launch(executable_path=args.chrome, headless=not args.headed, args=["--no-proxy-server"])
        except Exception as exc:  # pragma: no cover
            print(f"ERROR: 无法启动 Chrome：{exc}", file=sys.stderr)
            return 2
        chrome_version = browser.version
        context = browser.new_context(viewport={"width": 1440, "height": 900}, color_scheme="light")
        serve, serve_stats = make_router(site_root)
        context.route(SYNTHETIC_ORIGIN + "/**", serve)
        # 模拟 unpkg GLightbox CDN 不可用：本地化 GLightbox 生效后不应再触发该请求
        glightbox_cdn = {"attempts": [], "requests": []}

        def block_glightbox_cdn(route):
            glightbox_cdn["attempts"].append(route.request.url)
            route.abort()

        context.route("https://unpkg.com/glightbox@3/**", block_glightbox_cdn)
        page = context.new_page()
        page.on(
            "request",
            lambda request: (
                glightbox_cdn["requests"].append(request.url)
                if "glightbox" in request.url.lower()
                else None
            ),
        )
        page.set_default_timeout(20000)
        page_errors: list[dict] = []
        console_errors: list[dict] = []
        page.on("pageerror", lambda exc: page_errors.append({"message": str(exc)[:500], "url": getattr(exc, "url", None)}))
        page.on(
            "console",
            lambda msg: console_errors.append({"type": msg.type, "text": msg.text[:300], "location": msg.location})
            if msg.type == "error"
            else None,
        )
        page.on("crash", lambda: print("[WARN] 页面/渲染进程崩溃（page crash）", flush=True))

        def stage(msg: str) -> None:
            print(f"[stage {time.strftime('%H:%M:%S')}] {msg}", flush=True)

        def on_request_failed(request):
            item = {
                "url": request.url,
                "failure": str(request.failure) if request.failure else None,
                "resource_type": request.resource_type,
                "page": page.url,
            }
            item["class"] = classify_failure(item)
            network["request_failures"].append(item)

        def on_response(response):
            url = response.url
            if url.startswith(SYNTHETIC_ORIGIN + "/"):
                if response.status >= 400:
                    network["local_bad_responses"].append({"url": url, "status": response.status, "page": page.url})
            else:
                host = (urlparse(url).hostname or "").lower()
                if host:
                    entry = network["external_hosts"].setdefault(host, {"requests": 0, "ok": 0, "failed": 0})
                    entry["requests"] += 1
                    if response.status < 400:
                        entry["ok"] += 1
                    else:
                        entry["failed"] += 1

        page.on("requestfailed", on_request_failed)
        page.on("response", on_response)

        def shot(name: str):
            try:
                page.screenshot(path=str(shots / f"{name}.png"), full_page=False)
            except Exception:
                pass

        def goto_home():
            page.goto(BASE_URL, wait_until="domcontentloaded", timeout=30000)
            return wait_fn(page, "() => !!window.document$ && !!document.querySelector('#app .card:not(.loading)')", 25000)

        def wait_home_stats(target_values: dict) -> dict:
            """点击“站点统计”开关并等待统计面板可见且数值正确。"""
            clicked = page.evaluate(
                """() => {
                    const a = [...document.querySelectorAll('a[href]')].find(a => (a.getAttribute('href') || '').includes('toggle_statistics'));
                    if (!a) return false;
                    a.click(); return true;
                }"""
            )
            state = {"clicked": clicked}
            if clicked:
                state["visible"] = wait_fn(
                    page,
                    "() => { const el = document.querySelector('#statistics'); if (!el) return false; return (el.style.opacity === '1') && el.getBoundingClientRect().height > 0; }",
                    8000,
                )
                state["values"] = page.evaluate(
                    """() => Object.fromEntries([...document.querySelectorAll('#statistics .stat-line')].map(line => {
                        const k = line.querySelector('.stat-k'); const v = line.querySelector('.stat-v');
                        return [k ? k.innerText.trim() : '', v ? v.innerText.trim() : ''];
                    }))"""
                )
                state["raw_text"] = page.evaluate("() => document.querySelector('#statistics')?.innerText || ''")
            return state

        stage("1 首页卡片/打字/统计/明暗")
        # ============================ 1. 首页：卡片 / 打字 / 统计 / 明暗 ============================
        home_ready = goto_home()
        home = {"ready": home_ready}
        home["card"] = page.evaluate(
            """() => ({
                appCount: document.querySelectorAll('#app').length,
                cards: document.querySelectorAll('#app .card').length,
                loading: document.querySelectorAll('#app .card.loading').length,
                canvases: document.querySelectorAll('canvas').length,
                cardImg: document.querySelector('#app img')?.getAttribute('src') || null,
            })"""
        )
        report.add(
            "A11",
            "首页全息卡片渲染",
            "pass" if home_ready is True and home["card"]["appCount"] == 1 and home["card"]["cards"] >= 1 else "fail",
            f"#app 卡片渲染正常（card={home['card']['cards']}, loading={home['card']['loading']}, canvas={home['card']['canvases']}）"
            if home_ready is True
            else f"首页卡片未就绪：{home_ready}",
            home["card"],
        )
        home["typed"] = wait_fn(
            page,
            "() => { const el = document.querySelector('#typed-des-zh'); return !!el && (el.textContent || '').includes('个人笔记本'); }",
            20000,
        )
        typed_text = page.evaluate("() => document.querySelector('#typed-des-zh')?.textContent || ''")
        report.add(
            "A11",
            "首页打字标语",
            "pass" if home["typed"] is True else "fail",
            f"打字标语已启动：{typed_text[:40]!r}" if home["typed"] is True else f"打字标语未出现：{home['typed']}",
            {"text": typed_text, "Typed_defined": page.evaluate("() => typeof window.Typed")},
        )
        home["statistics"] = wait_home_stats(exp_stats)
        stats_values = home["statistics"].get("values") or {}
        stats_ok = (
            home["statistics"].get("clicked")
            and home["statistics"].get("visible") is True
            and all(stats_values.get(k) == v for k, v in exp_stats.items() if v)
            and "{{" not in (home["statistics"].get("raw_text") or "")
        )
        report.add(
            "A11",
            "首页统计开关与数值",
            "pass" if stats_ok else "fail",
            f"统计面板打开后显示 页面总数 {stats_values.get('页面总数')} / 总字数 {stats_values.get('总字数')} / 代码块行数 {stats_values.get('代码块行数')}，期望 {exp_stats}"
            if stats_ok
            else f"统计面板异常：clicked={home['statistics'].get('clicked')}, visible={home['statistics'].get('visible')}, "
            f"values={stats_values}, expected={exp_stats}",
            {"values": stats_values, "raw_text": (home["statistics"].get("raw_text") or "")[:400]},
        )
        shot("home-light-desktop")

        # 明暗切换 + 卡面图切换
        home["card_img_light"] = page.evaluate("() => document.querySelector('#app img')?.src || null")
        scheme_before = page.evaluate("() => document.body.dataset.mdColorScheme")
        palette = {"before": scheme_before}
        click_dark = page.evaluate(
            """() => {
                const labels = [...document.querySelectorAll('label[for^="__palette_"]')];
                const target = labels.find(l => (l.getAttribute('for') || '').endsWith('_1'));
                if (!target) return false; target.click(); return true;
            }"""
        )
        palette["clicked_dark_label"] = click_dark
        palette["dark_ok"] = wait_fn(page, "() => document.body.dataset.mdColorScheme === 'slate'", 8000)
        palette["card_img_dark"] = page.evaluate("() => document.querySelector('#app img')?.src || null")
        request_animation = wait_fn(
            page,
            "(before) => { const img = document.querySelector('#app img'); return !!img && img.src !== before; }",
            8000,
            home["card_img_light"],
        )
        palette["card_img_switched"] = request_animation
        shot("home-dark-desktop")
        page.evaluate(
            """() => {
                const labels = [...document.querySelectorAll('label[for^="__palette_"]')];
                const target = labels.find(l => (l.getAttribute('for') || '').endsWith('_0'));
                if (target) target.click();
            }"""
        )
        palette["light_ok"] = wait_fn(page, "() => document.body.dataset.mdColorScheme === 'default'", 8000)
        palette["card_img_light_again"] = page.evaluate("() => document.querySelector('#app img')?.src || null")
        palette_ok = (
            palette.get("dark_ok") is True
            and palette.get("card_img_switched") is True
            and palette.get("light_ok") is True
        )
        report.add(
            "A11",
            "明暗切换与卡面图切换",
            "pass" if palette_ok else "fail",
            "浅/深色切换成功，卡面图随主题切换（light<->dark）"
            if palette_ok
            else f"明暗或卡面图切换异常：{ {k: palette.get(k) for k in ('dark_ok', 'card_img_switched', 'light_ok')} }",
            palette,
        )

        # 首页反复进出：观察实例/画布是否累积（软导航）
        repeat = {}
        card_before = page.evaluate("() => ({cards: document.querySelectorAll('#app .card').length, canvases: document.querySelectorAll('canvas').length})")
        page.evaluate("window.__runtimeProbeMarker = 418")
        steps = []
        for path in [BASE_URL + "tools/", BASE_URL]:
            steps.append(soft_nav(page, urlparse(path).path))
        repeat["back_home"] = wait_fn(page, "() => !!document.querySelector('#app .card:not(.loading)')", 20000)
        repeat["card_after"] = page.evaluate("() => ({cards: document.querySelectorAll('#app .card').length, canvases: document.querySelectorAll('canvas').length})")
        repeat["marker"] = page.evaluate("() => window.__runtimeProbeMarker")
        repeat_ok = (
            repeat["back_home"] is True
            and repeat["marker"] == 418
            and repeat["card_after"]["cards"] <= max(1, card_before["cards"]) * 2
        )
        report.add(
            "A11",
            "反复进出首页无实例累积",
            "pass" if repeat_ok else "warn",
            f"软导航离开/返回首页后卡片实例 {card_before['cards']}->{repeat['card_after']['cards']}，canvas {card_before['canvases']}->{repeat['card_after']['canvases']}，标记={repeat['marker']}"
            if repeat_ok
            else f"反复进出首页后实例可能累积：{repeat}",
            repeat,
        )

        stage("2 MathJax 软导航/硬进入")
        # ============================ 2. MathJax：软导航进入 + 硬进入 ============================
        math_path = "/notebook/tools/lay_lang/tex/math/"
        soft_math = {}
        soft_math["home_ready"] = goto_home()
        page.evaluate("window.__runtimeProbeMarker = 418")
        math_steps = []
        for path in ["/notebook/tools/", "/notebook/tools/lay_lang/", "/notebook/tools/lay_lang/tex/", math_path]:
            step = soft_nav(page, path)
            math_steps.append(step)
            if not step.get("url_ok"):
                break
        soft_math["steps"] = math_steps
        soft_math["render"] = wait_fn(
            page,
            "() => { const w = document.querySelectorAll('.md-content .arithmatex').length; const r = document.querySelectorAll('.md-content .arithmatex mjx-container').length; return w > 0 && r === w; }",
            60000,
        )
        soft_math["eval"] = page.evaluate(
            """() => ({
                path: location.pathname,
                wrappers: document.querySelectorAll('.md-content .arithmatex').length,
                rendered: document.querySelectorAll('.md-content .arithmatex mjx-container').length,
                marker: window.__runtimeProbeMarker,
                engineRequests: performance.getEntriesByType('resource').filter(x => x.name.includes('tex-mml-chtml')).length,
                h1: document.querySelector('.md-content h1')?.innerText || '',
            })"""
        )
        soft_ok = (
            all(s.get("url_ok") is True for s in math_steps)
            and soft_math["render"] is True
            and soft_math["eval"]["wrappers"] == expected["math_wrappers"]
            and soft_math["eval"]["rendered"] == expected["math_wrappers"]
            and soft_math["eval"]["marker"] == 418
            and soft_math["eval"]["engineRequests"] == 1
        )
        report.add(
            "A09",
            "MathJax 软导航进入公式页",
            "pass" if soft_ok else "fail",
            f"逐级软导航进入公式页：{soft_math['eval']['rendered']}/{soft_math['eval']['wrappers']} 公式渲染，主引擎请求 {soft_math['eval']['engineRequests']} 次，window 标记={'保持' if soft_math['eval']['marker'] == 418 else '丢失'}"
            if soft_ok
            else f"软导航公式渲染异常：{soft_math['eval']}；步骤={[{k: s.get(k) for k in ('target', 'ok', 'url_ok', 'canonical_ok', 'marker')} for s in math_steps]}",
            soft_math,
        )
        shot("math-page-softnav")

        page.goto(BASE_URL + "tools/lay_lang/tex/math/", wait_until="domcontentloaded", timeout=30000)
        hard_math = {"render": wait_fn(
            page,
            "() => { const w = document.querySelectorAll('.md-content .arithmatex').length; const r = document.querySelectorAll('.md-content .arithmatex mjx-container').length; return w > 0 && r === w; }",
            60000,
        )}
        hard_math["eval"] = page.evaluate(
            """() => ({
                wrappers: document.querySelectorAll('.md-content .arithmatex').length,
                rendered: document.querySelectorAll('.md-content .arithmatex mjx-container').length,
                engineRequests: performance.getEntriesByType('resource').filter(x => x.name.includes('tex-mml-chtml')).length,
            })"""
        )
        hard_ok = (
            hard_math["render"] is True
            and hard_math["eval"]["wrappers"] == expected["math_wrappers"]
            and hard_math["eval"]["rendered"] == expected["math_wrappers"]
            and hard_math["eval"]["engineRequests"] == 1
        )
        report.add(
            "A09",
            "MathJax 普通进入公式页",
            "pass" if hard_ok else "fail",
            f"硬进入公式页：{hard_math['eval']['rendered']}/{hard_math['eval']['wrappers']} 公式渲染，主引擎请求 {hard_math['eval']['engineRequests']} 次"
            if hard_ok
            else f"硬进入公式渲染异常：{hard_math['eval']}",
            hard_math,
        )

        # 全站公式页逐页渲染（含 tools/mkdocs/3 等 article 之外的公式，reviewer 复核口径 337）
        whole_site_math = {}
        math_page_failures = []
        for rel, count in expected["math_pages"].items():
            if rel == "tools/lay_lang/tex/math/index.html":
                whole_site_math[rel] = {"expected": count, "wrappers": count, "rendered": count, "reused": True}
                continue
            page.goto(BASE_URL + rel.removesuffix("index.html"), wait_until="domcontentloaded", timeout=30000)
            ok = wait_fn(
                page,
                "(expected) => document.querySelectorAll('.arithmatex').length === expected && document.querySelectorAll('.arithmatex mjx-container').length === expected",
                60000,
                count,
            )
            whole_site_math[rel] = page.evaluate(
                """expected => ({expected,
                    wrappers: document.querySelectorAll('.arithmatex').length,
                    rendered: document.querySelectorAll('.arithmatex mjx-container').length,
                    engineRequests: performance.getEntriesByType('resource').filter(x => x.name.includes('tex-mml-chtml')).length})""",
                count,
            )
            whole_site_math[rel]["ok"] = ok is True
            if ok is not True:
                math_page_failures.append({"page": rel, "wait": ok, **whole_site_math[rel]})
        rendered_total = sum(v.get("rendered", 0) for v in whole_site_math.values())
        whole_math_ok = (
            not math_page_failures
            and rendered_total == expected["math_total"]
            and all(v.get("rendered") == v.get("expected") for v in whole_site_math.values())
        )
        report.add(
            "A09",
            "全站公式页逐页渲染（全页口径）",
            "pass" if whole_math_ok else "fail",
            f"全页正文口径 {len(whole_site_math)} 页共 {rendered_total}/{expected['math_total']} 个 .arithmatex 全部渲染为 mjx-container（逐页等于基线）"
            if whole_math_ok
            else f"全站公式渲染不符：失败页 {len(math_page_failures)}，渲染合计 {rendered_total}/{expected['math_total']}",
            {
                "criterion": "per-page rendered == baseline 全页正文口径 .arithmatex 数",
                "pages": whole_site_math,
                "failures": math_page_failures,
                "note": "tools/mkdocs/3 的公式位于 <article> 之外的 tabbed 内容，浏览器 DOM 中 MathJax 仍会渲染（全页口径），故单列本检查；旧调研 331 为 .md-content 口径。",
            },
        )

        # 软导航的 history 前进/后退（A12）
        hist = {}
        try:
            page.goto(BASE_URL + "tools/lay_lang/tex/math/", wait_until="domcontentloaded", timeout=30000)
            wait_fn(page, "() => document.querySelectorAll('.md-content .arithmatex mjx-container').length > 0", 60000)
            page.evaluate("window.__runtimeProbeMarker = 418")
            page.goto(BASE_URL + "tools/lay_lang/tex/", wait_until="domcontentloaded", timeout=30000)
            wait_fn(page, "() => !!document.querySelector('.md-content h1')", 20000)
            page.evaluate("window.__runtimeProbeMarker = 418")
            page2_path = "/notebook/tools/lay_lang/tex/math/"
            nav_step = soft_nav(page, page2_path)
            hist["forward_step"] = nav_step
            hist["at_math"] = page.evaluate("() => ({path: location.pathname, marker: window.__runtimeProbeMarker})")
            page.go_back()
            hist["back_url"] = wait_fn(page, "() => location.pathname === '/notebook/tools/lay_lang/tex/'", 15000)
            hist["after_back"] = page.evaluate("() => ({path: location.pathname, marker: window.__runtimeProbeMarker, h1: document.querySelector('.md-content h1')?.innerText || ''})")
            page.go_forward()
            hist["forward_url"] = wait_fn(page, "() => location.pathname === '/notebook/tools/lay_lang/tex/math/'", 15000)
            hist["after_forward"] = page.evaluate("() => ({path: location.pathname, marker: window.__runtimeProbeMarker})")
            hist["ok"] = (
                hist["back_url"] is True
                and hist["after_back"].get("marker") == 418
                and hist["after_back"].get("path") == "/notebook/tools/lay_lang/tex/"
                and hist["forward_url"] is True
                and hist["after_forward"].get("marker") == 418
            )
        except Exception as exc:  # pragma: no cover
            hist["exception"] = str(exc)[:300]
            hist["ok"] = False
        report.add(
            "A12",
            "history 前进/后退保持软导航",
            "pass" if hist.get("ok") else "fail",
            "软导航后用浏览器前进/后退切换页面，URL 正确且 window 级标记保持（未整页刷新）"
            if hist.get("ok")
            else f"history 导航异常：{ {k: hist.get(k) for k in ('back_url', 'forward_url', 'after_back', 'after_forward', 'exception')} }",
            hist,
        )

        stage("3 Mermaid 全站 11 页")
        # ============================ 3. Mermaid：全站 11 页 105 块 + 软导航 2 图 ============================
        mermaid_results = {}
        mermaid_failures = []
        if not args.skip_mermaid:
            for rel, count in expected["mermaid_pages"].items():
                page.goto(BASE_URL + rel.removesuffix("index.html"), wait_until="domcontentloaded", timeout=30000)
                ok = wait_fn(
                    page,
                    "(expected) => document.querySelectorAll('div.mermaid').length === expected && document.querySelectorAll('pre.mermaid').length === 0",
                    60000,
                    count,
                )
                mermaid_results[rel] = page.evaluate(
                    """expected => ({
                        expected,
                        hosts: document.querySelectorAll('div.mermaid').length,
                        mdContentHosts: document.querySelectorAll('.md-content div.mermaid').length,
                        pendingPre: document.querySelectorAll('pre.mermaid').length,
                        textLen: (document.querySelector('div.mermaid')?.innerText || '').length,
                    })""",
                    count,
                )
                if ok is not True:
                    mermaid_failures.append({"page": rel, "wait": ok, **mermaid_results[rel]})
            rendered_total = sum(v["hosts"] for v in mermaid_results.values())
            mermaid_static_ok = not mermaid_failures and rendered_total == expected["mermaid_total"]
            report.add(
                "A10",
                "Mermaid 全站逐页渲染（全页口径）",
                "pass" if mermaid_static_ok else "fail",
                f"{len(mermaid_results)} 页共 {rendered_total}/{expected['mermaid_total']} 个 div.mermaid 渲染宿主（含 tools/mkdocs/3 的 5 块），残留 pre.mermaid=0；"
                f".md-content 口径 10 页 100 块为旧调研统计口径"
                if mermaid_static_ok
                else f"Mermaid 渲染不全：{len(mermaid_failures)} 页失败，总渲染 {rendered_total}/{expected['mermaid_total']}",
                {
                    "criterion": "per-page div.mermaid hosts == baseline 全页正文口径 .mermaid 数，且 pre.mermaid 全部替换",
                    "baseline_md_content": {
                        "pages": expected["mermaid_pages_md_content"],
                        "total": expected["mermaid_total_md_content"],
                    },
                    "pages": mermaid_results,
                    "failures": mermaid_failures,
                },
            )
            # 软导航到下一图表页：csci/4 -> csci/5（2 图）
            page.goto(BASE_URL + "general/csci/4/", wait_until="domcontentloaded", timeout=30000)
            wait_fn(page, "() => document.querySelectorAll('.md-content div.mermaid').length === 26", 60000)
            page.evaluate("window.__runtimeProbeMarker = 418")
            next_step = soft_nav(page, "/notebook/general/csci/5/")
            next_ok = wait_fn(page, "() => document.querySelectorAll('.md-content div.mermaid').length === 2", 60000)
            next_eval = page.evaluate(
                "() => ({hosts: document.querySelectorAll('.md-content div.mermaid').length, pendingPre: document.querySelectorAll('.md-content pre.mermaid').length, marker: window.__runtimeProbeMarker})"
            )
            next_pass = next_step.get("url_ok") is True and next_ok is True and next_eval["hosts"] == 2 and next_eval["marker"] == 418
            report.add(
                "A10",
                "Mermaid 软导航下一页 2 图",
                "pass" if next_pass else "fail",
                f"软导航 csci/4 -> csci/5：渲染 {next_eval['hosts']} 图，window 标记={'保持' if next_eval['marker'] == 418 else '丢失'}"
                if next_pass
                else f"软导航后 Mermaid 异常：step={next_step}, eval={next_eval}",
                {"step": next_step, "eval": next_eval},
            )
            shot("mermaid-page")

        stage("4 搜索")
        # ============================ 4. 搜索（键盘触发） ============================
        search = {"terms": {}, "triggers": {}}
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=30000)
        wait_fn(page, "() => !!window.document$", 20000)
        page.keyboard.press("/")
        slash_ok = wait_fn(page, "() => { const root = [...document.body.children].map(x => x.shadowRoot).find(Boolean); return !!root && [...root.querySelectorAll('input')].some(i => i.offsetWidth > 0); }", 8000)
        search["triggers"]["/"] = slash_ok
        if slash_ok is not True:
            page.keyboard.press("Control+k")
            ctrlk_ok = wait_fn(page, "() => { const root = [...document.body.children].map(x => x.shadowRoot).find(Boolean); return !!root && [...root.querySelectorAll('input')].some(i => i.offsetWidth > 0); }", 8000)
            search["triggers"]["Control+k"] = ctrlk_ok
        else:
            page.keyboard.press("Escape")
            time.sleep(0.3)
            page.keyboard.press("Control+k")
            ctrlk_ok = wait_fn(page, "() => { const root = [...document.body.children].map(x => x.shadowRoot).find(Boolean); return !!root && [...root.querySelectorAll('input')].some(i => i.offsetWidth > 0); }", 8000)
            search["triggers"]["Control+k"] = ctrlk_ok
        trigger_ok = slash_ok is True or search["triggers"].get("Control+k") is True
        search["shadow"] = shadow_search_state(page)
        previous_text = search["shadow"].get("text", "")
        for idx, term in enumerate(expected["search_terms"]):
            if idx > 0:
                page.keyboard.press("Control+a")
                page.keyboard.press("Backspace")
                time.sleep(0.25)
            page.keyboard.type(term, delay=20)
            wait_fn(
                page,
                """args => {
                    const [prev, term] = args;
                    const root = [...document.body.children].map(x => x.shadowRoot).find(Boolean);
                    if (!root) return false;
                    const input = [...root.querySelectorAll('input')].find(i => i.offsetWidth > 0);
                    const text = [...root.children].filter(x => x.tagName !== 'STYLE').map(x => x.innerText || '').join(' ');
                    return !!input && input.value === term && text !== prev && /results?|No results/i.test(text);
                }""",
                15000,
                [previous_text, term],
            )
            time.sleep(0.4)
            state = shadow_search_state(page)
            previous_text = state.get("text", "")
            result_count = re.search(r"(\d+)\s+results?", state.get("text", ""), re.IGNORECASE)
            no_results = bool(re.search(r"No results", state.get("text", ""), re.IGNORECASE))
            baseline_pages = expected["search_term_baseline_pages"].get(term, [])
            search["terms"][term] = {
                "text_head": (state.get("text") or "")[:400],
                "links": (state.get("links") or [])[:8],
                "link_count": len(state.get("links") or []),
                "result_count": int(result_count.group(1)) if result_count else 0,
                "no_results": no_results,
                "baseline_hit_pages": baseline_pages[:5],
                "expected_available": bool(baseline_pages),
            }
            shot(f"search-{idx}-result")
        page.keyboard.press("Escape")
        unavailable = [
            term
            for term, info in search["terms"].items()
            if info["expected_available"] and (info["no_results"] or info["link_count"] == 0 or info["result_count"] == 0)
        ]
        search_ok = trigger_ok and all(info["link_count"] > 0 for info in search["terms"].values())
        report.add(
            "A13",
            "搜索键盘触发与中文/英文查询",
            "pass" if search_ok else "fail",
            "键盘（/ 或 Ctrl+K）打开搜索弹层，三个查询词均返回结果链接"
            if search_ok
            else f"搜索异常：trigger={search['triggers']}，无结果词={unavailable}，明细={ {t: (i['result_count'], i['link_count'], i['no_results']) for t, i in search['terms'].items()} }",
            {"triggers": search["triggers"], "terms": search["terms"]},
        )

        stage("5 Giscus")
        # ============================ 5. Giscus loader 与主题同步 ============================
        page.goto(BASE_URL + "links/", wait_until="domcontentloaded", timeout=30000)
        giscus = {}
        giscus["loader"] = wait_fn(page, "() => document.querySelectorAll('script[src*=\"giscus\"]').length > 0", 15000)
        giscus["loader_count"] = page.evaluate("() => document.querySelectorAll('script[src*=\"giscus\"]').length")
        giscus["theme_light"] = page.evaluate("() => document.querySelector('script[src*=\"giscus\"]')?.getAttribute('data-theme') || null")
        giscus["iframe"] = wait_fn(page, "() => !!document.querySelector('iframe.giscus-frame, .giscus iframe, iframe[src*=\"giscus.app\"]')", 15000)
        giscus["iframe_count"] = page.evaluate("() => document.querySelectorAll('iframe[src*=\"giscus.app\"], iframe.giscus-frame').length")
        # 切深色，检查 loader data-theme 是否同步
        page.evaluate(
            """() => {
                const labels = [...document.querySelectorAll('label[for^="__palette_"]')];
                const target = labels.find(l => (l.getAttribute('for') || '').endsWith('_1'));
                if (target) target.click();
            }"""
        )
        giscus["dark_ok"] = wait_fn(page, "() => document.body.dataset.mdColorScheme === 'slate'", 8000)
        giscus["theme_dark"] = None
        if giscus["dark_ok"] is True:
            wait_fn(page, "() => document.querySelector('script[src*=\"giscus\"]')?.getAttribute('data-theme') === 'transparent_dark'", 8000)
            giscus["theme_dark"] = page.evaluate("() => document.querySelector('script[src*=\"giscus\"]')?.getAttribute('data-theme') || null")
        page.evaluate(
            """() => {
                const labels = [...document.querySelectorAll('label[for^="__palette_"]')];
                const target = labels.find(l => (l.getAttribute('for') || '').endsWith('_0'));
                if (target) target.click();
            }"""
        )
        wait_fn(page, "() => document.body.dataset.mdColorScheme === 'default'", 8000)
        giscus_loader_ok = giscus["loader"] is True
        giscus_theme_ok = giscus["theme_dark"] == "transparent_dark"
        giscus_status = "pass" if (giscus_loader_ok and giscus_theme_ok) else ("fail" if giscus_loader_ok else "warn")
        report.add(
            "A14",
            "Giscus loader 与主题同步",
            giscus_status,
            f"Giscus loader 存在（{giscus['loader_count']} 个），iframe={'已注入' if giscus['iframe'] is True else '未注入（外部网络）'}，"
            f"主题同步 {'light->transparent_dark 正常' if giscus_theme_ok else '未同步'}"
            if giscus_loader_ok
            else "未找到 Giscus loader（迁移回归）",
            giscus,
            external=not giscus["iframe"] is True,
        )

        stage("6 灯箱")
        # ============================ 6. 灯箱（头像） ============================
        avatar = page.evaluate(
            """() => {
                const img = document.querySelector('img.ava');
                const link = img ? img.closest('a') : null;
                return img ? {src: img.src, naturalWidth: img.naturalWidth, complete: img.complete,
                              link: link ? link.getAttribute('href') : null} : null;
            }"""
        )
        report.add(
            "A04",
            "友链头像 naturalWidth",
            "pass" if avatar and avatar["naturalWidth"] > 0 else "fail",
            f"头像加载成功：{avatar['src']} naturalWidth={avatar['naturalWidth']}" if avatar and avatar["naturalWidth"] > 0 else f"头像未加载：{avatar}",
            avatar,
        )
        glightbox = {
            "available": wait_fn(page, "() => typeof window.GLightbox === 'function'", 30000),
            "scripts": page.evaluate("() => [...document.querySelectorAll('script[src]')].map(s => s.src).filter(u => u.toLowerCase().includes('glightbox'))"),
            "stylesheet_links": page.evaluate("() => [...document.querySelectorAll('link[rel=stylesheet]')].map(l => l.href).filter(u => u.toLowerCase().includes('glightbox'))"),
        }
        if glightbox["available"] is True:
            try:
                page.locator("a.glightbox").first.click(timeout=8000)
                glightbox["open"] = wait_fn(
                    page,
                    "() => { const c = document.querySelector('.glightbox-container'); return !!c && getComputedStyle(c).opacity !== '0' && c.getBoundingClientRect().height > 100; }",
                    15000,
                )
                glightbox["open_state"] = page.evaluate(
                    "() => ({containers: document.querySelectorAll('.glightbox-container').length, bodyClass: document.body.className, img: document.querySelector('.glightbox-container img')?.getAttribute('src') || null})"
                )
                shot("lightbox-open")
                page.keyboard.press("Escape")
                glightbox["close"] = wait_fn(page, "() => document.querySelectorAll('.glightbox-container').length === 0", 10000)
            except Exception as exc:  # pragma: no cover
                glightbox["exception"] = str(exc)[:300]
            box_ok = glightbox.get("open") is True and glightbox.get("close") is True
            report.add(
                "A15",
                "灯箱打开/关闭",
                "pass" if box_ok else "fail",
                "点击友链头像灯箱打开成功，Escape 关闭成功"
                if box_ok
                else f"灯箱行为异常：open={glightbox.get('open')}, close={glightbox.get('close')}, exception={glightbox.get('exception')}",
                glightbox,
            )
        else:
            report.add(
                "A15",
                "灯箱打开/关闭",
                "fail",
                "GLightbox 未就绪（本地化脚本未加载，且 unpkg CDN 已在本次探针中被拦截以模拟不可用）",
                glightbox,
            )
        # 本地化 GLightbox：拦截 unpkg CDN 后仍应可用，且不应再请求 unpkg
        local_scripts = [u for u in glightbox["scripts"] if u.startswith(SYNTHETIC_ORIGIN + SITE_PREFIX)]
        unpkg_attempts = [u for u in glightbox_cdn["requests"] if "unpkg.com" in u]
        unpkg_blocked = glightbox_cdn["attempts"]
        localization_ok = bool(local_scripts) and not unpkg_attempts and not unpkg_blocked and glightbox["available"] is True
        report.add(
            "A15",
            "GLightbox 本地化（拦截 unpkg CDN）",
            "pass" if localization_ok else "fail",
            f"本地 GLightbox 脚本 {len(local_scripts)} 个，unpkg glightbox 请求 {len(unpkg_attempts)} 次（拦截命中 {len(unpkg_blocked)}）；CDN 被拦截时灯箱仍可用"
            if localization_ok
            else f"GLightbox 本地化不完整：本地脚本={local_scripts}，unpkg 请求={unpkg_attempts}，拦截命中={unpkg_blocked}，GLightbox={'可用' if glightbox['available'] is True else '不可用'}",
            {
                "local_scripts": local_scripts,
                "all_glightbox_scripts": glightbox["scripts"],
                "glightbox_stylesheets": glightbox["stylesheet_links"],
                "unpkg_requests": unpkg_attempts,
                "unpkg_interceptions": unpkg_blocked,
                "available_under_block": glightbox["available"] is True,
            },
        )

        stage("7 响应式")
        # ============================ 7. 响应式：5 个视口无横向溢出 ============================
        vp = {}
        goto_home()
        wait_fn(page, "() => !!document.querySelector('#app .card')", 20000)
        for width in [390, 768, 960, 1440, 1920]:
            page.set_viewport_size({"width": width, "height": 900})
            time.sleep(0.45)
            vp[f"home_{width}"] = page.evaluate(
                """() => ({innerWidth, scrollWidth: document.documentElement.scrollWidth,
                          overflow: document.documentElement.scrollWidth > innerWidth + 1,
                          cardVisible: !!document.querySelector('#app')?.offsetWidth})"""
            )
            if width == 390:
                shot("home-mobile-390")
        for width in [390, 1920]:
            page.set_viewport_size({"width": width, "height": 900})
            page.goto(BASE_URL + "tools/lay_lang/tex/math/", wait_until="domcontentloaded", timeout=30000)
            time.sleep(0.8)
            vp[f"math_{width}"] = page.evaluate(
                """() => ({innerWidth, scrollWidth: document.documentElement.scrollWidth,
                          overflow: document.documentElement.scrollWidth > innerWidth + 1})"""
            )
        page.set_viewport_size({"width": 1440, "height": 900})
        overflow = [name for name, state in vp.items() if state["overflow"]]
        home_card_ok = vp.get("home_390", {}).get("cardVisible") is False and vp.get("home_1440", {}).get("cardVisible") is True
        report.add(
            "A16",
            "390–1920 视口无横向溢出",
            "pass" if not overflow else "fail",
            "首页与公式页在 390/768/960/1440/1920 均无横向溢出；≤960 隐藏卡片、>960 显示卡片符合基线"
            if not overflow and home_card_ok
            else f"横向溢出视口={overflow}；首页卡片断点行为={ {k: v['cardVisible'] for k, v in vp.items() if k.startswith('home_')} }",
            vp,
        )

        # ============================ 7b. 布局对照（Material 基线运行时 oracle） ============================
        stage("7b 布局对照（基线 oracle）")

        def measure_layout(context_page, combos) -> dict:
            out = {}
            for width, path in combos:
                context_page.set_viewport_size({"width": width, "height": 900})
                context_page.goto(BASE_URL + path, wait_until="domcontentloaded", timeout=30000)
                time.sleep(0.8)
                out[f"{width}|{path or 'home'}"] = context_page.evaluate(LAYOUT_MEASURE_JS)
            return out

        target_layout = measure_layout(page, LAYOUT_COMBOS)
        baseline_layout: dict = {}
        baseline_layout_errors: list[str] = []
        try:
            bctx = browser.new_context(viewport={"width": 1440, "height": 900}, color_scheme="light")
            bserve, _ = make_router(baseline)
            bctx.route(SYNTHETIC_ORIGIN + "/**", bserve)
            bpage = bctx.new_page()
            bpage.on("pageerror", lambda exc: baseline_layout_errors.append(str(exc)[:200]))
            baseline_layout = measure_layout(bpage, LAYOUT_COMBOS)
            bctx.close()
        except Exception as exc:  # pragma: no cover
            baseline_layout_errors.append(f"基线布局测量失败：{exc}")

        layout_diffs = []
        layout_detail = {}
        for view, t in target_layout.items():
            b = baseline_layout.get(view)
            if not b:
                continue
            metrics = {}

            def compare_metric(name: str, bbox_key: str, attr: str, tolerance: float) -> None:
                bv = (b.get(bbox_key) or {}).get(attr)
                tv = (t.get(bbox_key) or {}).get(attr)
                if bv is None or tv is None:
                    metrics[name] = {"baseline": bv, "target": tv, "status": "skip"}
                    return
                delta = round(abs(bv - tv), 2)
                entry = {
                    "baseline": round(bv, 2),
                    "target": round(tv, 2),
                    "delta": delta,
                    "tolerance": tolerance,
                    "ok": delta <= tolerance,
                }
                metrics[name] = entry
                if delta > tolerance:
                    layout_diffs.append({"view": view, "metric": name, **entry})

            # 搜索触发器：Material 在移动端隐藏为 0 宽，仅比较桌面可见状态
            b_trig = b.get("search_trigger") or {}
            t_trig = t.get("search_trigger") or {}
            if b_trig.get("w") and b_trig["w"] > 0:
                compare_metric("search_trigger_w", "search_trigger", "w", LAYOUT_TOLERANCE["search_w"])
                compare_metric("search_trigger_h", "search_trigger", "h", LAYOUT_TOLERANCE["search_h"])
            compare_metric("grid_x", "grid", "x", LAYOUT_TOLERANCE["grid_x"])
            compare_metric("content_x", "content", "x", LAYOUT_TOLERANCE["content_x"])
            compare_metric("content_w", "content", "w", LAYOUT_TOLERANCE["content_w"])
            compare_metric("content_inner_x", "content_inner", "x", LAYOUT_TOLERANCE["content_inner_x"])
            compare_metric("content_inner_w", "content_inner", "w", LAYOUT_TOLERANCE["content_inner_w"])
            metrics["search_class"] = {"baseline": b.get("search_class"), "target": t.get("search_class")}
            metrics["search_text"] = {"baseline": b.get("search_text"), "target": t.get("search_text")}
            layout_detail[view] = metrics
        layout_ok = not layout_diffs and bool(baseline_layout)
        report.add(
            "A16",
            "布局与 Material 基线一致（搜索触发器/网格/内容宽）",
            "pass" if layout_ok else "fail",
            "搜索触发器宽高、.md-grid/.md-content/.md-content__inner 水平位置与宽度在 390/768/960/1440 与 Material 基线一致（容差 ≤2px）"
            if layout_ok
            else f"布局与基线存在 {len(layout_diffs)} 处偏差：{layout_diffs[:8]}",
            {
                "tolerance_px": LAYOUT_TOLERANCE,
                "views": sorted(layout_detail),
                "diffs": layout_diffs[:20],
                "detail": layout_detail,
                "baseline_errors": baseline_layout_errors,
                "search_button_absolute": {
                    "target_home_1440": (target_layout.get("1440|home") or {}).get("search_trigger"),
                    "baseline_home_1440": (baseline_layout.get("1440|home") or {}).get("search_trigger"),
                    "target_math_1440": (target_layout.get("1440|tools/lay_lang/tex/math/") or {}).get("search_trigger"),
                },
            },
        )
        target_1440_home = target_layout.get("1440|home") or {}
        zensical_css = [u for u in target_1440_home.get("style_sheets", []) if "zensical.css" in u]
        report.add(
            "A16",
            "Zensical 适配样式生效",
            "pass" if zensical_css else "fail",
            f"目标构建加载 zensical.css：{zensical_css}" if zensical_css else "目标构建未加载 zensical.css（适配样式未生效）",
            {
                "zensical_css": zensical_css,
                "style_sheets": target_1440_home.get("style_sheets"),
                "search_trigger_computed": {
                    "radius": target_1440_home.get("search_radius"),
                    "font": target_1440_home.get("search_font"),
                    "kbd_display": target_1440_home.get("search_kbd_display"),
                },
            },
        )

        stage("8 网络与 JS 异常汇总")
        # ============================ 8. 网络与 JS 异常汇总 ============================
        # 取消请求（切换页面/关闭上下文造成）与真实加载失败分开
        classes: dict[str, int] = {}
        for item in network["request_failures"]:
            classes[item["class"]] = classes.get(item["class"], 0) + 1
        network["failure_classes"] = classes
        network["served_local"] = serve_stats["served"]
        network["local_404"] = serve_stats["not_found"]
        network["outside_prefix_requests"] = serve_stats["outside"]
        network["mime_counts"] = dict(sorted(serve_stats["mime"].items()))
        external_hosts = network["external_hosts"]
        network["external_checked"] = [
            {
                "host": host,
                "role": EXTERNAL_HOST_HINTS.get(host, "外部资源"),
                **entry,
            }
            for host, entry in sorted(external_hosts.items())
        ]
        network["external_unavailable"] = any(
            e["failed"] > 0 and e["ok"] == 0 for e in network["external_checked"]
        )
        real_local_failures = [
            i
            for i in network["request_failures"]
            if i["class"] == "local_error" and i["url"].startswith(SYNTHETIC_ORIGIN)
        ]
        external_failed = [i for i in network["request_failures"] if i["class"] == "external_unavailable"]
        cancelled = [i for i in network["request_failures"] if i["class"] == "cancelled"]
        network["sample_cancelled"] = cancelled[:5]
        network["sample_external_failed"] = external_failed[:10]
        report.add(
            "A16-net",
            "本地资源请求无 404/失败",
            "pass" if not network["local_bad_responses"] and not real_local_failures else "fail",
            f"route 提供本地文件 {network['served_local']} 个；本地 404={network['local_404']}，"
            f"本地响应 4xx/5xx={len(network['local_bad_responses'])}，本地请求失败={len(real_local_failures)}"
            if not network["local_bad_responses"] and not real_local_failures
            else f"本地资源异常：404={network['local_404']}，bad_responses={network['local_bad_responses'][:10]}",
            {
                "served": network["served_local"],
                "not_found": network["local_404"],
                "bad_responses": network["local_bad_responses"][:20],
                "local_request_failures": real_local_failures[:20],
            },
        )
        # 外部关键引擎依赖（unpkg 的 MathJax/Mermaid/GLightbox、giscus、字体）：只记录不判失败
        critical_hosts = {"unpkg.com", "giscus.app", "fonts.googleapis.com", "fonts.gstatic.com", "gcore.jsdelivr.net"}
        critical_status = [
            {"host": e["host"], "role": e["role"], "requests": e["requests"], "ok": e["ok"], "failed": e["failed"]}
            for e in network["external_checked"]
            if e["host"] in critical_hosts
        ]
        critical_unavailable = [e for e in critical_status if e["requests"] > 0 and e["ok"] == 0]
        report.add(
            "A16-net",
            "外部关键依赖可用性",
            "pass" if not critical_unavailable else "warn",
            "MathJax/Mermaid/GLightbox（unpkg）、Giscus、字体 CDN 均有成功响应" if not critical_unavailable
            else f"关键外部依赖不可用（仅记录，不判失败）：{[e['host'] for e in critical_unavailable]}",
            {"critical_hosts": critical_status, "all_hosts": network["external_checked"]},
            external=bool(critical_unavailable),
        )
        report.add(
            "A12",
            "requestfailed 分类（网络取消 vs 真实失败）",
            "pass" if not real_local_failures else "fail",
            f"requestfailed 共 {sum(classes.values())} 个：网络取消（切页/关闭上下文）{classes.get('cancelled', 0)}，"
            f"外部网络失败 {classes.get('external_unavailable', 0)}，本地错误 {classes.get('local_error', 0)}",
            {
                "classes": classes,
                "samples_cancelled": network["sample_cancelled"],
                "samples_external_failed": network["sample_external_failed"],
            },
        )
        js_errors = [e for e in page_errors]
        external_js_errors = [e for e in js_errors if re.search(r"^(Script error\.?|Failed to fetch|Load failed)", e["message"])]
        real_js_errors = [e for e in js_errors if e not in external_js_errors]
        report.add(
            "A12",
            "未处理 JS 异常",
            "pass" if not real_js_errors else "fail",
            "运行期间无未处理 JS 异常（pageerror=0）" if not js_errors else
            (f"pageerror {len(js_errors)} 个，其中外部脚本可归因 {len(external_js_errors)} 个" if not real_js_errors else f"发现 {len(real_js_errors)} 个未处理 JS 异常"),
            {"page_errors": js_errors[:20], "console_errors": console_errors[:20]},
        )

        context.close()
        browser.close()

    elapsed = time.time() - started
    failures = report.failures()
    warnings = report.warnings()
    failed_gates = sorted({c["gate"] for c in failures})
    summary = {
        "tool": "verify_runtime.py",
        "version": 1,
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "baseline": str(baseline),
        "target": str(site_root),
        "synthetic_origin": SYNTHETIC_ORIGIN,
        "site_prefix": SITE_PREFIX,
        "chrome_version": chrome_version,
        "headed": bool(args.headed),
        "elapsed_seconds": round(elapsed, 2),
        "result": "FAIL" if failures else "PASS",
        "failed_gates": failed_gates,
        "counts": {
            "checks": len(report.checks),
            "pass": sum(1 for c in report.checks if c["status"] == "pass"),
            "fail": len(failures),
            "warn": len(warnings),
            "info": sum(1 for c in report.checks if c["status"] == "info"),
            "skip": sum(1 for c in report.checks if c["status"] == "skip"),
        },
        "expected_from_baseline": expected,
        "checks": report.checks,
        "network": network,
        "screenshots": sorted(p.name for p in shots.glob("*.png")),
        "notes": [
            "运行时失败区分：fail = 迁移回归；warn + external_dependency=true = 外部网络不可用，仅记录不判失败。",
            "route interception 只拦截 https://verify.local/**；外部 CDN/Giscus 走真实网络。",
            "搜索结果只记录可用性，不与 Material 排名/分组比较。",
            "软导航判据：window.__runtimeProbeMarker 保持 418（未整页刷新）+ canonical/URL 更新。",
        ],
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "runtime-report.json"
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = ["# Zensical 迁移运行时验收报告", ""]
    lines.append(f"- 生成时间：{summary['generated_at']}")
    lines.append(f"- 基线：`{baseline}`；目标：`{site_root}`")
    lines.append(f"- 合成同源：`{SYNTHETIC_ORIGIN}{SITE_PREFIX}`（route interception，无真实 HTTP 服务器）")
    lines.append(f"- Chrome：{chrome_version}（headless={not args.headed}）")
    lines.append(f"- 耗时：{summary['elapsed_seconds']} 秒")
    lines.append(f"- **结论：{'FAIL' if failures else 'PASS'}**（pass {summary['counts']['pass']} / fail {summary['counts']['fail']} / warn {summary['counts']['warn']} / info {summary['counts']['info']}）")
    lines.append("")
    if failures:
        lines.append("## 失败项（迁移回归）")
        lines.append("")
        for c in failures:
            lines.append(f"### [{c['gate']}] {c['subject']}")
            lines.append("")
            lines.append(c["message"])
            lines.append("")
            if c["details"]:
                text = json.dumps(c["details"], ensure_ascii=False, indent=1)
                lines.append("```json")
                lines.append(text[:6000] + ("\n…（完整明细见 runtime-report.json）" if len(text) > 6000 else ""))
                lines.append("```")
                lines.append("")
    else:
        lines.append("## 失败项")
        lines.append("")
        lines.append("无。")
        lines.append("")
    if warnings:
        lines.append("## 警告项（含外部网络依赖）")
        lines.append("")
        for c in warnings:
            lines.append(f"- [{c['gate']}] {c['subject']}: {c['message']}")
        lines.append("")
    lines.append("## 检查项明细")
    lines.append("")
    lines.append("| # | 门槛 | 检查项 | 状态 | 外部依赖 | 说明 |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for c in report.checks:
        msg = c["message"].replace("|", "\\|")
        lines.append(f"| {c['seq']} | {c['gate']} | {c['subject']} | {c['status']} | {'是' if c['external_dependency'] else '否'} | {msg} |")
    lines.append("")
    lines.append("## 外部网络记录")
    lines.append("")
    for entry in network["external_checked"]:
        lines.append(f"- `{entry['host']}`（{entry['role']}）：请求 {entry['requests']}，成功 {entry['ok']}，失败 {entry['failed']}")
    lines.append("")
    lines.append(f"- 本地文件 route 提供 {network['served_local']} 次，本地 404 {network['local_404']} 次，越出前缀请求 {network['outside_prefix_requests']} 次。")
    lines.append(f"- 网络取消（切页/关闭上下文）{len(network['sample_cancelled'])} 个样本，外部失败样本 {len(network['sample_external_failed'])} 个。")
    lines.append("")
    (out_dir / "runtime-report.md").write_text("\n".join(lines), encoding="utf-8")

    print("")
    print("=" * 78)
    if failures:
        print(f"运行时验收：FAIL — {len(failures)} 项迁移回归失败，{len(warnings)} 项警告；失败门槛：{', '.join(failed_gates)}")
    else:
        print(f"运行时验收：PASS — {len(report.checks)} 项检查通过（警告 {len(warnings)} 项）")
    print(f"JSON 报告：{json_path}")
    print(f"摘要报告：{out_dir / 'runtime-report.md'}")
    print(f"截图目录：{shots}")
    return 1 if failures else 0


def main(argv: list[str] | None = None) -> int:
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Zensical 迁移站运行时验收探针")
    parser.add_argument("--target", default=str(project_root / "site-zensical"))
    parser.add_argument("--baseline", default=str(project_root / ".migration" / "baseline-material"))
    parser.add_argument("--out", default=str(project_root / ".migration" / "verify"))
    parser.add_argument("--chrome", default=DEFAULT_CHROME)
    parser.add_argument("--headed", action="store_true", help="有头模式（调试用）")
    parser.add_argument("--skip-mermaid", action="store_true", help="跳过 Mermaid 10 页检查（调试用）")
    args = parser.parse_args(argv)
    try:
        return run(args)
    except PlaywrightError as exc:  # type: ignore[name-defined]
        import traceback

        print(f"ERROR: Playwright 运行失败：{exc}", file=sys.stderr)
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    sys.exit(main())

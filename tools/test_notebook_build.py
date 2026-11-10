#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""``tools/notebook_build.py`` 的回归测试（标准库 unittest，无第三方测试框架）。

覆盖 2026-11-10 复审提出的两个 P2 逻辑问题：

1. 同一进程内多次 ``prepare`` 时，Git 时间缓存必须刷新（``serve`` 长时间运行场景）；
2. front matter 需兼容 MkDocs 的合法结束标记 ``...``，且 YAML 解析失败时必须保留原文。

测试会在临时目录中复制构建脚本与目录模板，初始化独立 Git 仓库，不触碰真实仓库内容。

运行：``python tools/test_notebook_build.py``
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOL_PATH = REPO_ROOT / "tools" / "notebook_build.py"
TOC_TEMPLATE = REPO_ROOT / "hooks" / "templates" / "toc.html"

DATE_1 = "2026-01-02T03:04:05+08:00"
DATE_2 = "2026-06-07T08:09:10+08:00"


def _timestamp(iso_date: str) -> int:
    return int(datetime.fromisoformat(iso_date).timestamp())


class PrepareFixture:
    """最小可运行的笔记站项目夹具（独立 Git 仓库）。"""

    def __init__(self, root: Path) -> None:
        self.root = root
        (root / "docs").mkdir()
        (root / "hooks" / "templates").mkdir(parents=True)
        (root / "includes").mkdir()
        (root / "tools").mkdir()
        shutil.copyfile(TOOL_PATH, root / "tools" / "notebook_build.py")
        shutil.copyfile(TOC_TEMPLATE, root / "hooks" / "templates" / "toc.html")
        (root / "includes" / "abbreviations.md").write_text("", encoding="utf-8")
        (root / "mkdocs.zensical.yml").write_text(
            "INHERIT: mkdocs.yml\n", encoding="utf-8"
        )
        self._git("init")
        self._git("config", "user.name", "Test")
        self._git("config", "user.email", "test@example.com")

    # -- Git 辅助 ---------------------------------------------------------
    def _git(self, *args: str, env: dict | None = None) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", *args],
            cwd=self.root,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
        )

    def commit(self, message: str, iso_date: str) -> str:
        env = os.environ.copy()
        env["GIT_AUTHOR_DATE"] = iso_date
        env["GIT_COMMITTER_DATE"] = iso_date
        self._git("add", "-A")
        self._git(
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.com",
            "commit",
            "-m",
            message,
            env=env,
        )
        return self._git("rev-parse", "HEAD").stdout.strip()

    # -- 文件 / 模块辅助 ---------------------------------------------------
    def write(self, rel_path: str, text: str) -> Path:
        path = self.root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def load_build_module(self, name: str):
        """从夹具内复制出的脚本加载模块，使模块级 ROOT 指向夹具目录。"""
        spec = importlib.util.spec_from_file_location(
            name, self.root / "tools" / "notebook_build.py"
        )
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def staged_text(self, rel_path: str) -> str:
        return (self.root / ".migration" / "docs" / rel_path).read_text(
            encoding="utf-8"
        )


class FrontMatterCompatibilityTest(unittest.TestCase):
    """P2-2：合法 ``...`` 结束标记与解析失败原文保留。"""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.fixture = PrepareFixture(Path(self.tmp.name))
        self.addCleanup(self.tmp.cleanup)

    def test_dot_terminated_front_matter_is_parsed_and_normalized(self) -> None:
        source = (
            "---\n"
            "title: YAML end marker\n"
            "comments: true\n"
            "hide:\n"
            "  - toc\n"
            "...\n"
            "# Probe\n"
            "\n"
            "Preserve metadata.\n"
        )
        self.fixture.write("docs/dots.md", source)
        self.fixture.commit("dots", DATE_1)
        module = self.fixture.load_build_module("nb_dot_marker")
        module.prepare()

        staged = self.fixture.staged_text("dots.md")
        meta, body, ok = module.split_front_matter(staged)
        self.assertTrue(ok)
        self.assertEqual(meta["title"], "YAML end marker")
        self.assertIs(meta["comments"], True)
        self.assertEqual(meta["hide"], ["toc"])
        self.assertIn("git_revision_date_localized", meta)
        # 解析后统一用 --- 结束（Zensical 0.1.0 兼容层只识别 ---）
        self.assertTrue(staged.startswith("---\n"))
        self.assertNotIn("\n...\n", staged)
        self.assertIn("git_revision_date_localized", staged)
        # comments: true 的页面统计仍应插入
        self.assertIn("margin-top: -30px", body)

    def test_invalid_yaml_front_matter_is_preserved(self) -> None:
        source = "---\ncomments: [invalid\n---\n# Visible body\n"
        self.fixture.write("docs/bad.md", source)
        self.fixture.commit("bad", DATE_1)
        module = self.fixture.load_build_module("nb_invalid_yaml")
        module.prepare()

        self.assertEqual(self.fixture.staged_text("bad.md"), source)

    def test_no_front_matter_gets_generated_dates(self) -> None:
        self.fixture.write("docs/plain.md", "# Plain\n\nbody\n")
        self.fixture.commit("plain", DATE_1)
        module = self.fixture.load_build_module("nb_plain")
        module.prepare()

        meta, _body, ok = module.split_front_matter(
            self.fixture.staged_text("plain.md")
        )
        self.assertTrue(ok)
        self.assertIn("git_revision_date_localized", meta)
        self.assertIn("git_creation_date_localized", meta)


class PrepareCacheRefreshTest(unittest.TestCase):
    """P2-1：同一进程两次提交 + 两次 prepare，日期与目录 data-ts 必须刷新。"""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.fixture = PrepareFixture(Path(self.tmp.name))
        self.addCleanup(self.tmp.cleanup)

    def test_dates_and_toc_timestamps_refresh_after_new_commit(self) -> None:
        self.fixture.write("docs/a.md", "# A\n\nfirst body\n")
        self.fixture.write(
            "docs/sec/index.md",
            "# 分区\n\n"
            "{{ BEGIN_TOC }}\n"
            "- 分区:\n"
            "    - 子页: child/\n"
            "{{ END_TOC }}\n",
        )
        self.fixture.write("docs/sec/child/index.md", "# 子页\n\ncontent\n")
        self.fixture.commit("first", DATE_1)

        module = self.fixture.load_build_module("nb_cache_refresh")
        module.prepare()

        expected_first = module.format_git_datetime(_timestamp(DATE_1))
        first_meta, _b, _ok = module.split_front_matter(
            self.fixture.staged_text("a.md")
        )
        first_toc = self.fixture.staged_text("sec/index.md")
        self.assertEqual(first_meta["git_revision_date_localized"], expected_first)
        self.assertIn(f'data-ts="{_timestamp(DATE_1)}"', first_toc)
        # 首次 prepare 后缓存应已有内容（证明下面第二次 prepare 若不刷新会读到旧值）
        self.assertTrue(module._GIT_TIMESTAMP_CACHE)
        self.assertTrue(module._TOC_TIME_CACHE)

        # 第二次提交：改动正文与子页，作者时间使用 DATE_2
        self.fixture.write("docs/a.md", "# A\n\nsecond body\n")
        self.fixture.write("docs/sec/child/index.md", "# 子页\n\nupdated\n")
        self.fixture.commit("second", DATE_2)

        module.prepare()

        expected_second = module.format_git_datetime(_timestamp(DATE_2))
        second_meta, _b, _ok = module.split_front_matter(
            self.fixture.staged_text("a.md")
        )
        second_toc = self.fixture.staged_text("sec/index.md")
        self.assertIn("second body", self.fixture.staged_text("a.md"))
        self.assertEqual(
            second_meta["git_revision_date_localized"], expected_second
        )
        self.assertIn(f'data-ts="{_timestamp(DATE_2)}"', second_toc)
        self.assertNotIn(f'data-ts="{_timestamp(DATE_1)}"', second_toc)

    def test_snapshot_includes_git_head(self) -> None:
        self.fixture.write("docs/a.md", "# A\n")
        head = self.fixture.commit("first", DATE_1)
        module = self.fixture.load_build_module("nb_snapshot")
        snapshot = module._snapshot_sources()
        self.assertEqual(snapshot["__git_head__"], head)


if __name__ == "__main__":
    unittest.main(verbosity=2)

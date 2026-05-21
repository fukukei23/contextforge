"""ContextForge スコアリング・選択・出力テスト"""
import pytest
from pathlib import Path
from unittest.mock import MagicMock
from contextforge import (
    FileItem, score_files, select_files, create_report_md,
    create_combined_code, collect_and_score_files,
    LogSink, BASE_COMPRESSION_RATIOS,
)
from collections import defaultdict


def _make_log(tmp_path):
    return LogSink(tmp_path, dry_run=True)


class TestScoreFiles:

    def test_python_file_scores_higher(self, tmp_path):
        log = _make_log(tmp_path)
        root = tmp_path
        py_item = FileItem(
            path=tmp_path / "main.py", root=root,
            rel_path=Path("main.py"), size_bytes=100, loc=50, entropy=4.5,
        )
        txt_item = FileItem(
            path=tmp_path / "readme.txt", root=root,
            rel_path=Path("readme.txt"), size_bytes=100, loc=50, entropy=4.5,
        )
        (tmp_path / "main.py").write_text("x = 1")
        score_files([py_item, txt_item], log)
        assert py_item.score > txt_item.score

    def test_name_weight_orchestrator(self, tmp_path):
        log = _make_log(tmp_path)
        root = tmp_path
        item = FileItem(
            path=tmp_path / "orchestrator.py", root=root,
            rel_path=Path("orchestrator.py"), size_bytes=50, loc=10, entropy=4.0,
        )
        (tmp_path / "orchestrator.py").write_text("x = 1")
        score_files([item], log)
        assert item.score >= 10  # orchestrator=10 + .py=3

    def test_loc_contributes_to_score(self, tmp_path):
        log = _make_log(tmp_path)
        root = tmp_path
        big = FileItem(
            path=tmp_path / "big.py", root=root,
            rel_path=Path("big.py"), size_bytes=5000, loc=200, entropy=4.5,
        )
        small = FileItem(
            path=tmp_path / "small.py", root=root,
            rel_path=Path("small.py"), size_bytes=100, loc=5, entropy=4.5,
        )
        (tmp_path / "big.py").write_text("x = 1\n" * 200)
        (tmp_path / "small.py").write_text("x = 1")
        score_files([big, small], log)
        assert big.score > small.score


class TestCollectAndScoreFiles:

    def test_collects_python_files(self, tmp_path):
        log = _make_log(tmp_path)
        (tmp_path / "app.py").write_text("print('hello')")
        (tmp_path / "utils.py").write_text("def helper(): pass")
        exclude = {"dirs": [], "files": []}
        items = collect_and_score_files(tmp_path, exclude, log)
        paths = [item.rel_path for item in items]
        assert Path("app.py") in paths
        assert Path("utils.py") in paths

    def test_excludes_pyc_files(self, tmp_path):
        log = _make_log(tmp_path)
        (tmp_path / "good.py").write_text("x = 1")
        (tmp_path / "bad.pyc").write_text("compiled")
        exclude = {"dirs": ["**/__pycache__"], "files": ["*.pyc"]}
        items = collect_and_score_files(tmp_path, exclude, log)
        exts = {item.path.suffix for item in items}
        assert ".pyc" not in exts

    def test_excludes_directories(self, tmp_path):
        log = _make_log(tmp_path)
        (tmp_path / "src" / "main.py").parent.mkdir()
        (tmp_path / "src" / "main.py").write_text("x = 1")
        (tmp_path / "__pycache__" / "cache.pyc").parent.mkdir()
        (tmp_path / "__pycache__" / "cache.pyc").write_text("compiled")
        exclude = {"dirs": ["**/__pycache__"], "files": []}
        items = collect_and_score_files(tmp_path, exclude, log)
        paths = [str(item.rel_path) for item in items]
        assert any("src" in p for p in paths)
        assert not any("__pycache__" in p for p in paths)

    def test_diagnose_mode(self, tmp_path):
        log = _make_log(tmp_path)
        (tmp_path / "app.py").write_text("x = 1")
        exclude = {"dirs": [], "files": []}
        diagnose = {}
        items = collect_and_score_files(tmp_path, exclude, log, diagnose=diagnose)
        assert "walk_total_dirs" in diagnose
        assert "walk_total_files" in diagnose
        assert diagnose["walk_total_files"] >= 1

    def test_empty_directory(self, tmp_path):
        log = _make_log(tmp_path)
        exclude = {"dirs": [], "files": []}
        items = collect_and_score_files(tmp_path, exclude, log)
        assert items == []

    def test_sorted_by_score_descending(self, tmp_path):
        log = _make_log(tmp_path)
        (tmp_path / "orchestrator.py").write_text("x = 1\n" * 50)
        (tmp_path / "misc.txt").write_text("hello")
        exclude = {"dirs": [], "files": []}
        items = collect_and_score_files(tmp_path, exclude, log)
        if len(items) >= 2:
            assert items[0].score >= items[1].score


class TestSelectFiles:

    def test_selects_within_budget(self, tmp_path):
        root = tmp_path
        items = [
            FileItem(path=tmp_path / "a.py", root=root, rel_path=Path("a.py"),
                     size_bytes=1000, loc=10, entropy=4.5),
            FileItem(path=tmp_path / "b.py", root=root, rel_path=Path("b.py"),
                     size_bytes=2000, loc=20, entropy=4.5),
        ]
        profile = {"target_mb": 1, "max_single_mb": 1, "selection_mode": "raw"}
        ratios = defaultdict(lambda: 0.5, {".py": 0.3})
        picked, heavy = select_files(items, profile, ratios)
        assert len(picked) == 2

    def test_exceeds_max_single_size(self, tmp_path):
        root = tmp_path
        items = [
            FileItem(path=tmp_path / "huge.py", root=root, rel_path=Path("huge.py"),
                     size_bytes=100 * 1024 * 1024, loc=1000, entropy=4.5),
        ]
        profile = {"target_mb": 1, "max_single_mb": 0.5, "selection_mode": "raw"}
        ratios = defaultdict(lambda: 0.5)
        picked, heavy = select_files(items, profile, ratios)
        assert len(picked) == 0
        assert len(heavy) == 1

    def test_priority_files_selected_first(self, tmp_path):
        root = tmp_path
        items = [
            FileItem(path=tmp_path / "low.py", root=root, rel_path=Path("low.py"),
                     size_bytes=100, loc=5, entropy=4.5, score=1.0),
            FileItem(path=tmp_path / "high.py", root=root, rel_path=Path("high.py"),
                     size_bytes=100, loc=5, entropy=4.5, score=10.0),
        ]
        profile = {
            "target_mb": 1, "max_single_mb": 1, "selection_mode": "raw",
            "priority_files": ["high.py"],
        }
        ratios = defaultdict(lambda: 0.5)
        picked, _ = select_files(items, profile, ratios)
        if len(picked) >= 2:
            assert picked[0].rel_path == Path("high.py")

    def test_compressed_mode_uses_ratio(self, tmp_path):
        root = tmp_path
        items = [
            FileItem(path=tmp_path / "a.py", root=root, rel_path=Path("a.py"),
                     size_bytes=500_000, loc=100, entropy=4.5),
        ]
        profile = {"target_mb": 1, "max_single_mb": 1, "selection_mode": "compressed"}
        ratios = defaultdict(lambda: 0.5, {".py": 0.3})
        picked, heavy = select_files(items, profile, ratios)
        assert len(picked) == 1


class TestCreateReportMd:

    def test_basic_report(self, tmp_path):
        items = [
            FileItem(path=tmp_path / "a.py", root=tmp_path, rel_path=Path("a.py"),
                     size_bytes=100, loc=10, entropy=4.5),
            FileItem(path=tmp_path / "b.md", root=tmp_path, rel_path=Path("b.md"),
                     size_bytes=200, loc=20, entropy=3.0),
        ]
        report = create_report_md(items, "test-profile", 1000.0, None)
        assert "パッケージ品質レポート" in report
        assert "a.py" not in report  # stats by ext, not filename
        assert ".py" in report
        assert ".md" in report

    def test_report_with_heavy_files(self, tmp_path):
        items = [
            FileItem(path=tmp_path / "a.py", root=tmp_path, rel_path=Path("a.py"),
                     size_bytes=100, loc=10, entropy=4.5),
        ]
        heavy = [(5.5, Path("big_file.bin"))]
        report = create_report_md(items, "test-profile", 1000.0, None, heavy)
        assert "除外された大容量ファイル" in report
        assert "big_file.bin" in report

    def test_report_with_actual_zip(self, tmp_path):
        items = [
            FileItem(path=tmp_path / "a.py", root=tmp_path, rel_path=Path("a.py"),
                     size_bytes=1000, loc=10, entropy=4.5),
        ]
        report = create_report_md(items, "test-profile", 300.0, 0.5)
        assert "情報密度" in report
        assert "予測精度" in report

    def test_purity_warning_low(self, tmp_path):
        items = [
            FileItem(path=tmp_path / "data.bin", root=tmp_path, rel_path=Path("data.bin"),
                     size_bytes=100, loc=0, entropy=0.0),
        ]
        report = create_report_md(items, "test-profile", 1000.0, None)
        assert "警告" in report


class TestCreateCombinedCode:

    def test_combines_files(self, tmp_path):
        log = _make_log(tmp_path)
        (tmp_path / "a.py").write_text("x = 1")
        (tmp_path / "b.py").write_text("y = 2")
        items = [
            FileItem(path=tmp_path / "a.py", root=tmp_path, rel_path=Path("a.py"),
                     size_bytes=5, loc=1, entropy=4.5),
            FileItem(path=tmp_path / "b.py", root=tmp_path, rel_path=Path("b.py"),
                     size_bytes=5, loc=1, entropy=4.5),
        ]
        code = create_combined_code(items, log)
        assert "x = 1" in code
        assert "y = 2" in code
        assert "START OF: a.py" in code
        assert "END OF: b.py" in code

    def test_empty_items(self, tmp_path):
        log = _make_log(tmp_path)
        code = create_combined_code([], log)
        assert "COMBINED SOURCE CODE (0 files)" in code

    def test_handles_unreadable_file(self, tmp_path):
        log = _make_log(tmp_path)
        nonexistent = tmp_path / "missing.py"
        items = [
            FileItem(path=nonexistent, root=tmp_path, rel_path=Path("missing.py"),
                     size_bytes=0, loc=0, entropy=0.0),
        ]
        code = create_combined_code(items, log)
        assert "ERROR" in code

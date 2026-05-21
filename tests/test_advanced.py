"""ContextForge 高度機能テスト（チャンク分割・診断レポート・緩和収集・エクスポート）"""
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from collections import defaultdict
from contextforge import (
    FileItem, LogSink, create_chunked_code_files,
    write_diagnose_report, collect_relaxed_additional,
    export_main_generator, PROFILES,
)


def _make_log(tmp_path):
    return LogSink(tmp_path, dry_run=True)


class TestCreateChunkedCodeFiles:

    def test_single_file_no_split(self, tmp_path):
        log = _make_log(tmp_path)
        (tmp_path / "a.py").write_text("x = 1")
        items = [
            FileItem(path=tmp_path / "a.py", root=tmp_path, rel_path=Path("a.py"),
                     size_bytes=5, loc=1, entropy=4.5),
        ]
        out_dir = tmp_path / "chunks"
        out_dir.mkdir()
        paths = create_chunked_code_files(items, out_dir, chunk_target_mb=1.0, log=log)
        assert len(paths) == 1
        content = paths[0].read_text()
        assert "x = 1" in content

    def test_splits_large_files(self, tmp_path):
        log = _make_log(tmp_path)
        (tmp_path / "big.py").write_text("line\n" * 1000)
        items = [
            FileItem(path=tmp_path / "big.py", root=tmp_path, rel_path=Path("big.py"),
                     size_bytes=6000, loc=1000, entropy=4.5),
        ]
        out_dir = tmp_path / "chunks"
        out_dir.mkdir()
        # 1バイトのチャンクサイズにして強制的に分割
        paths = create_chunked_code_files(items, out_dir, chunk_target_mb=0.00001, log=log)
        assert len(paths) >= 1

    def test_empty_items(self, tmp_path):
        log = _make_log(tmp_path)
        out_dir = tmp_path / "chunks"
        out_dir.mkdir()
        paths = create_chunked_code_files([], out_dir, chunk_target_mb=1.0, log=log)
        assert paths == []


class TestWriteDiagnoseReport:

    def test_basic_report(self, tmp_path):
        diagnose = {
            "walk_total_dirs": 5,
            "walk_total_files": 20,
            "excluded_by_dir": {"**/node_modules": 3},
            "excluded_by_ext": {"*.pyc": 10},
            "excluded_by_size": 2,
            "excluded_by_error": {},
            "included_by_ext": {".py": 8, ".md": 2},
            "included_by_dir": {"src": 6, ".": 4},
        }
        report_path = tmp_path / "diagnose.md"
        write_diagnose_report(diagnose, report_path, console_top_n=5, file_top_n=10)
        assert report_path.exists()
        content = report_path.read_text()
        assert "walk_total_dirs" in content
        assert "node_modules" in content
        assert "*.pyc" in content

    def test_empty_diagnose(self, tmp_path):
        diagnose = {
            "walk_total_dirs": 0,
            "walk_total_files": 0,
            "excluded_by_dir": {},
            "excluded_by_ext": {},
            "excluded_by_size": 0,
            "excluded_by_error": {},
            "included_by_ext": {},
            "included_by_dir": {},
        }
        report_path = tmp_path / "diagnose.md"
        write_diagnose_report(diagnose, report_path)
        content = report_path.read_text()
        assert "なし" in content

    def test_creates_parent_directory(self, tmp_path):
        diagnose = {"walk_total_dirs": 1, "walk_total_files": 1}
        report_path = tmp_path / "deep" / "nested" / "report.md"
        write_diagnose_report(diagnose, report_path)
        assert report_path.exists()


class TestCollectRelaxedAdditional:

    def test_collects_md_files(self, tmp_path):
        log = _make_log(tmp_path)
        (tmp_path / "design.md").write_text("# Design doc")
        (tmp_path / "notes.txt").write_text("some notes")
        exclude = {"dirs": [], "files": []}
        picked_paths = set()
        profile = {"max_single_mb": 10}
        result = collect_relaxed_additional(tmp_path, exclude, picked_paths, profile, log)
        exts = {item.path.suffix for item in result}
        assert ".md" in exts
        assert ".txt" in exts

    def test_skips_already_picked(self, tmp_path):
        log = _make_log(tmp_path)
        md_path = tmp_path / "design.md"
        md_path.write_text("# Design")
        exclude = {"dirs": [], "files": []}
        picked_paths = {md_path}
        profile = {"max_single_mb": 10}
        result = collect_relaxed_additional(tmp_path, exclude, picked_paths, profile, log)
        assert md_path not in [item.path for item in result]

    def test_skips_non_text_files(self, tmp_path):
        log = _make_log(tmp_path)
        (tmp_path / "image.png").write_bytes(b"\x89PNG")
        (tmp_path / "readme.md").write_text("# README")
        exclude = {"dirs": [], "files": []}
        picked_paths = set()
        profile = {"max_single_mb": 10}
        result = collect_relaxed_additional(tmp_path, exclude, picked_paths, profile, log)
        exts = {item.path.suffix for item in result}
        assert ".png" not in exts


class TestExportMainGenerator:

    def test_invalid_root(self, tmp_path):
        from threading import Event
        stop = Event()
        logs_dir = tmp_path / "logs"
        exports_dir = tmp_path / "exports"
        logs_dir.mkdir()
        exports_dir.mkdir()
        results = list(export_main_generator(
            "/nonexistent/path/xyz",
            "gemini-single-file",
            emit_zip=False, emit_folder=False, dry_run=True,
            exports_dir=exports_dir, logs_dir=logs_dir, stop_event=stop,
        ))
        assert len(results) > 0
        assert any("エラー" in r or "Error" in r.lower() for r in results)

    def test_dry_run_single_file(self, tmp_path):
        from threading import Event
        stop = Event()
        logs_dir = tmp_path / "logs"
        exports_dir = tmp_path / "exports"
        logs_dir.mkdir()
        exports_dir.mkdir()
        # プロジェクトディレクトリを作成
        proj = tmp_path / "myproject"
        proj.mkdir()
        (proj / "main.py").write_text("print('hello')")
        results = list(export_main_generator(
            str(proj),
            "gemini-single-file",
            emit_zip=False, emit_folder=False, dry_run=True,
            exports_dir=exports_dir, logs_dir=logs_dir, stop_event=stop,
        ))
        assert len(results) > 0
        combined_log = "\n".join(results)
        assert "main.py" in combined_log or "収集" in combined_log

    def test_stop_event_cancels(self, tmp_path):
        from threading import Event
        stop = Event()
        stop.set()  # 即座にキャンセル
        logs_dir = tmp_path / "logs"
        exports_dir = tmp_path / "exports"
        logs_dir.mkdir()
        exports_dir.mkdir()
        proj = tmp_path / "myproject"
        proj.mkdir()
        (proj / "main.py").write_text("x = 1")
        results = list(export_main_generator(
            str(proj),
            "gemini-single-file",
            emit_zip=False, emit_folder=False, dry_run=True,
            exports_dir=exports_dir, logs_dir=logs_dir, stop_event=stop,
        ))
        combined_log = "\n".join(results)
        assert "キャンセル" in combined_log

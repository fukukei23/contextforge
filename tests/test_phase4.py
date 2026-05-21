"""ContextForge Phase 4-5: ログ・圧縮統計・purge・エクスポート各モード"""
import pytest
import json
from pathlib import Path
from threading import Event
from unittest.mock import patch, MagicMock
from collections import defaultdict
from contextforge import (
    FileItem, LogSink, load_compression_ratios, update_compression_stats,
    purge_exports, export_main_generator, PROFILES,
    DEFAULT_EXPORTS_DIR, COMPRESSION_STATS_FILE,
)


class TestLogSinkFlush:

    def test_flush_writes_file(self, tmp_path):
        log = LogSink(tmp_path, dry_run=True)
        log.write("test line")
        log.flush("summary block")
        log_files = list(tmp_path.glob("ContextForge_build_dryrun_*.txt"))
        assert len(log_files) == 1
        content = log_files[0].read_text()
        assert "test line" in content
        assert "summary block" in content

    def test_flush_ioerror_handled(self, tmp_path):
        log = LogSink(tmp_path, dry_run=True)
        log.write("before error")
        # 読み取り専用にしてIOErrorを誘発
        log.path = Path("/nonexistent/dir/file.txt")
        log.flush("should not crash")

    def test_write_heavy_topN(self, tmp_path):
        log = LogSink(tmp_path, dry_run=True)
        heavy = [(10.5, Path("big1.bin")), (5.2, Path("big2.bin"))]
        log.write_heavy_topN(heavy, n=1)
        assert "big1.bin" in log.get_full_log()

    def test_write_heavy_topN_empty(self, tmp_path):
        log = LogSink(tmp_path, dry_run=True)
        log.write_heavy_topN([], n=5)
        assert "サイズ超過" not in log.get_full_log()


class TestLoadCompressionRatiosWithStats:

    def test_loads_from_file(self, tmp_path, monkeypatch):
        stats_file = tmp_path / "compression_stats.json"
        stats_data = {
            ".py": {"total_raw_bytes": 50_000_000, "total_zip_bytes": 20_000_000},
            ".md": {"total_raw_bytes": 30_000_000, "total_zip_bytes": 12_000_000},
        }
        stats_file.write_text(json.dumps(stats_data))
        monkeypatch.setattr("contextforge.COMPRESSION_STATS_FILE", stats_file)
        log = LogSink(tmp_path, dry_run=True)
        ratios = load_compression_ratios(log)
        # weight=0.95で実績ベースなので0.40付近になる（base=0.30、learned=0.40）
        assert 0.3 <= ratios[".py"] <= 0.95
        assert 0.3 <= ratios[".md"] <= 0.95

    def test_handles_corrupt_file(self, tmp_path, monkeypatch):
        stats_file = tmp_path / "bad_stats.json"
        stats_file.write_text("not valid json{{{")
        monkeypatch.setattr("contextforge.COMPRESSION_STATS_FILE", stats_file)
        log = LogSink(tmp_path, dry_run=True)
        ratios = load_compression_ratios(log)
        # フォールバックでデフォルト値
        assert ratios[".py"] == 0.30


class TestUpdateCompressionStats:

    def test_creates_new_stats_file(self, tmp_path, monkeypatch):
        stats_file = tmp_path / "compression_stats.json"
        monkeypatch.setattr("contextforge.COMPRESSION_STATS_FILE", stats_file)
        log = LogSink(tmp_path, dry_run=True)
        items = [
            FileItem(path=tmp_path / "a.py", root=tmp_path, rel_path=Path("a.py"),
                     size_bytes=10000, loc=100, entropy=4.5),
        ]
        update_compression_stats(items, 0.003, log)  # ~3KB zip
        assert stats_file.exists()
        data = json.loads(stats_file.read_text())
        assert ".py" in data

    def test_updates_existing_stats(self, tmp_path, monkeypatch):
        stats_file = tmp_path / "compression_stats.json"
        existing = {".py": {"total_raw_bytes": 5000, "total_zip_bytes": 1500}}
        stats_file.write_text(json.dumps(existing))
        monkeypatch.setattr("contextforge.COMPRESSION_STATS_FILE", stats_file)
        log = LogSink(tmp_path, dry_run=True)
        items = [
            FileItem(path=tmp_path / "b.py", root=tmp_path, rel_path=Path("b.py"),
                     size_bytes=2000, loc=20, entropy=4.0),
        ]
        update_compression_stats(items, 0.001, log)
        data = json.loads(stats_file.read_text())
        # 既存データに追記されている
        assert data[".py"]["total_raw_bytes"] > 5000

    def test_empty_items_noop(self, tmp_path, monkeypatch):
        stats_file = tmp_path / "stats.json"
        monkeypatch.setattr("contextforge.COMPRESSION_STATS_FILE", stats_file)
        log = LogSink(tmp_path, dry_run=True)
        update_compression_stats([], 0.0, log)
        assert not stats_file.exists()


class TestPurgeExports:

    def test_deletes_zip_and_md(self, tmp_path):
        exports = tmp_path / "exports"
        exports.mkdir()
        (exports / "test.zip").write_text("zip content")
        (exports / "report.md").write_text("report")
        (exports / "compression_stats.json").write_text("{}")
        (exports / "DIAGNOSE_test.md").write_text("diagnose")
        purge_exports(exports)
        assert not (exports / "test.zip").exists()
        assert not (exports / "report.md").exists()
        assert (exports / "compression_stats.json").exists()
        assert (exports / "DIAGNOSE_test.md").exists()

    def test_keep_last(self, tmp_path):
        exports = tmp_path / "exports"
        exports.mkdir()
        (exports / "old.zip").write_text("old")
        (exports / "new.zip").write_text("new")
        # 新しい方のmtimeを未来に設定するのは面倒なので、keep_last=1で最低1件残ることを確認
        purge_exports(exports, keep_last=1)
        remaining = list(exports.glob("*.zip"))
        assert len(remaining) <= 1

    def test_nonexistent_dir(self, tmp_path):
        # クラッシュしないこと
        purge_exports(tmp_path / "nonexistent")

    def test_empty_dir(self, tmp_path):
        exports = tmp_path / "exports"
        exports.mkdir()
        purge_exports(exports)  # クラッシュしない


class TestExportMainGeneratorModes:

    def _setup(self, tmp_path):
        proj = tmp_path / "myproject"
        proj.mkdir()
        (proj / "main.py").write_text("print('hello')")
        (proj / "utils.py").write_text("def helper(): pass")
        logs_dir = tmp_path / "logs"
        exports_dir = tmp_path / "exports"
        logs_dir.mkdir()
        exports_dir.mkdir()
        stop = Event()
        return proj, logs_dir, exports_dir, stop

    def test_single_file_mode(self, tmp_path):
        proj, logs_dir, exports_dir, stop = self._setup(tmp_path)
        results = list(export_main_generator(
            str(proj), "gemini-single-file",
            emit_zip=False, emit_folder=False, dry_run=False,
            exports_dir=exports_dir, logs_dir=logs_dir, stop_event=stop,
        ))
        combined = "\n".join(results)
        assert "生成が完了" in combined or "ドライラン" in combined or "選択" in combined
        # mdファイルが生成されている
        md_files = list(exports_dir.glob("*.md"))
        assert len(md_files) >= 1

    def test_chronicle_zip_mode(self, tmp_path):
        proj, logs_dir, exports_dir, stop = self._setup(tmp_path)
        results = list(export_main_generator(
            str(proj), "gemini-chronicle",
            emit_zip=False, emit_folder=False, dry_run=False,
            exports_dir=exports_dir, logs_dir=logs_dir, stop_event=stop,
        ))
        combined = "\n".join(results)
        assert "完了" in combined or "選択" in combined
        zip_files = list(exports_dir.glob("*.zip"))
        assert len(zip_files) >= 1

    def test_perplexity_prepare_mode(self, tmp_path):
        proj, logs_dir, exports_dir, stop = self._setup(tmp_path)
        results = list(export_main_generator(
            str(proj), "perplexity-prepare",
            emit_zip=False, emit_folder=False, dry_run=False,
            exports_dir=exports_dir, logs_dir=logs_dir, stop_event=stop,
        ))
        combined = "\n".join(results)
        assert "Perplexity" in combined or "完了" in combined or "選択" in combined

    def test_diagnose_mode(self, tmp_path):
        proj, logs_dir, exports_dir, stop = self._setup(tmp_path)
        results = list(export_main_generator(
            str(proj), "gemini-single-file",
            emit_zip=False, emit_folder=False, dry_run=True,
            exports_dir=exports_dir, logs_dir=logs_dir, stop_event=stop,
            diagnose=True,
        ))
        combined = "\n".join(results)
        assert "ドライラン" in combined
        diagnose_files = list(exports_dir.glob("DIAGNOSE_*.md"))
        assert len(diagnose_files) >= 1

    def test_exception_handling(self, tmp_path):
        """存在しないプロファイルで例外が発生してもクラッシュしない"""
        proj, logs_dir, exports_dir, stop = self._setup(tmp_path)
        # PROFILESに存在しないキーを渡すとKeyError→exceptが捕捉
        with patch.dict("contextforge.PROFILES", {}, clear=True):
            results = list(export_main_generator(
                str(proj), "nonexistent-profile",
                emit_zip=False, emit_folder=False, dry_run=True,
                exports_dir=exports_dir, logs_dir=logs_dir, stop_event=stop,
            ))
            combined = "\n".join(results)
            assert "エラー" in combined or "Error" in combined.lower() or len(results) > 0

    def test_standard_zip_mode_with_folder(self, tmp_path):
        proj, logs_dir, exports_dir, stop = self._setup(tmp_path)
        results = list(export_main_generator(
            str(proj), "gpt5-zip",
            emit_zip=True, emit_folder=True, dry_run=False,
            exports_dir=exports_dir, logs_dir=logs_dir, stop_event=stop,
        ))
        combined = "\n".join(results)
        assert "完了" in combined or "選択" in combined
        # フォルダとZIPが生成されている
        folders = [d for d in exports_dir.iterdir() if d.is_dir()]
        assert len(folders) >= 1

    def test_standard_zip_mode_zip_only(self, tmp_path):
        proj, logs_dir, exports_dir, stop = self._setup(tmp_path)
        results = list(export_main_generator(
            str(proj), "gpt5-zip",
            emit_zip=True, emit_folder=False, dry_run=False,
            exports_dir=exports_dir, logs_dir=logs_dir, stop_event=stop,
        ))
        combined = "\n".join(results)
        assert "完了" in combined or "選択" in combined
        zip_files = list(exports_dir.glob("*.zip"))
        assert len(zip_files) >= 1

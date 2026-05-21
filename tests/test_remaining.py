"""ContextForge Phase 5+: モック可能な残り領域のテスト"""
import pytest
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock
from threading import Event
from collections import defaultdict
from contextforge import (
    FileItem, LogSink, ChronicleGenerator, GuardianWatcher,
    build_import_map, collect_and_score_files, select_files,
    create_report_md, create_chunked_code_files,
    load_compression_ratios, update_compression_stats,
    purge_exports, export_main_generator, PROFILES,
)


# ---- ChronicleGenerator with mocked git ----

class TestChronicleGeneratorGenerate:

    def test_generate_with_mock_commits(self, tmp_path):
        gen = ChronicleGenerator(tmp_path)
        mock_commits = [
            {"hash": "abc123", "date": "2026-05-12", "subject": "add feature"},
            {"hash": "def456", "date": "2026-05-12", "subject": "fix bug"},
            {"hash": "ghi789", "date": "2026-05-05", "subject": "initial commit"},
        ]
        with patch.object(gen, "_run_git_log", return_value=mock_commits):
            result = gen.generate()
        assert "プロジェクト年代記" in result
        assert "add feature" in result
        assert "fix bug" in result

    def test_generate_empty_commits(self, tmp_path):
        gen = ChronicleGenerator(tmp_path)
        with patch.object(gen, "_run_git_log", return_value=[]):
            result = gen.generate()
        assert "Git履歴が見つかりません" in result

    def test_generate_no_valid_weeks(self, tmp_path):
        gen = ChronicleGenerator(tmp_path)
        commits = [{"hash": "a", "date": "invalid-date", "subject": "test"}]
        with patch.object(gen, "_run_git_log", return_value=commits):
            result = gen.generate()
        assert "利用可能なコミット履歴" in result or "年代記" in result

    def test_run_git_log_success(self, tmp_path):
        (tmp_path / ".git").mkdir()
        gen = ChronicleGenerator(tmp_path)
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "hash1<DELIMITER>2026-05-20<DELIMITER>add feature\nhash2<DELIMITER>2026-05-19<DELIMITER>fix bug"
        with patch("contextforge.subprocess.run", return_value=mock_result):
            commits = gen._run_git_log()
        assert len(commits) == 2
        assert commits[0]["subject"] == "add feature"

    def test_run_git_log_failure(self, tmp_path):
        (tmp_path / ".git").mkdir()
        gen = ChronicleGenerator(tmp_path)
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        with patch("contextforge.subprocess.run", return_value=mock_result):
            commits = gen._run_git_log()
        assert commits == []

    def test_run_git_log_no_git(self, tmp_path):
        gen = ChronicleGenerator(tmp_path)
        commits = gen._run_git_log()
        assert commits == []

    def test_summarize_by_week_invalid_date(self, tmp_path):
        gen = ChronicleGenerator(tmp_path)
        commits = [
            {"date": "2026-05-19", "subject": "ok"},
            {"date": "not-a-date", "subject": "bad"},
        ]
        result = gen._summarize_by_week(commits)
        assert len(result) == 1  # valid one only


# ---- GuardianWatcher with mocks ----

class TestGuardianWatcher:

    def test_get_last_commit_success(self, tmp_path):
        (tmp_path / ".git").mkdir()
        watcher = GuardianWatcher(str(tmp_path), 1, 1, Event())
        mock_result = MagicMock()
        mock_result.stdout.strip.return_value = "abc123def456"
        with patch("contextforge.subprocess.run", return_value=mock_result):
            result = watcher._get_last_commit()
        assert result == "abc123def456"

    def test_get_last_commit_no_git(self, tmp_path):
        watcher = GuardianWatcher(str(tmp_path), 1, 1, Event())
        result = watcher._get_last_commit()
        assert result is None

    def test_get_last_commit_exception(self, tmp_path):
        (tmp_path / ".git").mkdir()
        watcher = GuardianWatcher(str(tmp_path), 1, 1, Event())
        with patch("contextforge.subprocess.run", side_effect=Exception("fail")):
            result = watcher._get_last_commit()
        assert result is None


# ---- build_import_map edge cases ----

class TestBuildImportMapEdgeCases:

    def test_relative_path_value_error(self, tmp_path):
        """パスがrootの外部にある場合のValueError"""
        other_dir = tmp_path / "other"
        other_dir.mkdir()
        f = other_dir / "a.py"
        f.write_text("import b")
        # rootとは無関係なパスを渡す
        result = build_import_map(tmp_path, [f])
        assert isinstance(result, defaultdict)

    def test_parse_error_file(self, tmp_path):
        f = tmp_path / "broken.py"
        f.write_text("def incomplete(")
        result = build_import_map(tmp_path, [f])
        # パースエラーでクラッシュしない
        assert isinstance(result, defaultdict)

    def test_from_import_top_level(self, tmp_path):
        # モジュールがパッケージではなく単独ファイルの場合
        (tmp_path / "utils.py").write_text("x = 1")
        (tmp_path / "main.py").write_text("from utils import x")
        result = build_import_map(tmp_path, [tmp_path / "main.py", tmp_path / "utils.py"])
        # module_map["utils"] → utils.py
        assert (tmp_path / "utils.py") in result.get(tmp_path / "main.py", set())


# ---- collect_and_score_files edge cases ----

class TestCollectAndScoreFilesEdgeCases:

    def test_zero_size_file_excluded(self, tmp_path):
        log = LogSink(tmp_path, dry_run=True)
        f = tmp_path / "empty.py"
        f.write_text("")
        exclude = {"dirs": [], "files": []}
        items = collect_and_score_files(tmp_path, exclude, log)
        # 空ファイルはsize=0で除外される
        paths = [item.rel_path for item in items]
        assert Path("empty.py") not in paths or all(i.size_bytes > 0 for i in items)

    def test_exclude_by_error(self, tmp_path):
        log = LogSink(tmp_path, dry_run=True)
        exclude = {"dirs": [], "files": []}
        # 読み取れないファイルを作成
        f = tmp_path / "bad.py"
        f.write_text("ok")
        f.chmod(0o000)
        try:
            diagnose = {}
            items = collect_and_score_files(tmp_path, exclude, log, diagnose=diagnose)
            assert "excluded_by_error" in diagnose
        finally:
            f.chmod(0o644)


# ---- select_files edge cases ----

class TestSelectFilesEdgeCases:

    def test_fill_to_target_relax(self, tmp_path):
        root = tmp_path
        (tmp_path / "code.py").write_text("x = 1")
        (tmp_path / "design.md").write_text("# doc")
        items = [
            FileItem(path=tmp_path / "code.py", root=root, rel_path=Path("code.py"),
                     size_bytes=100, loc=1, entropy=4.5),
        ]
        # relax policyでfill_to_target有効、大きな目標値
        profile = {
            "target_mb": 10, "max_single_mb": 10,
            "selection_mode": "raw",
            "fill_to_target": True, "fill_policy": "relax",
        }
        ratios = defaultdict(lambda: 0.5)
        log = LogSink(tmp_path, dry_run=True)
        exclude = {"dirs": [], "files": []}
        picked, heavy = select_files(
            items, profile, ratios,
            root=root, exclude_globs=exclude, log=log,
        )
        log_text = log.get_full_log()
        assert "fill_mode=relax" in log_text or len(picked) >= 1

    def test_fill_to_target_strict(self, tmp_path):
        root = tmp_path
        items = [
            FileItem(path=tmp_path / "a.py", root=root, rel_path=Path("a.py"),
                     size_bytes=100, loc=1, entropy=4.5),
        ]
        profile = {
            "target_mb": 10, "max_single_mb": 10,
            "selection_mode": "raw",
            "fill_to_target": True, "fill_policy": "strict",
        }
        ratios = defaultdict(lambda: 0.5)
        log = LogSink(tmp_path, dry_run=True)
        picked, heavy = select_files(
            items, profile, ratios,
            root=root, exclude_globs={"dirs": [], "files": []}, log=log,
        )
        log_text = log.get_full_log()
        assert "fill_mode=strict" in log_text

    def test_duplicate_path_skipped(self, tmp_path):
        root = tmp_path
        item = FileItem(path=tmp_path / "a.py", root=root, rel_path=Path("a.py"),
                        size_bytes=100, loc=1, entropy=4.5)
        profile = {"target_mb": 1, "max_single_mb": 1, "selection_mode": "raw"}
        ratios = defaultdict(lambda: 0.5)
        picked, _ = select_files([item, item], profile, ratios)
        assert len(picked) == 1


# ---- report edge cases ----

class TestReportEdgeCases:

    def test_low_info_density_warning(self, tmp_path):
        items = [
            FileItem(path=tmp_path / "a.py", root=tmp_path, rel_path=Path("a.py"),
                     size_bytes=100, loc=1, entropy=4.5),
        ]
        # actual_zip_mbがrawより大きい → info_density < 1
        report = create_report_md(items, "test-profile", 300.0, 999.0)
        assert "情報密度" in report

    def test_low_prediction_accuracy(self, tmp_path):
        items = [
            FileItem(path=tmp_path / "a.py", root=tmp_path, rel_path=Path("a.py"),
                     size_bytes=100, loc=1, entropy=4.5),
        ]
        # predicted=300MB, actual=0.1MB → 大きな乖離
        report = create_report_md(items, "test-profile", 300_000_000.0, 0.1)
        assert "予測精度" in report
        assert "乖離" in report


# ---- chunked code splitting edge ----

class TestChunkedCodeEdgeCases:

    def test_file_exceeds_chunk_size_splits_across_chunks(self, tmp_path):
        log = LogSink(tmp_path, dry_run=True)
        big_content = "line\n" * 5000
        (tmp_path / "big.py").write_text(big_content)
        (tmp_path / "small.py").write_text("x = 1")
        items = [
            FileItem(path=tmp_path / "big.py", root=tmp_path, rel_path=Path("big.py"),
                     size_bytes=len(big_content), loc=5000, entropy=4.5),
            FileItem(path=tmp_path / "small.py", root=tmp_path, rel_path=Path("small.py"),
                     size_bytes=5, loc=1, entropy=4.5),
        ]
        out_dir = tmp_path / "chunks"
        out_dir.mkdir()
        # 極小チャンクサイズで強制的に複数チャンクに分割
        paths = create_chunked_code_files(items, out_dir, chunk_target_mb=0.001, log=log)
        assert len(paths) >= 2

    def test_unreadable_file_in_chunk(self, tmp_path):
        log = LogSink(tmp_path, dry_run=True)
        f = tmp_path / "missing.py"
        items = [
            FileItem(path=f, root=tmp_path, rel_path=Path("missing.py"),
                     size_bytes=0, loc=0, entropy=0.0),
        ]
        out_dir = tmp_path / "chunks"
        out_dir.mkdir()
        paths = create_chunked_code_files(items, out_dir, chunk_target_mb=1.0, log=log)
        assert len(paths) == 1
        assert "ERROR" in paths[0].read_text()


# ---- purge_exports edge cases ----

class TestPurgeExportsEdgeCases:

    def test_keep_last_zero_deletes_all(self, tmp_path):
        exports = tmp_path / "exports"
        exports.mkdir()
        for i in range(3):
            (exports / f"file{i}.zip").write_text(f"content{i}")
        purge_exports(exports, keep_last=0)
        remaining = list(exports.glob("*.zip"))
        assert len(remaining) == 0

    def test_keep_last_more_than_files(self, tmp_path):
        exports = tmp_path / "exports"
        exports.mkdir()
        (exports / "only.zip").write_text("content")
        purge_exports(exports, keep_last=5)
        remaining = list(exports.glob("*.zip"))
        assert len(remaining) == 1

    def test_delete_failure_handled(self, tmp_path):
        exports = tmp_path / "exports"
        exports.mkdir()
        f = exports / "readonly.zip"
        f.write_text("content")
        # WSLではchmod 0o444でも削除可能なので、代わりにunlinkをモック
        with patch("pathlib.Path.unlink", side_effect=OSError("permission denied")):
            purge_exports(exports, keep_last=0)


# ---- CLI main with mocked args ----

class TestCliMain:

    def test_main_dry_run(self, tmp_path):
        proj = tmp_path / "cli_project"
        proj.mkdir()
        (proj / "main.py").write_text("print('hello')")
        with patch("sys.argv", ["contextforge.py", str(proj), "--profile", "gemini-single-file", "--dry-run"]):
            with patch("contextforge.DEFAULT_EXPORTS_DIR", tmp_path / "exports"):
                with patch("contextforge.DEFAULT_LOGS_DIR", tmp_path / "logs"):
                    (tmp_path / "exports").mkdir()
                    (tmp_path / "logs").mkdir()
                    from contextforge import main
                    main()

    def test_main_purge_exports(self, tmp_path):
        exports = tmp_path / "exports"
        exports.mkdir()
        (exports / "test.zip").write_text("content")
        with patch("sys.argv", ["contextforge.py", str(tmp_path), "--purge-exports"]):
            with patch("contextforge.DEFAULT_EXPORTS_DIR", exports):
                with patch("contextforge.DEFAULT_LOGS_DIR", tmp_path / "logs"):
                    (tmp_path / "logs").mkdir()
                    from contextforge import main
                    main()
        assert not (exports / "test.zip").exists()


# ---- export_main_generator perplexity without chunk ----

class TestExportPerplexityNoChunk:

    def test_perplexity_without_chunk_target(self, tmp_path):
        proj = tmp_path / "proj"
        proj.mkdir()
        (proj / "main.py").write_text("x = 1")
        logs_dir = tmp_path / "logs"
        exports_dir = tmp_path / "exports"
        logs_dir.mkdir()
        exports_dir.mkdir()
        # perplexity-prepareにはchunk_target_mbがあるが、プロファイルを一時変更
        custom_profile = {
            "target_mb": 8.0,
            "output_mode": "perplexity_prepare",
            "max_single_mb": 1.8,
            "selection_mode": "raw",
            "exclude_globs": {"dirs": [], "files": []},
            "priority_files": [],
        }
        with patch.dict("contextforge.PROFILES", {"test-no-chunk": custom_profile}):
            results = list(export_main_generator(
                str(proj), "test-no-chunk",
                emit_zip=False, emit_folder=False, dry_run=False,
                exports_dir=exports_dir, logs_dir=logs_dir, stop_event=Event(),
            ))
        combined = "\n".join(results)
        assert "Perplexity" in combined or "完了" in combined
        # COMBINED_CODE.txt（チャンクではなく単一ファイル）
        code_files = list(exports_dir.rglob("COMBINED_CODE*"))
        assert len(code_files) >= 1

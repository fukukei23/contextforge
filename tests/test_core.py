"""ContextForge コア機能テスト"""
import pytest
import hashlib
import tempfile
from pathlib import Path
from contextforge import (
    to_win_long, shorten_path, glob_match, which_glob_match,
    get_file_stats, get_file_hash, FileItem,
    build_import_map, load_compression_ratios,
    ChronicleGenerator,
)


class TestToWinLong:

    def test_linux_path_unchanged(self):
        result = to_win_long(Path("/tmp/test.txt"))
        assert isinstance(result, str)


class TestShortenPath:

    def test_short_path_unchanged(self):
        p = Path("src/main.py")
        assert shorten_path(p) == p

    def test_long_path_shortened(self):
        long_path = Path("/".join(["very_long_dir_name"] * 30) + "/file.py")
        result = shorten_path(long_path)
        assert str(result) != str(long_path)
        assert len(str(result)) < len(str(long_path))


class TestGlobMatch:

    def test_match_extension(self):
        assert glob_match(Path("test.pyc"), ["*.pyc"]) is True

    def test_no_match(self):
        assert glob_match(Path("test.py"), ["*.pyc"]) is False

    def test_match_directory_pattern(self):
        assert glob_match(Path("src/__pycache__/cache.pyc"), ["**/__pycache__"]) is True


class TestWhichGlobMatch:

    def test_returns_matching_pattern(self):
        result = which_glob_match(Path("test.exe"), ["*.dll", "*.exe"])
        assert result == "*.exe"

    def test_no_match_returns_none(self):
        assert which_glob_match(Path("test.py"), ["*.exe", "*.dll"]) is None


class TestGetFileStats:

    def test_text_file(self, tmp_path):
        f = tmp_path / "test.py"
        f.write_text("line1\nline2\nline3\n")
        loc, entropy = get_file_stats(f)
        assert loc == 3
        assert entropy > 0

    def test_empty_file(self, tmp_path):
        f = tmp_path / "empty.txt"
        f.write_text("")
        loc, entropy = get_file_stats(f)
        assert loc == 0
        assert entropy == 0.0

    def test_nonexistent_file(self):
        loc, entropy = get_file_stats(Path("/nonexistent/file.txt"))
        assert loc == 0
        assert entropy == 0.0


class TestGetFileHash:

    def test_consistent_hash(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello world")
        h1 = get_file_hash(f)
        h2 = get_file_hash(f)
        assert h1 == h2
        assert len(h1) == 64  # SHA-256 hex length

    def test_different_content_different_hash(self, tmp_path):
        f1 = tmp_path / "a.txt"
        f2 = tmp_path / "b.txt"
        f1.write_text("content A")
        f2.write_text("content B")
        assert get_file_hash(f1) != get_file_hash(f2)


class TestFileItem:

    def test_creation(self):
        item = FileItem(
            path=Path("/project/src/main.py"),
            root=Path("/project"),
            rel_path=Path("src/main.py"),
            size_bytes=100,
            loc=10,
            entropy=4.5,
        )
        assert item.score == 0.0
        assert item.loc == 10


class TestBuildImportMap:

    def test_basic_imports(self, tmp_path):
        (tmp_path / "a.py").write_text("import b")
        (tmp_path / "b.py").write_text("")
        result = build_import_map(tmp_path, [tmp_path / "a.py", tmp_path / "b.py"])
        assert (tmp_path / "a.py") in result
        assert (tmp_path / "b.py") in result[(tmp_path / "a.py")]

    def test_no_imports(self, tmp_path):
        (tmp_path / "standalone.py").write_text("x = 1")
        result = build_import_map(tmp_path, [tmp_path / "standalone.py"])
        # ファイルがimportを持たない場合、マップに含まれない
        assert len(result) == 0


class TestLoadCompressionRatios:

    def test_default_ratios(self, tmp_path, monkeypatch):
        monkeypatch.setattr("contextforge.COMPRESSION_STATS_FILE", tmp_path / "nonexistent.json")
        from contextforge import LogSink
        log = LogSink(tmp_path, dry_run=True)
        ratios = load_compression_ratios(log)
        assert ratios[".py"] == 0.30
        assert ratios[".md"] == 0.35


class TestChronicleGenerator:

    def test_no_git_repo(self, tmp_path):
        gen = ChronicleGenerator(tmp_path)
        result = gen.generate()
        assert "Git" in result or "年代記" in result

    def test_analyze_theme_ai(self):
        gen = ChronicleGenerator(Path("/tmp"))
        result = gen._analyze_theme(["add agent feature", "fix LLM prompt"])
        assert result == "AI & Agents"

    def test_analyze_theme_general(self):
        gen = ChronicleGenerator(Path("/tmp"))
        result = gen._analyze_theme(["update readme", "misc changes"])
        assert result == "General Updates"

    def test_analyze_theme_empty(self):
        gen = ChronicleGenerator(Path("/tmp"))
        result = gen._analyze_theme([])
        assert result == "General Updates"

    def test_summarize_by_week(self):
        gen = ChronicleGenerator(Path("/tmp"))
        commits = [
            {"date": "2026-05-19", "subject": "fix bug"},
            {"date": "2026-05-19", "subject": "add feature"},
        ]
        result = gen._summarize_by_week(commits)
        assert len(result) == 1
        week_key = list(result.keys())[0]
        assert len(result[week_key]) == 2

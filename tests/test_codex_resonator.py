"""Tests for the Codex Resonator plugin."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from plugins.codex_resonator import generate_codex_scroll


@pytest.fixture()
def temp_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("# Sample Repo\nThis is a test.")
    return repo


def test_generate_codex_scroll_basic(
    temp_repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    mock_openai = SimpleNamespace(ChatCompletion=MagicMock())
    mock_openai.ChatCompletion.create.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="AI summary"))]
    )
    monkeypatch.setattr("plugins.codex_resonator.openai", mock_openai)

    output_file = generate_codex_scroll(str(temp_repo), tmp_path, use_openai=True)

    assert output_file.exists()
    content = output_file.read_text()
    assert "Sample Repo" in content
    assert "AI Analysis" in content


def test_generate_codex_scroll_no_readme(tmp_path: Path) -> None:
    repo = tmp_path / "repo2"
    repo.mkdir()
    output_file = generate_codex_scroll(str(repo), tmp_path)
    assert output_file.exists()
    assert "No README found" in output_file.read_text()

import json
import subprocess
import sys
from pathlib import Path

from fusion_meshmaster import fuse_repos


def test_fuse_repos(tmp_path: Path) -> None:
    repo1 = tmp_path / "repo1"
    repo1.mkdir()
    (repo1 / "file1.py").write_text("""\nclass Foo:\n    pass\n""")

    repo2 = tmp_path / "repo2"
    repo2.mkdir()
    (repo2 / "file2.py").write_text("""\ndef bar():\n    return 42\n""")

    manifest = fuse_repos(str(tmp_path))
    paths = {entry["path"] for entry in manifest}
    assert repo1.as_posix() in paths
    assert repo2.as_posix() in paths
    all_funcs = sum((entry["functions"] for entry in manifest), [])
    assert "bar" in all_funcs
    all_classes = sum((entry["classes"] for entry in manifest), [])
    assert "Foo" in all_classes


def test_cli_creates_output(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "x.py").write_text("def x():\n    pass\n")

    output_path = tmp_path / "out.json"
    subprocess.run(
        [
            sys.executable,
            "fusion_meshmaster.py",
            str(tmp_path),
            "--output",
            str(output_path),
        ],
        check=True,
    )
    assert output_path.exists()
    data = json.loads(output_path.read_text())
    assert data

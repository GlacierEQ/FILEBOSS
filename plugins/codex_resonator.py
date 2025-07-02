"""Codex Resonator plugin for project introspection."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Optional

try:
    import openai
except ImportError:  # pragma: no cover - openai is optional
    openai = None

DEFAULT_OUTPUT_DIR = "codex_scrolls"


def summarize_readme(readme_path: Path) -> str:
    """Return a short summary from the README file."""
    text = readme_path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    return "\n".join(lines[:20])


def generate_codex_scroll(
    repo_path: str,
    output_dir: str = DEFAULT_OUTPUT_DIR,
    use_openai: bool = False,
    model: str = "gpt-4",
) -> Path:
    """Generate a resonator scroll for the provided repository."""
    repo = Path(repo_path)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    readme = next(repo.glob("README*"), None)
    summary = summarize_readme(readme) if readme else "No README found."

    content = f"Codex Resonator Report for {repo.name}\n\n{summary}\n"

    if use_openai:
        if openai is None:  # pragma: no cover - optional dependency
            raise RuntimeError("openai package is required for --openai mode")

        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            openai.api_key = api_key

        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "Summarize repository"},
                {"role": "user", "content": summary},
            ],
        )
        ai_text = response.choices[0].message.content
        content += f"\nAI Analysis:\n{ai_text}\n"

    result_file = output / f"{repo.name}_scroll.md"
    result_file.write_text(content, encoding="utf-8")
    return result_file


def main(argv: Optional[list[str]] = None) -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Generate Codex Resonator scroll")
    parser.add_argument("repo_path", help="Path to repository")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--openai", action="store_true", help="Use OpenAI for analysis")
    args = parser.parse_args(argv)

    path = generate_codex_scroll(args.repo_path, args.output_dir, args.openai)
    print(f"Scroll generated at {path}")


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()

from __future__ import annotations

import re
import unittest
from pathlib import Path
from urllib.parse import unquote, urlsplit


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
ROOT_DOCUMENTS = (
    "README.md",
    "ROADMAP.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
)
DOCUMENTATION_DIRECTORIES = ("docs", "examples")
MARKDOWN_LINK = re.compile(r"!?\[[^]]*\]\(([^)]+)\)")
FENCED_CODE_BLOCK = re.compile(r"^(```|~~~).*?^\1\s*$", re.MULTILINE | re.DOTALL)


def documentation_files() -> list[Path]:
    files = [REPOSITORY_ROOT / name for name in ROOT_DOCUMENTS]
    for directory in DOCUMENTATION_DIRECTORIES:
        files.extend((REPOSITORY_ROOT / directory).rglob("*.md"))
    return sorted(files)


def link_target(raw_target: str) -> str:
    target = raw_target.strip()
    if target.startswith("<") and ">" in target:
        return target[1 : target.index(">")]
    return target.split(maxsplit=1)[0]


class DocumentationLinkTests(unittest.TestCase):
    def test_local_markdown_links_resolve_inside_repository(self) -> None:
        failures: list[str] = []

        for document in documentation_files():
            content = document.read_text(encoding="utf-8")
            content = FENCED_CODE_BLOCK.sub("", content)

            for match in MARKDOWN_LINK.finditer(content):
                target = link_target(match.group(1))
                parsed = urlsplit(target)
                if parsed.scheme or parsed.netloc or not parsed.path:
                    continue

                resolved = (document.parent / unquote(parsed.path)).resolve()
                source = document.relative_to(REPOSITORY_ROOT).as_posix()
                if not resolved.is_relative_to(REPOSITORY_ROOT):
                    failures.append(f"{source}: {target!r} resolves outside the repository")
                elif not resolved.exists():
                    failures.append(f"{source}: {target!r} does not exist")

        self.assertEqual(failures, [], "\n" + "\n".join(failures))


if __name__ == "__main__":
    unittest.main()

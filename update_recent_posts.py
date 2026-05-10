#!/usr/bin/env python3
"""Refresh the Recent posts block in the GitHub profile README.

Reads Hugo posts from ~/blog/content/posts, selects the newest published posts,
and replaces the bullet list between the Reports from the Frontline intro and the
next README section. No external dependencies.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable

PROFILE_DIR = Path(__file__).resolve().parent
README = PROFILE_DIR / "README.md"
POSTS_DIR = Path.home() / "blog" / "content" / "posts"
BASE_URL = "https://wesley.thesisko.com/posts"
POST_COUNT = 4


@dataclass(frozen=True)
class Post:
    title: str
    slug: str
    date: str
    summary: str


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    try:
        raw = text.split("---\n", 2)[1]
    except IndexError:
        return {}

    data: dict[str, str] = {}
    for line in raw.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] == '"':
            value = value[1:-1]
        data[key.strip()] = value
    return data


def published_posts(paths: Iterable[Path]) -> list[Post]:
    posts: list[Post] = []
    for path in paths:
        meta = parse_frontmatter(path)
        if not meta or meta.get("draft", "false").lower() == "true":
            continue
        title = meta.get("title")
        date = meta.get("date")
        if not title or not date:
            continue
        posts.append(
            Post(
                title=title,
                slug=path.stem,
                date=date,
                summary=meta.get("summary", "").rstrip("."),
            )
        )
    return sorted(posts, key=lambda post: post.date, reverse=True)


def render_post_list(posts: list[Post]) -> str:
    lines = []
    for post in posts[:POST_COUNT]:
        line = f"- [{post.title}]({BASE_URL}/{post.slug}/)"
        if post.summary:
            line += f" — {post.summary}."
        lines.append(line)
    return "\n".join(lines)


def main() -> None:
    posts = published_posts(POSTS_DIR.glob("*.md"))
    if not posts:
        raise SystemExit("No published posts found")

    readme = README.read_text(encoding="utf-8")
    new_block = render_post_list(posts)
    pattern = re.compile(
        r"(I write at \*\*\[wesley\.thesisko\.com\]\(https://wesley\.thesisko\.com\)\*\*\. Recent posts:\n\n)"
        r"(?:- \[[^\n]+\n)+"
        r"(\n## Operating Spec)",
        re.MULTILINE,
    )
    updated, count = pattern.subn(rf"\1{new_block}\n\2", readme)
    if count != 1:
        raise SystemExit("Could not locate Recent posts block in README.md")
    README.write_text(updated, encoding="utf-8")


if __name__ == "__main__":
    main()

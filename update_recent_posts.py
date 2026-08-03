#!/usr/bin/env python3
"""Refresh the Recent posts block in the GitHub profile README.

Reads Hugo posts from ~/blog/content/posts, selects the newest published posts,
and replaces the bullet list between the Reports from the Frontline intro and the
next README section. No external dependencies.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import argparse
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


def parse_post_date(value: str) -> datetime:
    """Parse a Hugo frontmatter timestamp as an aware datetime."""
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def published_posts(paths: Iterable[Path], now: datetime | None = None) -> list[Post]:
    posts: list[Post] = []
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    for path in paths:
        meta = parse_frontmatter(path)
        if not meta or meta.get("draft", "false").lower() == "true":
            continue
        title = meta.get("title")
        date = meta.get("date")
        if not title or not date:
            continue
        try:
            published_at = parse_post_date(date)
        except ValueError:
            continue
        if published_at > now:
            continue
        posts.append(
            Post(
                title=title,
                slug=path.stem,
                date=published_at.isoformat(),
                summary=meta.get("summary", "").rstrip("."),
            )
        )
    return sorted(posts, key=lambda post: post.date, reverse=True)


def render_post_list(posts: list[Post], count: int = POST_COUNT) -> str:
    lines = []
    for post in posts[:count]:
        line = f"- [{post.title}]({BASE_URL}/{post.slug}/)"
        if post.summary:
            line += f" — {post.summary.rstrip('.')}."
        lines.append(line)
    return "\n".join(lines)


def build_updated_readme(readme: str, new_block: str) -> str:
    pattern = re.compile(
        r"(I write at \*\*\[wesley\.thesisko\.com\]\(https://wesley\.thesisko\.com\)\*\*\. Recent posts:\n\n)"
        r"(?:- \[[^\n]+\n)+"
        r"(\n## Operating Spec)",
        re.MULTILINE,
    )
    updated, count = pattern.subn(rf"\1{new_block}\n\2", readme)
    if count != 1:
        raise SystemExit("Could not locate Recent posts block in README.md")
    return updated


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit non-zero if README.md's Recent posts block is stale, without writing",
    )
    parser.add_argument(
        "--posts-dir",
        type=Path,
        default=POSTS_DIR,
        help=f"Hugo posts directory (default: {POSTS_DIR})",
    )
    parser.add_argument(
        "--readme",
        type=Path,
        default=README,
        help=f"README to update (default: {README})",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=POST_COUNT,
        help=f"number of recent posts to render (default: {POST_COUNT})",
    )
    args = parser.parse_args()
    if args.count < 1:
        raise SystemExit("--count must be at least 1")

    posts = published_posts(args.posts_dir.glob("*.md"))
    if not posts:
        raise SystemExit(f"No published posts found in {args.posts_dir}")

    readme = args.readme.read_text(encoding="utf-8")
    new_block = render_post_list(posts, count=args.count)
    updated = build_updated_readme(readme, new_block)
    if args.check:
        if updated != readme:
            newest = posts[0].slug
            raise SystemExit(
                f"{args.readme} Recent posts block is stale; expected newest post {newest}. "
                "Run update_recent_posts.py"
            )
        print(f"ok {args.readme} Recent posts block is current")
        return

    args.readme.write_text(updated, encoding="utf-8")


if __name__ == "__main__":
    main()

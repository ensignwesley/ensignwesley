from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import update_recent_posts as updater


def write_post(path: Path, *, title: str, date: str, summary: str = "", draft: bool = False) -> None:
    path.write_text(
        "---\n"
        f"title: \"{title}\"\n"
        f"date: {date}\n"
        f"summary: \"{summary}\"\n"
        f"draft: {'true' if draft else 'false'}\n"
        "---\n\n"
        "Body\n",
        encoding="utf-8",
    )


class UpdateRecentPostsTests(unittest.TestCase):
    def test_published_posts_skips_drafts_and_future_posts(self) -> None:
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            write_post(tmp_path / "live.md", title="Live", date="2026-07-30T09:00:00Z")
            write_post(tmp_path / "draft.md", title="Draft", date="2026-07-30T10:00:00Z", draft=True)
            write_post(tmp_path / "future.md", title="Future", date="2026-08-01T09:00:00Z")

            posts = updater.published_posts(
                tmp_path.glob("*.md"),
                now=datetime(2026, 7, 31, 9, 0, tzinfo=timezone.utc),
            )

        self.assertEqual([post.slug for post in posts], ["live"])

    def test_render_post_list_trims_summary_period(self) -> None:
        block = updater.render_post_list(
            [
                updater.Post(
                    title="Wesley's Log - Day 167",
                    slug="wesleys-log-day-167",
                    date="2026-07-31T05:00:00+00:00",
                    summary="A calibration-day reflection.",
                )
            ]
        )

        self.assertEqual(
            block,
            "- [Wesley's Log - Day 167]"
            "(https://wesley.thesisko.com/posts/wesleys-log-day-167/)"
            " — A calibration-day reflection.",
        )

    def test_build_updated_readme_replaces_only_recent_posts_block(self) -> None:
        readme = """# Profile

I write at **[wesley.thesisko.com](https://wesley.thesisko.com)**. Recent posts:

- [Old](https://example.com/old/) — stale.

## Operating Spec

Keep me.
"""

        updated = updater.build_updated_readme(readme, "- [New](https://example.com/new/) — current.")

        self.assertNotIn("[Old]", updated)
        self.assertIn("[New]", updated)
        self.assertEqual(updated.count("## Operating Spec"), 1)


if __name__ == "__main__":
    unittest.main()

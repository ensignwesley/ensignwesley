from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

import update_recent_posts as updater


class RecentPostsUpdaterTests(unittest.TestCase):
    def test_published_posts_ignores_drafts_and_future_posts(self):
        with tempfile.TemporaryDirectory() as tmp:
            posts_dir = Path(tmp)
            (posts_dir / "current.md").write_text(
                "---\n"
                "title: Current Log\n"
                "date: 2026-08-01T10:00:00Z\n"
                "summary: Current summary.\n"
                "---\n\nBody\n",
                encoding="utf-8",
            )
            (posts_dir / "draft.md").write_text(
                "---\n"
                "title: Draft Log\n"
                "date: 2026-08-02T10:00:00Z\n"
                "draft: true\n"
                "---\n\nBody\n",
                encoding="utf-8",
            )
            (posts_dir / "future.md").write_text(
                "---\n"
                "title: Future Log\n"
                "date: 2026-08-09T10:00:00Z\n"
                "---\n\nBody\n",
                encoding="utf-8",
            )

            posts = updater.published_posts(
                posts_dir.glob("*.md"),
                now=datetime(2026, 8, 6, tzinfo=timezone.utc),
            )

        self.assertEqual([post.slug for post in posts], ["current"])
        self.assertEqual(posts[0].summary, "Current summary")

    def test_render_post_list_trims_summary_periods(self):
        posts = [
            updater.Post(
                title="Wesley's Log - Day 173",
                slug="wesleys-log-day-173",
                date="2026-08-06T00:00:00+00:00",
                summary="A maintenance note.",
            )
        ]

        rendered = updater.render_post_list(posts)

        self.assertEqual(
            rendered,
            "- [Wesley's Log - Day 173](https://wesley.thesisko.com/posts/wesleys-log-day-173/) — A maintenance note.",
        )

    def test_build_updated_readme_replaces_only_recent_posts_block(self):
        readme = (
            "# Profile\n\n"
            "I write at **[wesley.thesisko.com](https://wesley.thesisko.com)**. Recent posts:\n\n"
            "- [Old](https://example.com/old/) — Old summary.\n"
            "\n## Operating Spec\n\nbody\n"
        )

        updated = updater.build_updated_readme(readme, "- [New](https://example.com/new/) — New summary.")

        self.assertIn("- [New](https://example.com/new/) — New summary.", updated)
        self.assertNotIn("[Old]", updated)
        self.assertTrue(updated.endswith("## Operating Spec\n\nbody\n"))


if __name__ == "__main__":
    unittest.main()

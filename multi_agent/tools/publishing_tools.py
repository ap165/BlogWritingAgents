from pathlib import Path
import re
import json


# Output directory:
# multi_agent/output/
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "output"


def _make_slug(title: str) -> str:
    """Convert a title into a safe filename."""
    slug = title.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")

    return slug or "untitled-post"


def save_draft(
    title: str,
    body: str,
    meta_description: str = "",
) -> dict:
    """
    Save a generated blog article as a Markdown draft.

    Args:
        title: The blog article title.
        body: The complete article content in Markdown.
        meta_description: Optional SEO meta description.

    Returns:
        A dictionary containing the save status and file path.
    """
    if not title or not title.strip():
        return {
            "success": False,
            "error": "The article title cannot be empty.",
        }

    if not body or not body.strip():
        return {
            "success": False,
            "error": "The article body cannot be empty.",
        }

    try:
        # Create the output directory if necessary.
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        # Generate a safe filename from the title.
        slug = _make_slug(title)
        file_path = OUTPUT_DIR / f"{slug}.md"

        # Avoid overwriting an existing article.
        counter = 2
        while file_path.exists():
            file_path = OUTPUT_DIR / f"{slug}-{counter}.md"
            counter += 1

        # Build the Markdown document with metadata.
        content = (
            "---\n"
            f"title: {json.dumps(title.strip(), ensure_ascii=False)}\n"
            f"slug: {json.dumps(file_path.stem)}\n"
            f"meta_description: "
            f"{json.dumps(meta_description.strip(), ensure_ascii=False)}\n"
            "status: draft\n"
            "---\n\n"
            f"# {title.strip()}\n\n"
            f"{body.strip()}\n"
        )

        # Save the article as UTF-8 Markdown.
        file_path.write_text(content, encoding="utf-8")

        return {
            "success": True,
            "message": "Blog draft saved successfully.",
            "title": title.strip(),
            "file_path": str(file_path),
            "status": "draft",
        }

    except OSError as exc:
        return {
            "success": False,
            "error": f"Could not save the blog draft: {exc}",
        }
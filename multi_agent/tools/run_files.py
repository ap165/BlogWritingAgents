"""File-based handoff between the blog agents.

Each run gets its own folder. Agents write and read named JSON files there,
so the coordinator never has to copy packages or drafts through its own context.

Put this file in your tools/ folder and give each agent only the tools it needs
(see the table in the instructions).
"""

import json
import os
import re
import shutil
import time
import uuid
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
RUNS_DIR = Path(os.environ.get("BLOG_RUNS_DIR", BASE_DIR / "runs"))
DRAFTS_DIR = Path(os.environ.get("BLOG_DRAFTS_DIR", BASE_DIR / "drafts"))

MAX_BYTES = 300_000  # safety limit for one file

# Only these names are allowed. This blocks path tricks like "../../secret".
RUN_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
FILE_RE = re.compile(r"^(research_package|draft_v[1-9][0-9]?|review_v[1-9][0-9]?)\.json$")


def _error(message: str) -> dict:
    return {"status": "error", "message": message}


def _resolve(run_id: str, filename: str):
    """Return (path, None) if valid, or (None, error_dict) if not."""
    if not isinstance(run_id, str) or not RUN_ID_RE.match(run_id):
        return None, _error("Invalid run_id.")
    if not isinstance(filename, str) or not FILE_RE.match(filename):
        return None, _error(
            "Invalid filename. Allowed: research_package.json, draft_vN.json, review_vN.json."
        )
    run_dir = RUNS_DIR / run_id
    if not run_dir.is_dir():
        return None, _error("Run folder does not exist. The coordinator must call start_run first.")
    return run_dir / filename, None


def start_run() -> dict:
    """Start a new blog run and create its folder.

    Returns:
        dict with status and the new run_id. Use this run_id in every later call.
    """
    run_id = time.strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:4]
    (RUNS_DIR / run_id).mkdir(parents=True, exist_ok=True)
    return {"status": "ok", "run_id": run_id}


def write_run_file(run_id: str, filename: str, content: str) -> dict:
    """Save a JSON file for this run.

    Args:
        run_id: The run id given by the coordinator.
        filename: One of research_package.json, draft_vN.json, review_vN.json.
        content: The full file content as valid JSON text.

    Returns:
        dict with status "ok" and the byte size, or status "error" and a message.
        If you get an error, fix the problem and call again.
    """
    path, err = _resolve(run_id, filename)
    if err:
        return err
    if not isinstance(content, str):
        return _error("Content must be a JSON string.")
    data = content.encode("utf-8")
    if len(data) > MAX_BYTES:
        return _error(f"File too large ({len(data)} bytes). Limit is {MAX_BYTES}.")
    try:
        parsed = json.loads(content)
    except (json.JSONDecodeError, TypeError) as exc:
        return _error(f"Content is not valid JSON: {exc}")
    if not isinstance(parsed, dict):
        return _error("JSON root must be an object (dictionary).")

    tmp = path.with_suffix(f".{uuid.uuid4().hex[:6]}.tmp")
    try:
        tmp.write_bytes(data)
        os.replace(tmp, path)  # atomic: a reader never sees a half-written file
    finally:
        if tmp.exists():
            tmp.unlink(missing_ok=True)

    return {"status": "ok", "file": filename, "bytes": len(data)}


def read_run_file(run_id: str, filename: str) -> dict:
    """Read a JSON file saved earlier in this run.

    Args:
        run_id: The run id given by the coordinator.
        filename: One of research_package.json, draft_vN.json, review_vN.json.

    Returns:
        dict with status "ok" and the file content as text, or status "error".
    """
    path, err = _resolve(run_id, filename)
    if err:
        return err
    if not path.is_file():
        return _error(f"{filename} does not exist yet in this run.")
    return {"status": "ok", "file": filename, "content": path.read_text(encoding="utf-8")}


def save_final_draft(run_id: str, draft_version: int) -> dict:
    """Save the approved draft as the final post (dry-run output).

    Reads the draft file in code, so the coordinator never has to copy the article.

    Args:
        run_id: The run id.
        draft_version: The version number of the approved draft (for example 2).

    Returns:
        dict with status and the saved file paths, or status "error".
    """
    try:
        version_num = int(draft_version)
    except (ValueError, TypeError):
        return _error("draft_version must be an integer.")

    path, err = _resolve(run_id, f"draft_v{version_num}.json")
    if err:
        return err
    if not path.is_file():
        return _error("That draft file does not exist.")

    try:
        draft = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return _error(f"Corrupted draft JSON: {exc}")

    if not isinstance(draft, dict):
        return _error("Draft JSON content must be a JSON object.")

    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    json_path = DRAFTS_DIR / f"{run_id}.json"
    md_path = DRAFTS_DIR / f"{run_id}.md"
    json_path.write_text(json.dumps(draft, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(
        f"# {draft.get('title', '')}\n\n"
        f"<!-- slug: {draft.get('slug', '')} | meta: {draft.get('meta_description', '')} -->\n\n"
        f"{draft.get('body_markdown', '')}\n",
        encoding="utf-8",
    )
    return {"status": "ok", "json": str(json_path), "markdown": str(md_path)}


def cleanup_old_runs(max_age_days: int = 7) -> int:
    """Delete run folders older than max_age_days. Call this at startup, not as an agent tool.

    Returns the number of folders deleted.
    """
    if not RUNS_DIR.is_dir():
        return 0
    cutoff = time.time() - max_age_days * 86400
    deleted = 0
    for run_dir in RUNS_DIR.iterdir():
        if run_dir.is_dir() and run_dir.stat().st_mtime < cutoff:
            shutil.rmtree(run_dir, ignore_errors=True)
            deleted += 1
    return deleted
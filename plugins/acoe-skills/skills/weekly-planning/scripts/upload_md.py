#!/usr/bin/env python3
"""Upload a local markdown file to the user's OneDrive via Microsoft Graph.

This script is invoked by the `weekly-planning` skill via the Bash tool, BUT it
does not call Graph directly (no network creds available in the sandbox). It
instead emits a `CallGraph`-shaped instruction line that the parent agent reads
and executes via the `CallGraph` MCP tool.

Usage:
    python upload_md.py <local-path> <onedrive-path>
Example:
    python upload_md.py working/weekly-planning/tasks.md "/Documents/Cowork/WeeklyPlanning/tasks.md"

The script:
  - validates the local file exists,
  - prints a JSON envelope to stdout that the agent uses to drive CallGraph,
    e.g. {"action":"upload","path":"...","content_b64":"...","content_type":"text/markdown"}.
"""
import argparse
import base64
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("local_path")
    parser.add_argument("onedrive_path", help="Path under the user's OneDrive root, e.g. /Documents/Cowork/WeeklyPlanning/tasks.md")
    args = parser.parse_args()

    p = Path(args.local_path)
    if not p.exists():
        print(json.dumps({"error": f"local file not found: {p}"}), file=sys.stderr)
        return 1

    data = p.read_bytes()
    envelope = {
        "action": "upload",
        "graph_method": "PUT",
        "graph_path": f"/me/drive/root:{args.onedrive_path}:/content",
        "content_b64": base64.b64encode(data).decode("ascii"),
        "content_type": "text/markdown; charset=utf-8",
        "size": len(data),
    }
    print(json.dumps(envelope, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

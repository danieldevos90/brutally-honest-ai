#!/usr/bin/env python3
"""
Rebuild frontend-visible transcription history on a Jetson/NVIDIA box.

The frontend UI reads history from the JSON file defined in `frontend/server.js`:
  FRONTEND_HISTORY_FILE -> defaults to <repo_root>/data/transcription_history.json

In practice, history can appear "gone" after redeploys because the JSON state file
and/or the recordings directory weren't migrated, even if some audio files still
exist under `frontend/uploads/recordings/`.

This script scans for existing recording files and (re)creates history entries so
the UI can display them again.

Safe to run multiple times (it won't create duplicate entries for the same savedFilename).
"""

from __future__ import annotations

import json
import os
import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


AUDIO_EXTS = {".wav", ".mp3", ".m4a", ".ogg", ".flac", ".aac", ".webm"}


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _load_json_list(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _atomic_write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2))
    os.replace(tmp, path)


def _iso_from_mtime(mtime_s: float) -> str:
    return datetime.fromtimestamp(mtime_s, tz=timezone.utc).isoformat()


_PREFIX_RE = re.compile(r"^(\d{8}_\d{6}_|[\dT:\-]{19,}[_-])")


def _guess_original_filename(saved_filename: str) -> str:
    # Strip common timestamp prefixes used by backend/frontend.
    return _PREFIX_RE.sub("", saved_filename) or saved_filename


def _list_audio_files(dir_path: Path) -> List[Path]:
    if not dir_path.exists() or not dir_path.is_dir():
        return []
    out: List[Path] = []
    for p in dir_path.iterdir():
        if not p.is_file():
            continue
        if p.suffix.lower() in AUDIO_EXTS:
            out.append(p)
    out.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return out


def _index_by_saved_filename(history: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    idx: Dict[str, Dict[str, Any]] = {}
    for item in history:
        sf = item.get("savedFilename")
        if isinstance(sf, str) and sf:
            idx[sf] = item
    return idx


def _make_id(saved_filename: str, mtime_s: float) -> str:
    # Close enough to frontend's "Date.now().toString()", but stable across rebuilds.
    return f"{int(mtime_s * 1000)}_{abs(hash(saved_filename)) % 1_000_000}"


def main() -> int:
    root = _repo_root()

    history_file = root / "data" / "transcription_history.json"
    uploads_recordings_dir = root / "frontend" / "uploads" / "recordings"
    backend_recordings_dir = root / "recordings"

    # Load existing history (this is what the UI reads).
    history = _load_json_list(history_file)
    by_saved = _index_by_saved_filename(history)

    # Discover recordings from both places. The UI download endpoint expects files in uploads/recordings.
    discovered: List[Tuple[Path, str]] = []
    for p in _list_audio_files(uploads_recordings_dir):
        discovered.append((p, p.name))
    for p in _list_audio_files(backend_recordings_dir):
        # If only exists in backend dir, copy into uploads so UI can download it.
        uploads_recordings_dir.mkdir(parents=True, exist_ok=True)
        target = uploads_recordings_dir / p.name
        if not target.exists():
            shutil.copy2(p, target)
        discovered.append((target, target.name))

    # Deduplicate by filename (prefer uploads copy).
    seen: set[str] = set()
    unique: List[Path] = []
    for p, name in discovered:
        if name in seen:
            continue
        seen.add(name)
        unique.append(p)

    added = 0
    for p in unique:
        st = p.stat()
        saved_filename = p.name
        if saved_filename in by_saved:
            continue

        entry: Dict[str, Any] = {
            "id": _make_id(saved_filename, st.st_mtime),
            "timestamp": _iso_from_mtime(st.st_mtime),
            "originalFilename": _guess_original_filename(saved_filename),
            "savedFilename": saved_filename,
            "fileSize": st.st_size,
            # No results available for orphaned files. UI handles missing transcription gracefully.
            "result": {},
            "status": "pending",
        }
        history.insert(0, entry)
        by_saved[saved_filename] = entry
        added += 1

    # Keep most recent 100 like the frontend does.
    history = history[:100]

    _atomic_write_json(history_file, history)
    print(f"Wrote {history_file} (entries={len(history)}, added={added})")
    print(f"Uploads recordings dir: {uploads_recordings_dir} (files={len(_list_audio_files(uploads_recordings_dir))})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


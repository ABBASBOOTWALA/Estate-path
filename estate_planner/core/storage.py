import json
import os
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from core.models import (
    DeceasedProfile, EstateTask, GeneratedDocument,
    Deadline, ActivityEntry
)

BASE_DIR = Path.home() / ".estatepath"
DOCS_DIR = BASE_DIR / "documents"


def _ensure_dirs():
    BASE_DIR.mkdir(exist_ok=True)
    DOCS_DIR.mkdir(exist_ok=True)


def _read(filename: str) -> any:
    _ensure_dirs()
    path = BASE_DIR / filename
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write(filename: str, data: any):
    _ensure_dirs()
    path = BASE_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ── Profile ──────────────────────────────────────────────

def load_profile() -> Optional[DeceasedProfile]:
    data = _read("profile.json")
    if data is None:
        return None
    return DeceasedProfile.from_dict(data)


def save_profile(profile: DeceasedProfile):
    _write("profile.json", profile.to_dict())


def profile_exists() -> bool:
    return (BASE_DIR / "profile.json").exists()


# ── Tasks ─────────────────────────────────────────────────

def load_tasks() -> List[EstateTask]:
    data = _read("tasks.json")
    if not data:
        return []
    return [EstateTask.from_dict(t) for t in data]


def save_tasks(tasks: List[EstateTask]):
    _write("tasks.json", [t.to_dict() for t in tasks])


def update_task_status(task_id: str, status: str, notes: str = ""):
    tasks = load_tasks()
    for t in tasks:
        if t.task_id == task_id:
            t.status = status
            if notes:
                t.notes = notes
            if status == "completed":
                t.completed_date = datetime.now().date().isoformat()
            break
    save_tasks(tasks)
    log_activity(task_id, f"Status updated to '{status}'", task_id)


def get_task(task_id: str) -> Optional[EstateTask]:
    for t in load_tasks():
        if t.task_id == task_id:
            return t
    return None


# ── Documents ─────────────────────────────────────────────

def load_documents() -> List[GeneratedDocument]:
    data = _read("documents.json")
    if not data:
        return []
    return [GeneratedDocument.from_dict(d) for d in data]


def save_document(doc: GeneratedDocument):
    docs = load_documents()
    docs.append(doc)
    _write("documents.json", [d.to_dict() for d in docs])


# ── Deadlines ─────────────────────────────────────────────

def load_deadlines() -> List[Deadline]:
    data = _read("deadlines.json")
    if not data:
        return []
    return [Deadline.from_dict(d) for d in data]


def save_deadlines(deadlines: List[Deadline]):
    _write("deadlines.json", [d.to_dict() for d in deadlines])


# ── Activity Log ──────────────────────────────────────────

def load_activity_log() -> List[ActivityEntry]:
    data = _read("activity_log.json")
    if not data:
        return []
    return [ActivityEntry.from_dict(e) for e in data]


def log_activity(action: str, description: str, task_id: str = ""):
    log = load_activity_log()
    entry = ActivityEntry(
        timestamp=datetime.now().isoformat(),
        action=action,
        task_id=task_id,
        description=description,
    )
    log.insert(0, entry)
    log = log[:100]  # keep last 100 entries
    _write("activity_log.json", [e.to_dict() for e in log])


# ── Helpers ───────────────────────────────────────────────

def get_docs_dir() -> Path:
    _ensure_dirs()
    return DOCS_DIR


def reset_estate():
    """Delete all estate data (for testing or starting over)."""
    for f in ["profile.json", "tasks.json", "documents.json", "deadlines.json", "activity_log.json"]:
        p = BASE_DIR / f
        if p.exists():
            p.unlink()

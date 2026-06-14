"""
Obsidian vault writer — creates markdown notes in the user's EchoVault.
Obsidian picks up new files automatically; no plugin required.
"""

from datetime import datetime
from pathlib import Path

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def write_memory_note(title: str, content: str, memory_id: str) -> str:
    """
    Write a memory to the Obsidian vault as a markdown file.
    Returns the path of the created file.
    """
    settings = get_settings()
    vault = Path(settings.obsidian_vault_path)
    vault.mkdir(parents=True, exist_ok=True)

    memories_dir = vault / "Echo Memories"
    memories_dir.mkdir(exist_ok=True)

    safe_title = "".join(c if c.isalnum() or c in " -_" else "" for c in title).strip()
    safe_title = safe_title[:60] or "Memory"
    filename = f"{safe_title}.md"
    filepath = memories_dir / filename

    # Avoid overwriting by appending ID suffix if file exists
    if filepath.exists():
        filename = f"{safe_title} {memory_id[:8]}.md"
        filepath = memories_dir / filename

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    note = f"""---
tags: [echo, memory]
created: {now}
memory_id: {memory_id}
---

# {title}

{content}
"""
    filepath.write_text(note, encoding="utf-8")
    logger.info(f"Obsidian note written: {filepath}")
    return str(filepath)

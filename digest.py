"""
digest.py — Daily memory digest

Runs once a day (via cron at 23:59).
1. Pulls all short-term memories from Chroma for today
2. Asks Claude to write a coherent diary entry in plain prose
3. Saves/overwrites the diary in the Obsidian vault under Daily Notes
4. Deletes those entries from Chroma to clean up short-term memory
"""

import sys
import os
from datetime import datetime
from pathlib import Path

# Allow imports from the Shiba package root
sys.path.insert(0, str(Path(__file__).parent))

import chromadb
import anthropic

from config import CHROMA_PATH, VAULT_PATH, ANTHROPIC_API_KEY, MODEL
from memory.vault import ObsidianVault


# ── Helpers ──────────────────────────────────────────────────────────────────

def fetch_todays_entries(col) -> tuple[list[str], list[str]]:
    """Return (ids, documents) for all entries timestamped today."""
    today = datetime.now().strftime("%Y-%m-%d")
    total = col.count()
    if total == 0:
        return [], []

    result = col.get(include=["documents", "metadatas"])
    ids, docs = [], []
    for i, meta in enumerate(result["metadatas"]):
        ts = meta.get("timestamp", "")
        if ts.startswith(today):
            ids.append(result["ids"][i])
            role = meta.get("role", "unknown")
            docs.append(f"[{ts}] {role}: {result['documents'][i]}")

    return ids, docs


def build_diary_prompt(date_str: str, entries: list[str]) -> str:
    raw = "\n".join(entries)
    return f"""Below are all conversation turns between a user and their AI assistant (Shiba) on {date_str}.

Write a diary entry from Shiba's perspective — first person, plain prose, no bullet points, no headers, no emojis. 
Write it like a thoughtful personal diary. Capture what happened, what was built or decided, what the user seemed to care about, and any notable moments. Be concise but complete. Do not invent things not present in the transcripts.

---
{raw}
---

Write the diary entry now:"""


def write_diary(date_str: str, diary_text: str, vault: ObsidianVault) -> None:
    """Write (or overwrite) the diary note for the given date."""
    path = vault.vault_path / "Daily Notes" / f"{date_str}.md"

    import frontmatter

    if path.exists():
        post = frontmatter.load(str(path))
        # Replace or append the diary section
        existing = post.content
        marker = "<!-- digest -->"
        if marker in existing:
            # Overwrite everything after the marker
            pre = existing[:existing.index(marker)]
            post.content = pre + marker + "\n\n" + diary_text
        else:
            post.content = existing + f"\n\n{marker}\n\n" + diary_text
        post.metadata["updated"] = datetime.now().isoformat()
        post.metadata["tags"] = list(set(post.metadata.get("tags", []) + ["diary", "daily-summary", date_str]))
    else:
        post = frontmatter.Post(
            content=f"<!-- digest -->\n\n{diary_text}",
            title=f"{date_str} Diary",
            date=date_str,
            type="diary",
            tags=["diary", "daily-summary", date_str],
            updated=datetime.now().isoformat(),
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(frontmatter.dumps(post))
    print(f"Diary saved to {path}")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"[digest] Starting digest for {today}")

    # Connect to Chroma
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    col = client.get_or_create_collection(
        name="conversations",
        metadata={"hnsw:space": "cosine"},
    )

    ids, entries = fetch_todays_entries(col)

    if not entries:
        print("[digest] No entries found for today. Nothing to do.")
        return

    print(f"[digest] Found {len(entries)} entries. Asking Claude to write diary...")

    # Ask Claude to write the diary
    anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    response = anthropic_client.messages.create(
        model=MODEL,
        max_tokens=2048,
        messages=[
            {"role": "user", "content": build_diary_prompt(today, entries)}
        ],
    )
    diary_text = response.content[0].text.strip()

    # Save to vault
    vault = ObsidianVault(VAULT_PATH)
    write_diary(today, diary_text, vault)

    # Clean up Chroma
    col.delete(ids=ids)
    print(f"[digest] Deleted {len(ids)} entries from Chroma. Done.")


if __name__ == "__main__":
    main()

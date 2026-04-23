import subprocess
from datetime import datetime
from pathlib import Path

import frontmatter

from config import OBSIDIAN_CLI, VAULT_PATH


class ObsidianVault:
    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
        for folder in ("Daily Notes", "Topics", "Projects"):
            (vault_path / folder).mkdir(parents=True, exist_ok=True)
        self._ensure_cli_default()

    # ── CLI helpers ──────────────────────────────────────────────────────────

    def _cli(self, *args) -> str:
        try:
            result = subprocess.run(
                [OBSIDIAN_CLI, "--vault", str(self.vault_path), *args],
                capture_output=True, text=True, timeout=10,
            )
            return result.stdout.strip()
        except Exception:
            return ""

    def _ensure_cli_default(self) -> None:
        try:
            subprocess.run(
                [OBSIDIAN_CLI, "set-default", "Shiba-Vault", str(self.vault_path)],
                capture_output=True, text=True, timeout=10,
            )
        except Exception:
            pass

    def cli_search(self, term: str) -> str:
        return self._cli("search-content", term)

    # ── Note operations ──────────────────────────────────────────────────────

    def save_note(
        self,
        title: str,
        content: str,
        tags: list[str] | None = None,
        folder: str = "Topics",
    ) -> str:
        safe = "".join(c if c.isalnum() or c in " -_" else "_" for c in title).strip()
        note_dir = self.vault_path / folder
        note_dir.mkdir(exist_ok=True)
        path = note_dir / f"{safe}.md"

        post = frontmatter.Post(
            content=content,
            title=title,
            tags=tags or [],
            updated=datetime.now().isoformat(),
        )
        path.write_text(frontmatter.dumps(post))
        return str(path)

    def save_daily_note(self, session_id: str, content: str) -> str:
        date_str = datetime.now().strftime("%Y-%m-%d")
        path = self.vault_path / "Daily Notes" / f"{date_str}.md"

        if path.exists():
            post = frontmatter.load(str(path))
            sessions = post.metadata.get("sessions", [])
            if session_id not in sessions:
                sessions.append(session_id)
            post.metadata["sessions"] = sessions
            post.content = post.content + f"\n\n---\n\n{content}"
        else:
            post = frontmatter.Post(
                content=content,
                date=date_str,
                sessions=[session_id],
                created=datetime.now().isoformat(),
            )

        path.write_text(frontmatter.dumps(post))
        return str(path)

    def read_note(self, note_name: str) -> str | None:
        name = note_name.strip()
        for p in self.vault_path.rglob("*.md"):
            if p.stem.lower() == name.lower() or p.name.lower() == name.lower():
                return p.read_text()
        return None

    def list_notes(self) -> list[str]:
        return sorted(
            str(p.relative_to(self.vault_path))
            for p in self.vault_path.rglob("*.md")
        )

    def get_recent_daily_notes(self, n: int = 3) -> list[dict]:
        daily_dir = self.vault_path / "Daily Notes"
        notes = sorted(daily_dir.glob("*.md"), key=lambda p: p.stem, reverse=True)[:n]
        return [{"date": p.stem, "content": p.read_text()} for p in notes]

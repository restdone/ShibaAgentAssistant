from pathlib import Path
from datetime import datetime
from flask import abort

from .app import BASE_DIR

TEXT_EXTS = {
    ".txt", ".py", ".js", ".ts", ".html", ".htm", ".css", ".md",
    ".json", ".yaml", ".yml", ".toml", ".sh", ".bash", ".xml",
    ".csv", ".ini", ".cfg", ".env", ".rs", ".go", ".c", ".cpp",
    ".h", ".java", ".rb", ".php", ".sql", ".log",
}


def safe_path(rel: str) -> Path:
    target = (BASE_DIR / rel).resolve()
    if not str(target).startswith(str(BASE_DIR)):
        abort(403)
    return target


def human_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def human_mtime(ts: float) -> str:
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")


def js_bool(val: bool) -> str:
    """Convert a Python bool to a JavaScript boolean literal."""
    return "true" if val else "false"


def js_str(val: str) -> str:
    """Escape a Python string for safe use as a JS string argument."""
    return "'" + val.replace("\\", "\\\\").replace("'", "\\'") + "'"


def build_breadcrumbs(rel: str) -> str:
    parts = [p for p in rel.split("/") if p]
    html = ""
    for i, part in enumerate(parts):
        so_far = "/".join(parts[: i + 1])
        html += f' <span>/</span> <a href="/browse/{so_far}">{part}</a>'
    return html


def build_rows(rel: str, path: Path) -> tuple:
    parent_row = ""
    if rel:
        parent = "/".join(rel.rstrip("/").split("/")[:-1])
        parent_row = (
            f'<tr><td colspan="5"><a href="/browse/{parent}">&#128281; ..</a></td></tr>'
        )

    rows = []
    entries = sorted(path.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower()))
    for entry in entries:
        entry_rel = (rel.rstrip("/") + "/" + entry.name).lstrip("/")
        is_dir = entry.is_dir()
        icon = "&#128193;" if is_dir else "&#128196;"

        try:
            stat = entry.stat()
            mtime_str = human_mtime(stat.st_mtime)
            size_str = "—" if is_dir else human_size(stat.st_size)
        except Exception:
            mtime_str = "?"
            size_str = "?"

        if is_dir:
            name_html = f'<a href="/browse/{entry_rel}">{icon} {entry.name}</a>'
            type_str = "Folder"
        else:
            name_html = f"{icon} {entry.name}"
            suffix = entry.suffix.lstrip(".").upper() or "File"
            type_str = f"{suffix} File"

        can_edit = not is_dir and entry.suffix.lower() in TEXT_EXTS

        # Desktop action buttons
        actions = []
        if not is_dir:
            actions.append(
                f'<a class="btn btn-primary btn-sm" href="/download?path={entry_rel}">&#8681; Download</a>'
            )
        if can_edit:
            actions.append(
                f'<button class="btn btn-warn btn-sm" onclick="openEditor({js_str(entry_rel)}, {js_str(entry.name)})">&#9998; Edit</button>'
            )
        actions.append(
            f'<button class="btn btn-sm" style="background:#cba6f7;color:#1e1e2e" onclick="openRename({js_str(entry_rel)}, {js_str(entry.name)})">&#9998; Rename</button>'
        )
        actions.append(
            f'<button class="btn btn-danger btn-sm" onclick="deleteItem({js_str(entry_rel)}, {js_str(entry.name)})">&#128465; Delete</button>'
        )

        # Mobile "..." button — passes correct JS booleans
        mobile_btn = (
            f'<button class="btn btn-sm mobile-menu-btn" '
            f'onclick="openActionSheet({js_str(entry_rel)}, {js_str(entry.name)}, {js_bool(is_dir)}, {js_bool(can_edit)})">'
            f'&#8942;</button>'
        )

        action_html = (
            '<div class="actions desktop-actions">' + "".join(actions) + "</div>"
            + mobile_btn
        )

        rows.append(
            f"<tr>"
            f"<td>{name_html}<div class='mobile-meta'>{type_str} · {size_str}<br><span class='mtime'>{mtime_str}</span></div></td>"
            f"<td class='type-col'>{type_str}</td>"
            f"<td class='size-col'>{size_str}</td>"
            f"<td class='modified-col'>{mtime_str}</td>"
            f"<td>{action_html}</td>"
            f"</tr>"
        )

    return parent_row, "\n".join(rows)
